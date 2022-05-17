from yex.control.control import *
from yex.control.string import C_StringControl
import yex.gismo
import logging

logger = logging.getLogger("yex.commands")

class Kern(C_Unexpandable):
    def __call__(self, tokens):
        width = yex.value.Dimen(tokens)

        result = yex.gismo.Kern(
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
