import logging
import yex.exception

logger = logging.getLogger('yex.general')

class C_Control:
    """
    Superclass of all controls.

    A control has:
       - a name, which is a string. If you don't pass one in,
            we default to the name of the class in lowercase.
       - a __call__() method, which causes it to run
       - the flags is_long and is_outer, which affect
            where it can be called

    Each control is usually referred to by at least one
    yex.parse.Control object in a given Document. But those objects
    are symbols, and these are procedures; don't get them confused.

    A Document keeps track of many controls. The control
    doesn't know which doc it's in, but when it's called, it
    can find it by looking in the `doc` field of `tokens`.

    Some controls (such as the superclass) have names
    beginning with `C_`. This is so that they can't be called
    from TeX code; TeX identifiers can't contain underscores.
    If they began with a plain underscore, Python wouldn't export
    them from their modules.
    """

    even_if_not_expanding = False
    conditional = False

    is_array = False
    is_queryable = False

    def __init__(self,
            is_long = False,
            is_outer = False,
            name = None,
            doc = None,
            *args, **kwargs):

        self.is_long = is_long
        self.is_outer = is_outer
        self.doc = doc

        if name is None:
            self.name = self.__class__.__name__.lower()
        else:
            self.name = name

    @property
    def identifier(self):
        """
        A good string to use for looking up this control in a document.

        In practice, it could be stored under a different string as well,
        or instead, or it might not be stored at all. But this is often
        a reasonable shot.
        """
        return fr'\{self.name}'

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def query(self, *args, **kwargs):
        return self.value

    def __str__(self):
        return fr'\{self.name}'

    def __repr__(self):
        return fr'[\{self.name}]'

    @classmethod
    def from_serial(self, state):
        name = state['control'][0].upper() + \
                state['control'][1:].lower()

        if not hasattr(yex.control, name):
            raise KeyError(state['control'])

        result = getattr(yex.control, name)()

        if 'value' in state:
            result.value = state['value']

        return result

    @classmethod
    def get_arguments_from_tokens(cls, types, tokens):
        result = []

        ALL_ARGS_SUFFIX = 'all_args'

        t = tokens.another(
                level = 'reading',
                on_eof = 'raise',
                )

        logger.debug('args: Looking for these arguments: %s', types)
        logger.debug('args: from this Expander: %s', tokens)

        for arg in types:

            if isinstance(arg, tuple):
                the_name, the_type = arg
                logger.debug('args: finding arg "%s", annotated as %s',
                        the_name, the_type)
            else:
                the_name = None
                the_type = arg
                logger.debug('args: finding arg "%s", with no annotation',
                        the_name)

            if the_type is None:

                # This argument has no type annotation.
                # Perhaps we can work it out from the the_name?

                if the_name=='tokens':
                    value = tokens
                elif the_name=='doc':
                    value = tokens.doc
                elif the_name=='optional_equals':
                    value = tokens.eat_optional_char('=')
                elif the_name.endswith(ALL_ARGS_SUFFIX):
                    value = ''

                    level = the_name[:-len(ALL_ARGS_SUFFIX)-1],
                    logger.debug('args: slurping up tokens at level "%s"',
                            level)

                    for t in tokens.another(
                            level=level,
                            bounded='single',
                            on_eof='exhaust',
                            ):
                        value += str(t)

                    logger.debug('args: which gives us: %s',
                            value)

                else:
                    logger.debug(
                            "args: can't work that out with no annotation")

                    raise yex.exception.WeirdControlNameError(
                            argname = the_name,
                            )

            elif issubclass(the_type, int):
                logger.debug('args: looking for an integer')

                value = int(yex.value.Number.from_tokens(t))

            elif issubclass(the_type, yex.parse.Location):
                value = t.location

            elif issubclass(the_type, (
                    yex.parse.Token,
                    yex.control.C_Control,
                    )):

                logger.debug('args: looking for a %s in its own right',
                        the_type.__name__)

                # These might be in the token stream,
                # in their own right.

                value = t.next()

                if not isinstance(value, the_type):
                    logger.debug('args:   -- but we found a %s',
                            value.__class__.__name__)

                    raise yex.exception.NeededSomethingElseError(
                            needed = the_type,
                            problem = value,
                            )

            elif issubclass(the_type, (
                    yex.value.Value,
                    yex.box.Gismo,
                    yex.filename.Filename,
                    )):

                # These can be constructed from the token stream.

                logger.debug('args: constructing a %s',
                        the_type.__name__)

                value = the_type.from_tokens(t)

            else:
                logger.debug(
                        "args: can't work out an annotation of %s",
                        the_type.__name__)

                raise yex.exception.WeirdControlAnnotationError(
                        type = the_type,
                        control = fn,
                        the_name = the_name,
                        )

            logger.debug("args:  -- so %s == %s", the_name, value)
            result.append(value)

        logger.debug("args: result: %s", result)
        return result

class C_Expandable(C_Control):
    """
    Superclass of all expandable controls.

    Expandable controls include all macros, and
    some control flow primitives.

    For full details, see the TeXbook, p211f.
    """
    def __call__(self, tokens):
        logger.warning("%s: not implemented; you REALLY need to fix that",
                self)
        raise NotImplementedError()

    def __getstate__(self):
        return {
                'control': self.name,
                }

class C_Unexpandable(C_Control):
    """
    Superclass of all unexpandable controls.

    Unexpandable controls are the most basic primitives.
    All of them carry flags saying which modes they can
    run in. True means the control is permitted;
    False means it's forbidden; a string which is the name of a mode
    forces a switch to that mode before it's used.

    For full details, see the TeXbook, p211f.
    """

    vertical = True
    horizontal = True
    math = True

    def __call__(self, tokens):
        logger.warning("%s: not implemented; you need to fix that",
                self)
        raise NotImplementedError()

    def __getstate__(self):
        result = {
                'control': self.name,
                }

        # There is no need to return the modes:
        # they're derivable from the name of the control.

        return result
