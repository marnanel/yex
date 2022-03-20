import datetime
import yex.value
import yex.box
import yex.control
import yex.register
import yex.mode
import yex.exception
import re
import logging

commands_logger = logging.getLogger('yex.macros')
macros_logger = logging.getLogger('yex.macros')
restores_logger = logging.getLogger('yex.restores')

ASSIGNMENT_LOG_RECORD = "%s %-8s = %s"

KEYWORD_WITH_INDEX = re.compile(r'^([^;]+?);?(-?[0-9]+)$')

class Group:
    def __init__(self, state):
        self.state = state
        self.restores = {}

    def remember_restore(self, f, v):

        if f in ('inputlineno', ):
            # that makes no sense
            return

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

class _Ifdepth_List(list):
    """
    Just like an ordinary list, except that its representation
    is suited for printing a list of booleans compactly.
    """
    def __repr__(self):
        def _repr(v):
            if v==True:
                return 'T'
            elif v==False:
                return 'f'
            else:
                return repr(v)
        result = ''.join([_repr(v) for v in self])
        return result

class Callframe:
    """
    Description of a macro call.

    Only used for tracebacks; the macros take care of themselves.

    Stored in the list State.call_stack.
    """
    def __init__(self,
            callee,
            args,
            location,
            ):
        self.callee = callee
        self.args = args
        self.location = location

    def __repr__(self):
        args = ','.join([
            ''.join([c.ch for c in v])
            for (f,v) in sorted(self.args.items())])
        return f'{self.callee}({args}):{self.location}'

class State:

    mode_handlers = yex.mode.handlers()

    def __init__(self):

        self.created_at = datetime.datetime.now()

        self.controls = yex.control.ControlsTable()
        self.controls |= yex.control.handlers()

        self.fonts = {}

        self.registers = yex.register.handlers(state=self)

        self.groups = []

        self.next_assignment_is_global = False
        self.parshape = None

        self.ifdepth = _Ifdepth_List([True])
        self.call_stack = []

        self.font = None
        self.mode = None
        self.output = None

    def __setitem__(self, field, value,
            from_restore = False):

        if field.startswith('_'):
            return self._setitem_internal(field, value, from_restore)

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
                    break
            return

        if field.startswith('_'):
            self.controls[field].value = value
        else:
            self.controls[field] = value

    def __getitem__(self, field,
            tokens=None,
            the_object_itself=True,
            ):

        if field.startswith('_'):
            return self._getitem_internal(field, tokens)

        if the_object_itself:
            maybe_look_up = lambda x: x
            log_mark = 'TOI '
        else:
            maybe_look_up = lambda x: x.value
            log_mark = ''

        # If it's the name of a registers table (such as "count"),
        # and we have access to the tokeniser, read in the integer
        # which completes the name.
        #
        # Note that you can't subscript controls this way.
        # This is because you shouldn't access these from TeX code.
        if field in self.registers and tokens is not None:
            index = yex.value.Number(tokens).value
            result = self.registers[field][index]
            commands_logger.debug(r"  -- %s%s%d==%s",
                    log_mark, field, index, result)
            return maybe_look_up(result)

        # If it's in the controls table, that's easy.
        if field in self.controls:
            result = self.controls.__getitem__(
                    field,
                    the_object_itself=the_object_itself,
                    )
            commands_logger.debug(r"  -- %s%s==%s",
                    log_mark, field, result)
            return result

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

    def _setitem_internal(self, field, value, from_restore):
        if field=='_font':
            self.font = yex.font.Font(
                    filename=value,
                    )
        elif field=='_mode':
            if isinstance(value, yex.mode.Mode):
                self.mode = value
            elif value is None:
                self.value = None
            else:
                try:
                    self.mode = self.mode_handlers[str(value)](self)
                except KeyError:
                    raise ValueError(f"no such mode: {value}")
        elif field=='_output':
            if isinstance(value, yex.output.Output):
                self.output = value
            elif value is None:
                self.value = None
            else:
                try:
                    self.mode = self.mode_handlers[str(value)](
                            filename=None, # TODO
                            )
                except KeyError:
                    raise ValueError(f"no such output: {value}")
        else:
            raise KeyError(field)

    def _getitem_internal(self, field, tokens):
        if field=='_font':
            if self.font is None:
                self.font = yex.font.Font(
                        filename='cmr10.tfm',
                        )
                commands_logger.debug(
                        "created Font on first request: %s",
                        self.font)
            return self.font

            pass
        elif field=='_mode':
            if self.mode is None:
                self.mode = yex.mode.Vertical(state=self)
                commands_logger.debug(
                        "created Mode on first request: %s",
                        self.mode)
            return self.mode
        elif field=='_output':
            if self.output is None:
                self.output = yex.output.get_default()(
                        state=self,
                        filename=None, # TODO
                        )
                commands_logger.debug(
                        "created Output on first request: %s",
                        self.output)
            return self.output
        else:
            raise KeyError(field)

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
            raise yex.exception.YexError("More groups ended than began!")

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
