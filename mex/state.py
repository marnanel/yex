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

KEYWORD_WITH_INDEX = re.compile('([a-z]+)([0-9]+)')

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

        restores_logger.debug("Remember: %s was %s", f, v)
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

        self.lineno = 1
        self.created_at = datetime.datetime.now()

        self.controls = mex.control.ControlsTable()
        self.controls |= mex.macro.handlers()
        self.controls |= mex.parameter.handlers(self)

        self.fonts = {}

        self.registers = {
                'count': mex.register.CountsTable(),
                'dimen': mex.register.DimensTable(),
                'skip': mex.register.SkipsTable(),
                'muskip': mex.register.MuskipsTable(),
                'toks': mex.register.ToksTable(),
                'box': mex.register.BoxTable(),
                'hyphenation': mex.register.HyphenationTable(),
                'catcode': mex.register.CatcodesTable(),
                'mathcode': mex.register.MathcodesTable(),
                'uccode': mex.register.UccodesTable(),
                'lccode': mex.register.LccodesTable(),
                'sfcode': mex.register.SfcodesTable(),
                'delcode': mex.register.DelcodesTable(),
                }

        self.groups = []

        self.next_assignment_is_global = False

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
            self.registers[keyword][int(index)] = value
            return

        if field.startswith('_'):
            self.controls[field].value = value
        else:
            self.controls[field] = value

    def __getitem__(self, field,
            tokens=None,
            the_object_itself=False,
            ):

        if the_object_itself:
            maybe_look_up = lambda x: x
            log_mark = 'TOI '
        else:
            maybe_look_up = lambda x: x.value
            log_mark = ''

        # If it's in the controls table, that's easy.
        # (The controls table decides whether it's a
        # value lookup, so we don't honour the_object_itself
        # here.)
        if field in self.controls:
            result = self.controls[field]
            commands_logger.info(r"  -- %s%s==%s",
                    log_mark, field, result)
            return result

        # If it's the name of a registers table (such as "count"),
        # and we have access to the tokeniser, read in the integer
        # which completes the name.
        if field in self.registers and tokens is not None:
            index = mex.value.Number(tokens).value
            result = self.registers[field][index]
            commands_logger.info(r"  -- %s%s%d==%s",
                    log_mark, field, index, result)
            return maybe_look_up(result)

        # Or maybe it's already a variable name plus an integer.
        m = re.match(KEYWORD_WITH_INDEX, field)

        if m is not None:
            keyword, index = m.groups()

            try:
                result = self.registers[keyword][int(index)]
                commands_logger.info(r"  -- %s%s==%s",
                        log_mark, field, result)
                return maybe_look_up(result)
            except KeyError:
                pass

        raise KeyError(field)

    def get(self, field, default=None,
            the_object_itself=False,
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
        commands_logger.debug("Started group: %s",
                self.groups)

    def end_group(self):
        if not self.groups:
            raise mex.exception.MexError("More groups ended than began!",
                    self)
        commands_logger.debug("Ended group:   %s",
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

    @property
    def mode(self):
        return self.controls['_mode'].mode
