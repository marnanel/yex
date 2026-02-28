"""
Arithmetic controls.

These controls implement the basic arithmetic functions: add and subtract,
multiply, and divide.
"""
import yex.logging
from yex.control.control import Control, Unexpandable
import yex.exception
import yex.parse

logger = yex.logging.getLogger('control')

class Arithmetic(Unexpandable):
    """
    Adds, multiplies, or divides two quantities.
    """
    def __call__(self, parser):

        lvalue_name = parser.next(
                level = 'expanding',
                on_eof='raise')

        if isinstance(lvalue_name, yex.parse.Token):
            lvalue = parser.doc.get(
                    lvalue_name.identifier,
                    default=None,
                    parser=parser)
        elif isinstance(lvalue_name, Control) and lvalue_name.is_array:
            lvalue = lvalue_name.get_element_from_parser(parser)
        else:
            lvalue = lvalue_name

        parser.eat_optional_spaces()
        parser.optional_string("by")
        parser.eat_optional_spaces()

        rvalue = lvalue.get_type().from_parser(parser)

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
