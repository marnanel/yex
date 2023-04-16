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
                    "outer horizontal modes because they're wordwrapped")

        self._spaces = {}

        # Requesting the font via subscripting is much slower than
        # simply doing self.doc.font. But it has the advantage that
        # if there's no font set, it will find one. So we call it
        # once, here in the constructor.
        self.doc['_font']

    def _handle_token(self, item, tokens):

        def append_space(ch):

            if ch not in self._spaces:
                self._spaces[ch] = yex.box.Leader(
                    glue = tokens.doc.font.interword,
                    ch = ch,
                    )
            self.append(self._spaces[ch])

        def append_character(ch):

            wordbox = None
            try:
                if isinstance(self.list[-1], yex.box.WordBox):
                    wordbox = self.list[-1]
                    if wordbox.font != tokens.doc.font:
                        wordbox = None
            except IndexError:
                pass

            if wordbox is None:
                wordbox = yex.box.WordBox(
                    font = tokens.doc.font,
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
                append_space(item.ch)
            else:
                append_character(item.ch)

        elif isinstance(item, (yex.parse.Superscript, yex.parse.Subscript)):

            raise yex.exception.ParseError(
                    f"You can't use {item} in {self}.",
                    )

        elif isinstance(item, yex.parse.Space):
            append_space(item.ch)

        elif isinstance(item, yex.parse.Paragraph):

            if self.is_inner:
                return

            tokens.doc.mode.close()

        else:
            raise ValueError(f"What do I do with token {item}?")

    def _calculate_result(self):
        if self.is_inner:
            return super()._calculate_result()
        else:
            return yex.wrap.wrap(
                    items=self.list,
                    doc=self.doc,
                    )

    def append(self, item,
            hyphenpenalty = 50,
            exhyphenpenalty = 50):

        self._result = None
        add_after = None

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

            add_after = yex.box.Breakpoint(demerits)
            logger.debug(
                    '%s: adding discretionary break, then breakpoint: %s',
                    self, self.list)

        super().append(item)

        if add_after is not None:
            super().append(add_after)

class Restricted_Horizontal(Horizontal):
    is_inner = True
