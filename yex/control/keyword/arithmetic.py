"""
Arithmetic controls.

These controls implement the basic arithmetic functions: add and subtract,
multiply, and divide.
"""
import logging
from yex.control.control import Control, Unexpandable
import yex.exception
import yex.parse

logger = logging.getLogger('yex.general')

class Arithmetic(Unexpandable):
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
        elif isinstance(lvalue_name, Control) and lvalue_name.is_array:
            lvalue = lvalue_name.get_element_from_tokens(tokens)
        else:
            lvalue = lvalue_name

        tokens.eat_optional_spaces()
        tokens.optional_string("by")
        tokens.eat_optional_spaces()

        rvalue = lvalue.get_type().from_tokens(tokens)

        logger.debug(r"\%s %s by %s",
                self, lvalue, rvalue)

        self.do_operation(lvalue, rvalue)

        logger.debug(r"  -- giving %s",
                lvalue)

class Advance(Arithmetic):
    """
    Adds two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue += rvalue

class Multiply(Arithmetic):
    """
    Multiplies two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue *= rvalue

class Divide(Arithmetic):
    """
    Divides two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue /= rvalue
