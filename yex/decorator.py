import logging
import inspect

logger = logging.getLogger('yex.general')

def control(
        **kwargs,
    ):

    ALL_ARGS_SUFFIX = 'all_args'

    PARAMS = {
            'vertical': True,
            'horizontal': True,
            'math': True,

            'expandable': False,
            'even_if_not_expanding': False,
            'push_result': True,
            'conditional': False,
            }

    for k in kwargs.keys():
        if k not in PARAMS:
            raise ValueError(
                    f"yex.decorator.control has no {k} param")

    def _control(fn):

        from yex.control.control import C_Expandable, C_Unexpandable

        def native_to_yex(item):
            import yex.value

            if isinstance(item, (int, float)):
                return yex.value.Number(item)
            else:
                return item

        def all_args(tokens, level):

            s = ''

            for t in tokens.another(
                    level=level,
                    single=True,
                    on_eof='exhaust',
                    ):
                s += str(t)

            return s

        if kwargs.get('expandable', False):
            parent_class = C_Expandable
        else:
            parent_class = C_Unexpandable

        class _Control(parent_class):

            # attributes in PARAMS are set just after this class definition

            argspec = inspect.getfullargspec(fn)
            __doc__ = fn.__doc__

            conditional = kwargs.get('conditional', False)

            def __init__(self, *fn_args, **fn_kwargs):
                super().__init__(*fn_args, **fn_kwargs)

            def __call__(self, tokens):
                import yex.value

                fn_args = []

                t = tokens.another(
                        level = 'reading',
                        on_eof = 'raise',
                        )

                for arg in self.argspec.args:
                    annotation = self.argspec.annotations.get(arg, None)

                    if annotation is None:

                        # No annotation, but perhaps we can work it out
                        # from the name.

                        if arg=='tokens':
                            value = tokens
                        elif arg.endswith(ALL_ARGS_SUFFIX):
                            value = all_args(
                                    tokens = tokens,
                                    level = arg[:-len(ALL_ARGS_SUFFIX)-1],
                                    )
                        else:
                            raise yex.exception.WeirdControlNameError(
                                    control = fn,
                                    argname = arg,
                                    )

                    elif issubclass(annotation, int):
                        value = int(yex.value.Number.from_tokens(t))

                    elif issubclass(annotation, yex.parse.Location):
                        value = tokens.location

                    elif issubclass(annotation, (
                            yex.parse.Token,
                            yex.control.C_Control,
                            )):

                        # These might be in the token stream,
                        # in their own right.

                        value = t.next()

                        if not isinstance(value, annotation):
                            raise yex.exception.NeededSomethingElseError(
                                    needed = annotation,
                                    problem = value,
                                    )

                    elif issubclass(annotation, (
                            yex.value.Value,
                            yex.box.Gismo,
                            yex.filename.Filename,
                            )):

                        # These can be constructed from the token stream.

                        value = annotation.from_tokens(t)

                    else:
                        raise yex.exception.WeirdControlAnnotationError(
                                annotation = annotation,
                                control = fn,
                                arg = arg,
                                )

                    logger.debug("%s: param: %s == %s",
                            self, arg, value)
                    fn_args.append(value)

                received = fn(*fn_args)
                logger.debug("%s: result: %s", self, received)

                if received is None:
                    pass

                elif not kwargs.get('push_result', True):
                    pass

                elif isinstance(received, list):
                    for item in reversed(received):
                        tokens.push(native_to_yex(item),
                                is_result=True,
                                )

                else:
                    tokens.push(native_to_yex(received),
                            is_result=True,
                            )

                return received

            def __repr__(self):
                return '[\\'+fn.__name__.lower()+']'

        for f,v in PARAMS.items():
            setattr(_Control, f,
                    kwargs.get(f, v))
        _Control.__name__ = fn.__name__.title()

        return _Control

    return _control
