import logging
import inspect

logger = logging.getLogger('yex.general')

def control(
        **kwargs,
    ):

    PARAMS = {
            'vertical': True,
            'horizontal': True,
            'math': True,

            'expandable': False,
            'even_if_not_expanding': False,
            'push_result': True,
            'conditional': False,
            'bypasses_levels': False,
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

                arg_types = []
                for arg in self.argspec.args:
                    annotation = self.argspec.annotations.get(arg, None)

                    arg_types.append( (arg, annotation) )

                fn_args = yex.control.C_Control.get_arguments_from_tokens(
                        types = arg_types,
                        tokens = tokens,
                        )

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
