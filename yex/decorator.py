import logging
import inspect
import functools

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

        argspec = inspect.getfullargspec(fn)
        class _Control(parent_class):

            # attributes in PARAMS are set just after this class definition

            __doc__ = fn.__doc__

            conditional = kwargs.get('conditional', False)

            def __init__(self, *fn_args, **fn_kwargs):
                super().__init__(*fn_args, **fn_kwargs)

            def __call__(self, tokens):

                fn_args = _argspec_to_fn_args(argspec, tokens,
                        self_object = None,
                        )

                received = fn(*fn_args)
                logger.debug("%s: result: %s", self, received)

                if received is None:
                    pass

                elif not kwargs.get('push_result', True):
                    logger.debug(
                            "%s:   -- push_result is False; returning that",
                            self)

                elif isinstance(received, list):
                    for item in reversed(received):
                        tokens.push(native_to_yex(item),
                                is_result=True,
                                )
                    return None

                else:
                    tokens.push(native_to_yex(received),
                            is_result=True,
                            )
                    return None

                return received

            @classmethod
            def on_query(cls):
                class _QueryDescriptor:
                    def __get__(self, obj, cls):
                        # We pass in doc rather than self because
                        # self exists only wrt this decorator;
                        # from the decorated function's view it doesn't
                        # exist.
                        return obj._get_value_via_decorator(doc=obj.doc)

                def _get_value(fn):
                    cls.is_queryable = True
                    cls._get_value_via_decorator = staticmethod(fn)
                    cls.value = _QueryDescriptor()
                    return cls

                return _get_value

            def __repr__(self):
                return '[\\'+fn.__name__.lower()+']'

        for f,v in PARAMS.items():
            setattr(_Control, f,
                    kwargs.get(f, v))
        _Control.__name__ = fn.__name__.title()

        return _Control

    return _control

##################

def array():

    import yex

    def _array(fn):

        from yex.control.control import C_Unexpandable

        argspec = inspect.getfullargspec(fn)
        class _Array(C_Unexpandable):

            is_array = True
            __doc__ = fn.__doc__

            def __init__(self, *fn_args, **fn_kwargs):
                super().__init__(*fn_args, **fn_kwargs)

            def __call__(self, tokens):
                raise yex.exception.CalledAnArrayError()

            def get_member(self, *args, **kwargs):

                result = fn(*args, **kwargs)
                logger.debug("%s: result: %s", self, result)

                self._check_result(result)

                return result

            def get_member_from_tokens(self, tokens):

                fn_args = _argspec_to_fn_args(argspec, tokens,
                        self_object = None,
                        )

                result = fn(*fn_args)
                logger.debug("%s: result: %s", self, result)

                self._check_result(result)

                return result

            def _check_result(self, result):
                if not isinstance(result, yex.control.C_Unexpandable) or \
                        not result.is_queryable:
                            raise yex.exception.ArrayReturnWasWeirdError(
                                    problem = result,
                                    )

            def __repr__(self):
                return '[\\'+fn.__name__.lower()+']'

        _Array.__name__ = fn.__name__.title()
        _Array.__doc__ = fn.__doc__

        return _Array

    return _array

##################

def get_member_from_tokens_method(
        **kwargs,
        ):
    def _get_member_from_tokens(fn):

        argspec = _check_first_element_is_self(inspect.getfullargspec(fn))

        def get_member_from_tokens(self, tokens):
            fn_args = _argspec_to_fn_args(argspec, tokens,
                    self_object = self,
                    )

            received = fn(*fn_args)
            logger.debug("%s: %s.get_member_from_tokens(%s) returns %s",
                self, fn, fn_args, received)
            return received

        return get_member_from_tokens

    return _get_member_from_tokens

def _argspec_to_fn_args(argspec, tokens, self_object):

    import yex.control

    logger.debug("argspec %s", argspec)
    args = argspec.args

    if self_object is not None:
        _check_first_element_is_self(argspec)
        args = args[1:]
        logger.debug("args: %s (dropped 'self')", args)

    arg_types = []
    for arg in args:
        annotation = argspec.annotations.get(arg, None)

        arg_types.append( (arg, annotation) )

    logger.debug("arg_types: %s", arg_types)

    fn_args = yex.control.C_Control.get_arguments_from_tokens(
            types = arg_types,
            tokens = tokens,
            )

    if self_object is not None:
        fn_args.insert(0, self_object)

    return fn_args

def _check_first_element_is_self(a):
    import yex.exception

    if not a.args:
        raise yex.exception.ArgspecSelfError()

    if a.args[0]!='self':
        raise yex.exception.ArgspecSelfError()

    return a
