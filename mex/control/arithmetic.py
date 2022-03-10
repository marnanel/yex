import logging
from mex.control.word import *
import mex.exception

macros_logger = logging.getLogger('mex.macros')
commands_logger = logging.getLogger('mex.commands')

class C_Arithmetic(C_Expandable):
    """
    Adds, multiplies, or divides two quantities.
    """
    def __call__(self, name, tokens):

        lvalue_name = tokens.next(
                expand=False,
                on_eof=tokens.EOF_RAISE_EXCEPTION)

        lvalue = tokens.state.get(
                lvalue_name.name,
                default=None,
                tokens=tokens)

        tokens.optional_string("by")
        tokens.eat_optional_spaces()

        rvalue = lvalue.our_type(tokens)

        macros_logger.debug(r"\%s %s by %s",
                name, lvalue, rvalue)

        self.do_operation(lvalue, rvalue)

class Advance(C_Arithmetic):
    """
    Adds two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue += rvalue

class Multiply(C_Arithmetic):
    """
    Multiplies two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue *= rvalue

class Divide(C_Arithmetic):
    """
    Divides two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue /= rvalue
