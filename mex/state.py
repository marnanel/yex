import datetime
import mex.value
import mex.box
import mex.parameter
import mex.control
import mex.register
import mex.mode
import mex.exception
import re
import logging

commands_logger = logging.getLogger('mex.macros')
macros_logger = logging.getLogger('mex.macros')
restores_logger = logging.getLogger('mex.restores')

ASSIGNMENT_LOG_RECORD = "%s %-8s = %s"

KEYWORD_WITH_INDEX = re.compile(r'^([^;]+?);?([0-9]+)$')

class Group:
    def __init__(self, state):
        self.state = state
        self.restores = {}

    def remember_restore(self, f, v):

        if f in self.restores:
            restores_logger.debug(
                    "Redefinition of %s; ignored for remembers", f)
            return

        try:
            v = v.value
        except AttributeError:
            pass

        restores_logger.debug(
                ASSIGNMENT_LOG_RECORD,
                '*', f, repr(v))
        self.restores[f] = v

    def run_restores(self):
        restores_logger.debug("Beginning restores: %s",
                self.restores)
        self.next_assignment_is_global = False
        for f, v in self.restores.items():
            self.state.__setitem__(
                    field = f,
                    value = v,
                    from_restore = True,
                    )

        restores_logger.debug("  -- restores done.")
        self.restores = {}

    def __repr__(self):
        return 'g%04x' % (hash(self) % 0xffff,)

class State:

    def __init__(self):

        self.created_at = datetime.datetime.now()

        self.controls = mex.control.ControlsTable()
        self.controls |= mex.control.handlers()
        self.controls |= mex.parameter.handlers(self)

        self.fonts = {}

        self.registers = {
                'count': mex.register.CountsTable(state=self),
                'dimen': mex.register.DimensTable(state=self),
                'skip': mex.register.SkipsTable(state=self),
                'muskip': mex.register.MuskipsTable(state=self),
                'toks': mex.register.ToksTable(state=self),
                'box': mex.register.BoxTable(state=self),
                'hyphenation': mex.register.HyphenationTable(state=self),
                'catcode': mex.register.CatcodesTable(state=self),
                'mathcode': mex.register.MathcodesTable(state=self),
                'uccode': mex.register.UccodesTable(state=self),
                'lccode': mex.register.LccodesTable(state=self),
                'sfcode': mex.register.SfcodesTable(state=self),
                'delcode': mex.register.DelcodesTable(state=self),
                }

        self.groups = []

        self.next_assignment_is_global = False
        self.parshape = None

        self.ifdepth = [True]

    def __setitem__(self, field, value,
            from_restore = False):

        if from_restore:
            restores_logger.info(
                    ASSIGNMENT_LOG_RECORD,
                    'R', field, repr(value))
        elif self.next_assignment_is_global:
            commands_logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    'G', field, repr(value))
            self.next_assignment_is_global = False
        else:
            commands_logger.debug(
                    ASSIGNMENT_LOG_RECORD,
                    '', field, repr(value))

            if self.groups:
                # XXX This is rather inefficient, because
                # we parse the fieldname twice
                previous = self.get(field, default=None)
                self.groups[-1].remember_restore(field,
                        previous)

        m = re.match(KEYWORD_WITH_INDEX, field)
        if m is not None:

            keyword, index = m.groups()

            for block in [self.registers, self.controls]:
                if keyword in block:
                    block[keyword][int(index)] = value
            return

        if field.startswith('_'):
            self.controls[field].value = value
        else:
            self.controls[field] = value

    def __getitem__(self, field,
            tokens=None,
            the_object_itself=True,
            ):

        if the_object_itself:
            maybe_look_up = lambda x: x
            log_mark = 'TOI '
        else:
            maybe_look_up = lambda x: x.value
            log_mark = ''

        # If it's in the controls table, that's easy.
        if field in self.controls:
            result = self.controls.__getitem__(
                    field,
                    the_object_itself=the_object_itself,
                    )
            commands_logger.debug(r"  -- %s%s==%s",
                    log_mark, field, result)
            return result

        # If it's the name of a registers table (such as "count"),
        # and we have access to the tokeniser, read in the integer
        # which completes the name.
        #
        # Note that you can't subscript controls this way.
        # This is because you shouldn't access these from TeX code.
        if field in self.registers and tokens is not None:
            index = mex.value.Number(tokens).value
            result = self.registers[field][index]
            commands_logger.debug(r"  -- %s%s%d==%s",
                    log_mark, field, index, result)
            return maybe_look_up(result)

        # Or maybe it's already a variable name plus an integer.
        m = re.match(KEYWORD_WITH_INDEX, field)

        if m is not None:
            keyword, index = m.groups()

            for block in (self.registers, self.controls):
                try:
                    result = block[keyword][int(index)]
                    commands_logger.debug(r"  -- %s%s==%s",
                            log_mark, field, result)
                    return maybe_look_up(result)
                except KeyError:
                    pass

        raise KeyError(field)

    def get(self, field, default=None,
            the_object_itself=True,
            tokens=None):
        try:
            return self.__getitem__(field,
                    tokens=tokens,
                    the_object_itself=the_object_itself,
                    )
        except KeyError:
            return default

    def begin_group(self):
        new_group = Group(
                state = self,
                )
        self.groups.append(new_group)
        commands_logger.debug("%s[[ Started group: %s",
                '  '*len(self.groups),
                self.groups)

    def end_group(self):
        if not self.groups:
            raise mex.exception.MexError("More groups ended than began!")

        commands_logger.debug("%s]] Ended group: %s",
                '  '*len(self.groups),
                self.groups)
        ended = self.groups.pop()
        ended.run_restores()

    def showlists(self):
        """
        Implements the \\showlists debugging command.
        See p88 of the TeXbook.
        """
        raise ValueError("showlists...?")
        a="""
        for v in reversed(self.values):
            v['controls']['_mode'].mode.showlist()
            """

    def __len__(self):
        return len(self.groups)+1

    def remember_restore(self, f, v):
        if not self.groups:
            return
        if self.next_assignment_is_global:
            self.next_assignment_is_global = False
            return
        self.groups[-1].remember_restore(f,v)

    @property
    def mode(self):
        return self.controls['_mode'].mode
