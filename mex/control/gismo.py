from mex.control.word import C_ControlWord
from mex.control.string import C_StringControl
import mex.gismo
import logging

commands_logger = logging.getLogger("mex.commands")

class Kern(C_ControlWord):
    def __call__(self, name, tokens):
        distance = mex.value.Dimen(tokens)

        result = mex.gismo.Kern(
                distance = distance,
                )

        commands_logger.debug(f"{name}: created {result}")

        tokens.push(result)

class Special(C_StringControl):
    def handle_string(self, name, s):
        # does nothing by default
        pass
