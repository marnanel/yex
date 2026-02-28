import yex.logging
from yex.control.control import Control, Unexpandable
import yex.exception
import yex.parse

logger = yex.logging.getLogger('control')

class _Arithmetic(Unexpandable):
    """
    Implements the basic arithmetic functions: add or subtract,
    multiply, and divide.
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

class Advance(_Arithmetic):
    """
    Adds two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue += rvalue

class Multiply(_Arithmetic):
    """
    Multiplies two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue *= rvalue

class Divide(_Arithmetic):
    """
    Divides two quantities.
    """
    def do_operation(self, lvalue, rvalue):
        lvalue /= rvalue
