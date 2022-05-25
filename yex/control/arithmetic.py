"""
Arithmetic controls.

These controls implement the basic arithmetic functions: add and subtract,
multiply, and divide.
"""
import logging
from yex.control.control import *
import yex.exception
import yex.parse

logger = logging.getLogger('yex.general')

class C_Arithmetic(C_Unexpandable):
    """
    Adds, multiplies, or divides two quantities.
    """
    def __call__(self, tokens):

        lvalue_name = tokens.next(
                level = 'reading',
                on_eof='raise')

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

        logger.debug(r"\%s %s by %s",
                self, lvalue, rvalue)

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
