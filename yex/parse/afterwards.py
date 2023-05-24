import logging

logger = logging.getLogger('yex.general')

class Afterwards:
    """
    For Expander's on_push attr; pushes an item on the first is_result=True
    """
    def __init__(self, item):
        self.item = item
        logger.debug("%s: begins", self)

    def __call__(self, tokens, thing, is_result):
        if is_result:
            if self.item is not None:
                tokens.push(self.item)
                logger.debug("%s: pushed; it's gone now", self)
                self.item = None
            else:
                logger.debug("%s: nothing here any more", self)

    def __repr__(self):
        return '[ea;%04x;%s]' % (id(self)%0xFFFF, self.item)
