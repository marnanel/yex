import yex.value
import logging
import yex
from yex.box.gismo import *
from yex.box.box import *

logger = logging.getLogger('yex.general')

class Rule(Box):
    """
    A box which appears black on the page.
    """
    def __str__(self):
        return fr'[\rule; {self.width}x({self.height}+{self.depth})]'

    @property
    def symbol(self):
        return '▅'

    @classmethod
    def _get_dimension(cls, tokens):

        DIMENSIONS = {
                'w': 'idth',
                'h': 'eight',
                'd': 'epth',
                }

        def next_token():
            t = tokens.next(
                    on_eof = 'none',
                    level = 'deep',
                    )

            return t

        t = next_token()

        if not isinstance(t, yex.parse.Letter) or t.ch not in DIMENSIONS:
            logger.debug('  -- but %s is not the start of a dimension; bail',
                    t)
            tokens.push(t)
            return None

        result = t.ch

        for c in DIMENSIONS[t.ch]:
            t = next_token()
            if not isinstance(t, yex.parse.Letter) or t.ch!=c:
                logger.debug('  -- "%s%s" is not a dimension; bail',
                        result, t.ch)
                tokens.push(result)
                return None

            result += t.ch

        logger.debug('  -- the dimension is "%s"', result)
        return result

    @classmethod
    def from_tokens(cls, tokens,
            is_horizontal = True,
            ):
        r"""
        Constructs a Rule from tokens.

        See p219 of the TeXbook for the syntax rules. For example,
            \vrule width5pt height5pt width2pt

        Args:
            tokens: the token source
            is_horizontal: True if this is a horizontal rule, and
                False if it's a vertical rule. This decides default
                values for the result.

        Result:
            the new Rule.
        """
        if is_horizontal:
            logger.debug("Rule.from_tokens: constructing new hrule.")
            dimensions = {
                    'width': 'inherit',
                    'height': yex.value.Dimen(0.4, 'pt'),
                    'depth': yex.value.Dimen(0),
                    }
        else:
            logger.debug("Rule.from_tokens: constructing new vrule.")
            dimensions = {
                'width': yex.value.Dimen(0.4, 'pt'),
                'height': 'inherit',
                'depth': 'inherit',
                }

        while True:
            tokens.eat_optional_spaces()

            dimension = cls._get_dimension(tokens)

            if dimension is None:
                break

            logger.debug("Rule.from_tokens: reading the dimension '%s'",
                    dimension)

            tokens.eat_optional_spaces()
            size = yex.value.Dimen.from_tokens(tokens)
            logger.debug("Rule.from_tokens:   -- %s is %s",
                    dimension, size)

            dimensions[dimension] = size

        logger.debug("Rule.from_tokens: new dimensions are: %s",
                dimensions)

        result = cls(
                width = dimensions['width'],
                height = dimensions['height'],
                depth = dimensions['depth'],
                )

        logger.debug("Rule.from_tokens:   -- new rule is: %s",
                result)

        return result
