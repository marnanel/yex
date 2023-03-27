from yex.control import DocumentField
import yex.font
import logging

logger = logging.getLogger('yex.general')

class X__mode(DocumentField):

    our_type = (yex.mode.Mode, str)

    def _get_value(self):
        if self.doc.mode is None:
            self.doc.mode = yex.mode.Vertical(doc=self.doc)
            logger.debug(
                    "created Mode on first request: %s",
                    self.doc.mode)

        return super()._get_value()

    def _set_value(self, value):

        if not hasattr(value, 'append'):
            # okay, maybe it's the name of a mode
            try:
                handler = yex.mode.Mode.handlers[str(value)]
            except KeyError:
                raise ValueError(f"no such mode: {value}")

            if handler.is_inner:
                value = handler(self.doc,
                        recipient = self.doc.mode,
                        )
            else:
                value = handler(self.doc)

        super()._set_value(value)

class X__modelist(DocumentField):

    our_type = list

    def _get_value(self):
        if self.doc.mode is None:
            self.doc['_mode']

        return self.doc.mode.list

    def _set_value(self, value):
        if self.doc.mode is None:
            self.doc['_mode']

        self.doc.mode.list = value

class X__font(DocumentField):

    our_type = (yex.font.Font, str)

    def _get_value(self):
        if not hasattr(self, 'doc'):
            raise ValueError()
        if self.doc.font is None:
            self.doc.font = yex.font.Font.from_name(
                    name=None,
                    doc=self,
                    )
            logger.debug(
                    "created Font on first request: %s",
                    self.doc.font)

        return super()._get_value()

    def _set_value(self, value):
        if isinstance(value, str):
            value = yex.font.Font.from_name(
                    name=value,
                    source=value,
                    doc=self.doc,
                    )
        elif not isinstance(value, yex.font.Font):
            raise TypeError(f'{value} is not a Font but a {type(value)}')

        super()._set_value(value)

class X__fonts(DocumentField):
    our_type = dict

class X__parshape(DocumentField):
    our_type = list

class X__next_assignment_is_global(DocumentField):
    our_type = bool

class X__output(DocumentField):
    our_type = yex.output.Output

class X__created(DocumentField):
    our_type = int

class X__contents(DocumentField):
    our_type = list
