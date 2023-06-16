import yex
from yex.box.box import *
from yex.box.gismo import *
from yex.box.kern import Kern
from yex.box.hvbox import *
import logging

logger = logging.getLogger('yex.general')

class WordBox(HBox):
    """
    A box holding a sequence of characters, all in the same font.

    Not something in TeX. This exists because the TeXbook says
    about character tokens in horizontal mode (p282):

    "If two or more commands of this type occur in succession,
    TEX processes them all as a unit, converting to ligatures
    and/or inserting kerns as directed by the font information."

    Attributes:
        font (Font): the font these characters are in.
        source_index (int or None): when this WordBox has gone through
            word-wrapping, this is the index of the same WordBox
            in the list which was wrapped. In all other cases, this is None.

            The actual numbers are unreliable, because lists change often.
            The only guarantee is that all the source_indexes will be
            unique and ascending, immediately after wrapping.
    """

    def __init__(self, font):
        super().__init__()
        self.font = font
        self.source_index = None

    def append(self, ch):
        if not isinstance(ch, str):
            raise TypeError(
                    f'WordBoxes can only hold characters '
                    f'(and not {ch}, which is {type(ch)})')
        elif len(ch)!=1:
            raise TypeError(
                    f'You can only add one character at a time to '
                    f'a WordBox (and not "{ch}")')

        new_char = CharBox(
                ch = ch,
                font = self.font,
                )

        font_metrics = self.font.metrics

        previous = None
        try:
            previous = self.contents[-1].ch
        except IndexError as e:
            pass
        except AttributeError as e:
            pass

        if previous is not None:
            pair = previous + ch

            kern_size = font_metrics.kerns.get(pair, None)

            if kern_size is not None:
                new_kern = Kern(width=kern_size)
                logger.debug("%s: adding kern: %s",
                        self, new_kern)

                self.contents.append(new_kern)
                self._adjust_dimens_for_item(new_kern)
                logger.debug("%s: added kern: %s", self, new_kern)

            else:

                ligature = font_metrics.ligatures.get(pair, None)

                if ligature is not None:

                    left_hand = self.contents.pop()

                    new_char = CharBox(
                            ch = ligature,
                            font = self.font,
                            )

                    new_char.from_ligature = (
                        left_hand.from_ligature or previous) + ch

                    self.width -= left_hand.width
                    self.height = max([n.height-n.shifted_by
                        for n in self.contents],
                        default=yex.value.Dimen())
                    self.depth = max([n.depth+n.shifted_by
                        for n in self.contents],
                        default=yex.value.Dimen())

                    logger.debug(
                        "%s: adding ligature: briefly w=%s, h=%s, d=%s",
                        self,
                        self.width, self.height, self.depth,
                        )

        self.contents.append(new_char)
        self._adjust_dimens_for_item(new_char)
        self._ch_cache = None
        logger.debug("%s: adding %s after %s: now w=%s, h=%s, d=%s",
                self, str(new_char), str(previous),
                self.width, self.height, self.depth,
                )

    def __repr__(self):
        result = f'[wordbox;{self.ch}'

        if self.source_index is not None:
            result += f';s={self.source_index}'

        result += ']'

        return result

    def showbox(self):
        r"""
        Returns a list of lines to be displayed by \showbox.

        WordBox doesn't appear in the output because it's not
        something that TeX displays.
        """
        return sum(
                [x.showbox() for x in self.contents],
                [])

    @property
    def symbol(self):
        if self.contents:
            return self.contents[0].symbol
        else:
            return '∅'
