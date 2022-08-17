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
    def _get_letters(cls, tokens):
        # XXX This would be better as a tokeniser method
        result = ''
        while True:
            t = tokens.next(
                    on_eof = 'none',
                    )

            if not isinstance(t, yex.parse.Letter):
                tokens.push(t)
                return result

            result += t.ch

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

            candidate = cls._get_letters(tokens)

            if candidate=='':
                break

            logger.debug("Rule.from_tokens: reading the dimension '%s'",
                    candidate)

            if candidate not in dimensions:
                logger.debug("Rule.from_tokens:   -- that was not a dimension")
                tokens.push(candidate)
                break

            tokens.eat_optional_spaces()
            size = yex.value.Dimen.from_tokens(tokens)
            logger.debug("Rule.from_tokens:   -- %s is %s",
                    candidate, size)

            dimensions[candidate] = size

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
