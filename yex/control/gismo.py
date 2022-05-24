"""
Gismo controls.

These controls deal with gismos, which are items inside lists.
Boxes are also gismos, but are covered in yex.control.box;
we may merge these two modules later.
"""
from yex.control.control import *
from yex.control.string import C_StringControl
import yex.box
import logging

logger = logging.getLogger("yex.commands")

class Kern(C_Unexpandable):
    def __call__(self, tokens):
        width = yex.value.Dimen(tokens)

        result = yex.box.Kern(
                width = width,
                )

        logger.debug(f"{self.name}: created {result}")

        tokens.push(result)

class MKern(Kern):
    def __call__(self, tokens):
        # TODO we have no general way of representing mudimen
        raise NotImplementedError()

class Special(C_Unexpandable):
    def handle_string(self, name, s):
        # does nothing by default
        pass
