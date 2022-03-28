from yex.control.word import *
from yex.control.string import C_StringControl
import yex.gismo
import logging

commands_logger = logging.getLogger("yex.commands")

class Kern(C_Unexpandable):
    def __call__(self, name, tokens):
        width = yex.value.Dimen(tokens)

        result = yex.gismo.Kern(
                width = width,
                )

        commands_logger.debug(f"{name}: created {result}")

        tokens.push(result)

class MKern(Kern):
    def __call__(self, name, tokens):
        # TODO we have no general way of representing mudimen
        raise NotImplementedError()

class Special(C_Unexpandable):
    def handle_string(self, name, s):
        # does nothing by default
        pass
