import logging
from mex.control.word import C_ControlWord
import mex.parse
import mex.exception
import mex.value

commands_logger = logging.getLogger('mex.commands')

class C_Box(C_ControlWord):

    our_type = mex.box.Box
    inside_mode = None

    def __call__(self, name, tokens):
        tokens.push(
                self._construct_box(
                    name,
                    tokens,
                    )
                )

    def _construct_box(self, name, tokens):
        """
        Constructs a box.

        We expect the next token to begin a group.

        Returns a list. The new box is the last item in the list.
        Before it, there are any control words which we found
        during parsing, in the order they were found.

        You should push all this to the tokeniser, after you've
        messed around with it as you need.
        """

        for token in tokens:
            if token.category == token.BEGINNING_GROUP:
                # good
                tokens.push(token)
                break

            raise mex.exception.MexError(
                    f"{name} must be followed by a group")

        newbox = self.our_type()

        tokens.state.begin_group()

        if self.inside_mode is not None:
            tokens.state['_mode'] = self.inside_mode

        e = mex.parse.Expander(
                tokens,
                single = True,
                )

        pushback = []

        commands_logger.debug("%s: beginning creation of %s",
                self, newbox)

        for t in e:

            if isinstance(t, mex.parse.Token):

                if t.category in (t.LETTER, t.OTHER):
                    font = tokens.state['_currentfont'].value
                    addendum = mex.box.CharBox(font=font, ch=t.ch)
                elif t.category in (t.SPACE,):
                    addendum = mex.value.Glue() # TODO
                else:
                    addendum = t
            else:
                addendum = t

            if isinstance(addendum, (
                mex.gismo.Gismo,
                # TODO: Glue should really be a subclass of Gismo anyway
                mex.value.Glue,
                )):
                commands_logger.debug("append %s -> %s",
                        t, self)

                newbox.append(addendum)
            else:
                raise mex.exception.MexError(
                        f"{addendum} is of type {type(addendum)}, "
                        f"which can't appear in a {name}")

        tokens.state.end_group()

        commands_logger.debug("%s: creation done: %s",
                self, newbox)
        commands_logger.debug("%s:   -- with pushback: %s",
                self, pushback)

        pushback.append(newbox)

        return pushback

class Hbox(C_Box):
    our_type = mex.box.HBox
    inside_mode = 'restricted_horizontal'

class Vbox(C_Box):
    our_type = mex.box.VBox
    inside_mode = 'internal_vertical'

class Raise(C_Box):
    our_type = mex.box.Shifted
    direction = (0, -1)

    def __call__(self, name, tokens):

        # TODO there are supposed to be restrictions on the mode

        distance = mex.value.Dimen(tokens)

        commands_logger.debug(
                "%s: will shift by %s in %s: finding contents of new box",
                name,
                distance,
                self.direction,
                )

        for t in mex.parse.Expander(
                tokens,
                single=True,
                ):
            newbox = t

        if not isinstance(newbox, mex.box.Box):
            raise mex.exception.ParseError(
                    fr"{name}: received {newbox}, which is a {type(newbox)},"
                    "but we needed a Box"
                    )

        wrapped = mex.box.Shifted(
            dx = distance*self.direction[0],
            dy = distance*self.direction[1],
            contents = [newbox],
            )

        commands_logger.debug(
                "%s: new box is %s",
                name,
                wrapped,
                )

        tokens.push(wrapped)

class Lower(Raise):
    direction = (0, 1)

class Moveleft(Raise):
    direction = (-1, 0)

class Moveright(Raise):
    direction = (1, 0)

class C_BoxDimensions(C_ControlWord):

    dimension = None

    def _get_box(self, name, tokens):
        which = mex.value.Number(tokens).value
        commands_logger.debug("%s: find box number %s",
                name, which)

        result = tokens.state.registers['box']. \
                get_directly(which, no_destroy = True)
        commands_logger.debug("%s:   -- it's %s",
                name, result)

        return result

    def get_the(self, name, tokens):
        box = self._get_box(name, tokens)

        dimension = self.dimension
        commands_logger.debug("%s:  -- looking up its %s",
                name, dimension)

        result = getattr(box, dimension)

        commands_logger.debug("%s:    -- %s",
                name, result)

        return str(result)

    def __call__(self, name, tokens):
        raise mex.exception.MexError(
                f"you cannot set the {self.dimension} of a box directly"
                )

class Wd(C_BoxDimensions):
    dimension = 'width'

class Ht(C_BoxDimensions):
    dimension = 'height'

class Dp(C_BoxDimensions):
    dimension = 'depth'

class Setbox(C_ControlWord):
    def __call__(self, name, tokens):
        index = mex.value.Number(tokens)
        tokens.eat_optional_equals()

        e = mex.parse.Expander(
                tokens,
                )
        for rvalue in e:
            break

        if not isinstance(rvalue, mex.box.Box):
            raise mex.exception.MexError(
                    "this was not a box"
                    )

        tokens.state[f'box{index}'] = rvalue

class Showbox(C_ControlWord):
    def __call__(self, name, tokens):
        index = mex.value.Number(tokens)

        box = tokens.state[f'copy{index}'].value

        result = box.showbox()

        print('\n'.join(result))
