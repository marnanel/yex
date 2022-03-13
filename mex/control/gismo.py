from mex.control.word import *
from mex.control.string import C_StringControl
import mex.gismo
import logging

commands_logger = logging.getLogger("mex.commands")

class Kern(C_Expandable):
    def __call__(self, name, tokens):
        width = mex.value.Dimen(tokens)

        result = mex.gismo.Kern(
                width = width,
                )

        commands_logger.debug(f"{name}: created {result}")

        tokens.push(result)

class MKern(Kern):
    def __call__(self, name, tokens):
        # TODO we have no general way of representing mudimen
        raise NotImplementedError()

class Special(C_Expandable):
    def handle_string(self, name, s):
        # does nothing by default
        pass
