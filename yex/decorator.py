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

            'even_if_not_expanding': False,
            }

    for k in kwargs.keys():
        if k not in PARAMS:
            raise ValueError(
                    f"yex.decorator.control has no {k} param")

    def _control(fn):

        from yex.control.control import C_Unexpandable

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
                    ):
                s += str(t)

            return s

        class _Control(C_Unexpandable):

            # attributes in PARAMS are set just after this class definition

            argspec = inspect.getfullargspec(fn)
            __doc__ = fn.__doc__

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

                        if arg=='tokens':
                            value = tokens
                        elif arg.endswith(ALL_ARGS_SUFFIX):
                            value = all_args(
                                    tokens = tokens,
                                    level = arg[:-len(ALL_ARGS_SUFFIX)-1],
                                    )
                        else:
                            raise ValueError(
                                    "I don't understand the name "
                                    f'of argument {arg} on {fn.__name__}.'
                                    )

                    elif issubclass(annotation, int):
                        value = int(yex.value.Number.from_tokens(t))

                    elif issubclass(annotation, yex.parse.Location):
                        value = tokens.location

                    elif issubclass(annotation, yex.parse.Token):
                        value = t.next()

                        if not issubclass(value, annotation):
                            raise ValueError(
                                    'I needed a {annotation}, not '
                                    '{value} (which is a {value.__class__}).'
                                    )

                    elif issubclass(annotation, (
                            yex.value.Value,
                            yex.box.Gismo,
                            )):
                        value = annotation.from_tokens(t)

                    else:
                        raise ValueError(
                                f"I don't understand the annotation "
                                f'{annotation} '
                                f'on {fn.__name__}, argument {arg}.'
                                )

                    logger.debug("%s: param: %s == %s",
                            self, arg, value)
                    fn_args.append(value)

                to_push = fn(*fn_args)
                logger.debug("%s: result: %s", self, to_push)

                if to_push is None:
                    pass
                elif isinstance(to_push, list):

                    for item in reversed(to_push):
                        tokens.push(native_to_yex(item),
                                is_result=True,
                                )
                else:
                    tokens.push(native_to_yex(to_push),
                            is_result=True,
                            )

            def __repr__(self):
                return '[\\'+fn.__name__.lower()+']'

        for f,v in PARAMS.items():
            setattr(_Control, f,
                    kwargs.get(f, v))
        _Control.__name__ = fn.__name__.title()

        return _Control

    return _control
