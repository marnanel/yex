import logging
import inspect
import yex

logger = logging.getLogger('yex.general')

def control(fn):

    def native_to_yex(item):
        if isinstance(item, (int, float)):
            return yex.value.Number(item)
        else:
            return item

    class _Control(yex.control.C_Unexpandable):
        def __call__(self, tokens):

            argspec = inspect.getfullargspec(fn)

            fn_args = []

            t = tokens.another(
                    level = 'reading',
                    on_eof = 'raise',
                    )

            for arg in argspec.args:
                annotation = argspec.annotations.get(arg, None)

                if annotation is None:

                    if arg=='tokens':
                        value = t
                    else:
                        value = t.next()

                elif annotation==int:
                    value = int(yex.value.Number.from_tokens(t))

                elif annotation in (
                        yex.value.Number, yex.value.Dimen,
                        yex.value.Glue, yex.value.Muglue,
                        ):
                    value = annotation.from_tokens(t)

                else:
                    raise ValueError(
                            f"Don't understand the annotation {annotation} "
                            f"on {fn}, argument {arg}"
                            )

                logger.debug("%s: param: %s == %s",
                        self, arg, value)
                fn_args.append(value)

            to_push = fn(*fn_args)

            if to_push is None:
                pass
            elif isinstance(to_push, list):
                logger.debug("pushing a list: %s", to_push)

                for item in reversed(to_push):
                    tokens.push(native_to_yex(item))
            else:
                logger.debug("pushing a single item: %s", to_push)
                tokens.push(native_to_yex(to_push))

        def __repr__(self):
            return fn.__name__

    return _Control()
