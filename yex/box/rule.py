import yex.value
import yex.logging
import yex
from yex.box.gismo import *
from yex.box.box import *
from typing import Self

logger = yex.logging.getLogger('box')

class Rule(Box):
    """
    A box which appears black on the page.
    """
    def __str__(self) -> str:
        return fr'[\rule; {self.width}x({self.height}+{self.depth})]'

    @property
    def symbol(self) -> str:
        return '▅'

    def is_void(self) -> bool:
        return False

    @classmethod
    def _find_dimension(cls, parser: 'yex.parse.Parser') -> 'yex.value.Dimen':

        DIMENSIONS = {
                'w': 'idth',
                'h': 'eight',
                'd': 'epth',
                }

        def next_token():
            t = parser.next(
                    on_eof = 'none',
                    level = 'executing',
                    )

            return t

        spaces = parser.eat_optional_spaces(level='querying')

        t = next_token()

        if not isinstance(t, yex.parse.Letter) or t.ch not in DIMENSIONS:
            logger.debug('  -- but %s is not the start of a dimension; bail',
                    t)
            parser.push(t)
            parser.push(spaces)
            return None

        result = [t]

        for c in DIMENSIONS[t.ch]:
            t = next_token()
            if not isinstance(t, yex.parse.Letter) or t.ch!=c:
                logger.debug('  -- "%s%s" is not a dimension; bail',
                        result, t.ch)
                parser.push(t)
                parser.push(result)
                parser.push(spaces)
                return None

            result.append(t)

        result = ''.join([t.ch for t in result])

        logger.debug('  -- the dimension is "%s"', result)
        return result

    @classmethod
    def from_parser(cls, parser: 'yex.parse.Parser',
                    is_horizontal: bool = True,
                    ) -> Self:
        r"""
        Constructs a Rule from tokens. For example:
        ```
            \vrule width5pt height5pt width2pt
        ```

        TeXbook:
            p219

        Args:
            parser: the token source
            is_horizontal: True if this is a horizontal rule, and
                False if it's a vertical rule. This decides default
                values for the result.
        """
        if is_horizontal:
            logger.debug("Rule.from_parser: constructing new hrule.")
            dimensions = {
                    'width': None,
                    'height': yex.value.Dimen(0.4, 'pt'),
                    'depth': yex.value.Dimen(0),
                    }
        else:
            logger.debug("Rule.from_parser: constructing new vrule.")
            dimensions = {
                'width': yex.value.Dimen(0.4, 'pt'),
                'height': None,
                'depth': None,
                }

        while True:

            dimension = cls._find_dimension(parser)

            if dimension is None:
                break

            logger.debug("Rule.from_parser: reading the dimension '%s'",
                    dimension)

            parser.eat_optional_spaces()
            size = yex.value.Dimen.from_parser(parser)
            logger.debug("Rule.from_parser:   -- %s is %s",
                    dimension, size)

            dimensions[dimension] = size

        logger.debug("Rule.from_parser: new dimensions are: %s",
                dimensions)

        result = cls(
                width = dimensions['width'],
                height = dimensions['height'],
                depth = dimensions['depth'],
                )

        logger.debug("Rule.from_parser:   -- new rule is: %s",
                result)

        return result
