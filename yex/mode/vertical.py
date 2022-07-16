import yex.box
import yex.value
from yex.mode.mode import Mode
import yex.parse
import logging

logger = logging.getLogger('yex.general')

class Vertical(Mode):
    is_vertical = True
    our_type = yex.box.VBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def exercise_page_builder(self):
        logger.info("%s: page builder exercised",
                self)

        self.doc[r'\box255'] = yex.box.VBox(self.list)
        self.list = []

        group = self.doc.begin_group()

        self.doc.read(
                self.doc[r'\output'].value,
                level = 'executing',
                )

        self.doc.end_group(group = group)

    def _handle_token(self, item, tokens):

        if isinstance(item, (yex.parse.Letter, yex.parse.Other)):

            logger.debug("%s: symbol forcing us to horizontal mode: %s",
                    self, item)

            tokens.push(item)
            tokens.push(yex.control.Indent())

        elif isinstance(item, (yex.parse.Superscript, yex.parse.Subscript)):

            raise yex.exception.ParseError(
                    f"You can't use {item} in {self}.",
                    )

        elif isinstance(item, yex.parse.Paragraph):

            pass # nothing

        elif isinstance(item, yex.parse.Space):

            pass # nothing

        else:
            raise ValueError(f"What do I do with token {item}?")

    def _start_up(self):
        logger.debug("%s: I'm new",
                self)

        self.doc[r'\prevdepth'] = yex.value.Dimen(-1000, 'pt')

    def append(self, item):

        # This algorithm is given on pp79-80 of the TeXbook.

        if not self.list:
            self._start_up()

        if isinstance(item, yex.box.Rule):
            logger.debug(
                    "%s: appending rule, with no interline glue: %s",
                    self, item)
            super().append(item)
            self.doc[r'\prevdepth'] = yex.value.Dimen(-1000, 'pt')
            return

        elif isinstance(item, yex.box.Leader):
            logger.debug(
                    "%s: appending space: %s",
                    self, item)
            super().append(item)
            self.doc[r'\prevdepth'] = item.depth
            return

        prevdepth = self.doc[r'\prevdepth'].value
        baselineskip = self.doc[r'\baselineskip'].value
        basic_skip = baselineskip.space - prevdepth - item.height

        if prevdepth <= yex.value.Dimen(-1000):
            logger.debug("%s: we don't need any extra padding for %s: "
                    "%s<=-1000pt",
                self, item, prevdepth)

        elif basic_skip < self.doc[r'\lineskip'].value.space:
            addendum = yex.box.Leader(
                    space = basic_skip,
                    stretch = baselineskip.stretch,
                    shrink = baselineskip.shrink,
                    )
            logger.debug("%s: adding calculated glue: %s",
                self, addendum)
            self.list.append(addendum)

        else:
            lineskip = self.doc[r'\lineskip'].value
            addendum = yex.box.Leader(
                    space = lineskip.space,
                    stretch = lineskip.stretch,
                    shrink = lineskip.shrink,
                    )
            logger.debug(r"%s: adding \lineskip: %s",
                self, addendum)
            self.list.append(addendum)

        self.doc[r'\prevdepth'] = item.depth

        super().append(item)

class Internal_Vertical(Vertical):
    is_inner = True
