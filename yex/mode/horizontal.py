import yex.box
import yex.value
import yex.wrap
from yex.mode.mode import Mode
import yex.parse
import logging

logger = logging.getLogger('yex.general')

class Horizontal(Mode):
    is_horizontal = True
    default_box_type = yex.box.HBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_inner and (
                self.to is not None or self.spread is not None):
            raise ValueError("'to' and 'spread' can't be set on "
                    "Horizontal modes because they're wordwrapped")

    def _handle_token(self, item, tokens):

        def append_space():
            font = tokens.doc['_font']

            interword_space = font[2]
            interword_stretch = font[3]
            interword_shrink = font[4]

            self.append(yex.box.yex.box.Leader(
                    space = interword_space,
                    stretch = interword_stretch,
                    shrink = interword_shrink,
                    ))

        def append_character(ch):

            current_font = tokens.doc['_font']

            wordbox = None
            try:
                if isinstance(self.list[-1], yex.box.WordBox):
                    wordbox = self.list[-1]
                    if wordbox.font != current_font:
                        wordbox = None
            except IndexError:
                pass

            if wordbox is None:
                wordbox = yex.box.WordBox(
                    font = current_font,
                        )
                self.append(wordbox)

            wordbox.append(ch)
            logger.debug(
                    "%s: added %s to wordbox: %s",
                    self, item, wordbox,
                    )

        if isinstance(item,
                (yex.parse.Letter, yex.parse.Other)
                ):

            if item.ch==' ':
                # This will be a space produced by a tie.
                # It's protected from being treated as a space until
                # it reaches here, so that the wordwrap routines
                # can't split it.
                append_space()
            else:
                append_character(item.ch)

        elif isinstance(item, (yex.parse.Superscript, yex.parse.Subscript)):

            raise yex.exception.ParseError(
                    f"You can't use {item} in {self}.",
                    )

        elif isinstance(item, yex.parse.Space):
            append_space()

        elif isinstance(item, yex.parse.Paragraph):

            if self.is_inner:
                return

            # FIXME: \unskip \penalty10000 \hskip\parfillskip

            tokens.doc.end_group()

        else:
            raise ValueError(f"What do I do with token {item}?")

    @property
    def result(self):
        if self.is_inner:
            return super().result
        else:
            return yex.wrap.wrap(
                    items=self.list,
                    doc=self.doc,
                    )

    def _start_up(self):
        logger.debug("%s: I'm new",
                self)

    def append(self, item,
            hyphenpenalty = 50,
            exhyphenpenalty = 50):

        if not self.list:
            self._start_up()

        def is_glue(item):
            return isinstance(item, yex.box.Leader) and \
                    isinstance(item.glue, yex.value.Glue)

        try:
            previous = self.list[-1]
        except IndexError:
            previous = None
            super().append(yex.box.Breakpoint())
            logger.debug(
                    '%s: added initial breakpoint: %s',
                    self, self.list)

        if is_glue(item):
            if previous is not None and not previous.discardable:
                super().append(yex.box.Breakpoint())
                logger.debug(
                        '%s: added breakpoint before glue: %s',
                        self, self.list)

            elif isinstance(previous, yex.box.Kern):

                self.list.insert(-1, yex.box.Breakpoint())

                logger.debug(
                        '%s: added breakpoint before previous kern: %s',
                        self, self.list)

            elif isinstance(previous,
                    yex.box.MathSwitch) and previous.which==False:

                self.list.insert(-1, yex.box.Breakpoint())

                logger.debug(
                        '%s: added breakpoint before previous math-off: %s',
                        self, self.list)

        elif isinstance(item, yex.box.Penalty):
            super().append(yex.box.Breakpoint(item.demerits))
            logger.debug(
                    '%s: added penalty breakpoint: %s',
                    self, self.list)

        elif isinstance(item, yex.box.DiscretionaryBreak):

            try:
                if previous.ch!='':
                    demerits = exhyphenpenalty
                else:
                    demerits = hyphenpenalty
            except AttributeError:
                demerits = exhyphenpenalty

            super().append(yex.box.Breakpoint(demerits))
            logger.debug(
                    '%s: added breakpoint before discretionary break: %s',
                    self, self.list)

        super().append(item)

class Restricted_Horizontal(Horizontal):
    is_inner = True
