import logging
from yex.control.word import *
import yex.exception
import yex.parse

macros_logger = logging.getLogger('yex.macros')
commands_logger = logging.getLogger('yex.commands')

class C_Arithmetic(C_Unexpandable):
    """
    Adds, multiplies, or divides two quantities.
    """
    def __call__(self, name, tokens):

        lvalue_name = tokens.next(
                expand=False,
                on_eof=tokens.EOF_RAISE_EXCEPTION)

        if isinstance(lvalue_name, yex.parse.Token):
            lvalue = tokens.doc.get(
                    lvalue_name.identifier,
                    default=None,
                    tokens=tokens)
        else:
            lvalue = lvalue_name

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
