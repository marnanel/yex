import logging
import yex

logger = logging.getLogger('yex.general')

class PushMonitor:
    def __init__(self, handler, tokens,
            push_after_expansion=None,
            ):

        self.handler = handler
        self.push_after_expansion = push_after_expansion

        if tokens.push_cb is None:
            self.tokens = tokens
        else:
            self.tokens = tokens.another(force_new=True)

        self.stack_size_at_start = None

        self.seen_results = False

    def _stack_size(self):
        return len(self.tokens.tokeniser.source.push_back)

    def __enter__(self):
        self.tokens.push_cb = self
        self.stack_size_at_start = self._stack_size()
        return self

    def __call__(self, thing, is_result):

        if is_result:
            self.seen_results = True

            if self.push_after_expansion is not None:
                self._do_push_after_expansion("this is a result")

    def _do_push_after_expansion(self, message):
        logger.debug("%s: %s, so push %s",
                self, message, self.push_after_expansion)
        self.tokens.push(self.push_after_expansion)
        self.push_after_expansion = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        stack_size_at_end = self._stack_size()

        if stack_size_at_end > self.stack_size_at_start:
            if not self.seen_results:
                logger.debug("%s: stack size at start: %s",
                        self, self.stack_size_at_start)
                logger.debug("%s: stack size at end: %s",
                        self, stack_size_at_end)
                logger.debug("%s: stack at end: %s",
                        self, self.tokens.tokeniser.source.push_back)

                raise ValueError(
                        f"The handler for {self.handler} left results "
                        f"on the stack, but it didn't push any of them "
                        f"with is_result=True."
                        )

        if self.push_after_expansion:
            self._do_push_after_expansion("we're done")

    def __repr__(self):
        return '[pm;'+repr(self.tokens)[1:]
