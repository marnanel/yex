import mex.value
import mex.filename
import logging

commands_logger = logging.getLogger('mex.commands')

class Font:

    DIMEN_SLANT_PER_PT = 1
    DIMEN_INTERWORD_SPACE = 2
    DIMEN_INTERWORD_STRETCH = 3
    DIMEN_INTERWORD_SHRINK = 4
    DIMEN_X_HEIGHT = 5
    DIMEN_QUAD_WIDTH = 6
    DIMEN_EXTRA_SPACE = 7

    # σ-params
    DIMEN_QUAD = 6
    DIMEN_NUM1 = 8
    DIMEN_NUM2 = 9
    DIMEN_NUM3 = 10
    DIMEN_DENOM1 = 11
    DIMEN_DENOM2 = 12
    DIMEN_SUP1 = 13
    DIMEN_SUP2 = 14
    DIMEN_SUP3 = 15
    DIMEN_SUB1 = 16
    DIMEN_SUB2 = 17
    DIMEN_SUP_DROP = 18
    DIMEN_SUB_DROP = 19
    DIMEN_DELIM1 = 20
    DIMEN_DELIM2 = 21
    DIMEN_AXIS_HEIGHT = 22

    # ξ-params
    DIMEN_DEFAULT_RULE_THICKNESS = 8
    DIMEN_BIG_OP_SPACING1 = 9
    DIMEN_BIG_OP_SPACING2 = 10
    DIMEN_BIG_OP_SPACING3 = 11
    DIMEN_BIG_OP_SPACING4 = 12
    DIMEN_BIG_OP_SPACING5 = 13

    def __init__(self,
            tokens = None,
            filename = None,
            scale = None,
            name = None,
            state = None,
            ):

        if state is not None:
            self.hyphenchar = state['defaulthyphenchar']
            self.skewchar = state['defaultskewchar']
        else:
            self.hyphenchar = ord('-')
            self.skewchar = -1

        self._metrics = None
        self.has_been_used = False

    def __getitem__(self, n):

        if not isinstance(n, int):
            raise TypeError()
        if n<=0:
            raise ValueError()

        if n in self.metrics.dimens:
            result = mex.value.Dimen(self.metrics.dimens[n])
        else:
            result = mex.value.Dimen()

        commands_logger.debug(
                r"%s: lookup dimen %s, == %s",
                self, n, result)

        return result

    def __setitem__(self, n, v):
        if not isinstance(n, int):
            raise TypeError()
        if n<=0:
            raise ValueError()
        if not isinstance(v, mex.value.Dimen):
            raise TypeError()

        if n not in self.metrics.dimens and self.has_been_used:
            raise mex.exception.MexError(
                    "You can only add new dimens to a font "
                    "before you use it.")

        commands_logger.debug(
                r"%s: set dimen %s, = %s",
                self, n, v)
        self.metrics.dimens[n] = v

    def _set_from_tokens(self, tokens):
        self.filename = mex.filename.Filename(
                name = tokens,
                filetype = 'font',
                )

        commands_logger.debug(r"font is: %s",
                self.filename.value)

        tokens.eat_optional_spaces()
        if tokens.optional_string("at"):
            tokens.eat_optional_spaces()
            self.scale = mex.value.Dimen(tokens)
            commands_logger.debug(r"  -- scale is: %s",
                    self.scale)
        elif tokens.optional_string("scaled"):
            tokens.eat_optional_spaces()
            self.scale = mex.value.Number(tokens)
            commands_logger.debug(r"  -- scale is: %s",
                    self.scale)
        else:
            self.scale = None
            commands_logger.debug(r"  -- scale is not specified")

    def __repr__(self):
        result = self.name
        if self.scale is not None:
            result += f' at {self.scale}pt'

        return result
