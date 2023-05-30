import logging
import yex
from yex.value import *
from yex.control.control import Expandable, Unexpandable

logger = logging.getLogger('yex.general')

class Register(Unexpandable):
    """
    A wrapper so we can pass out references to
    entries in a Array, and have them update
    the original values.
    """

    is_outer = False
    is_queryable = True

    def __init__(self, parent, index):
        self.parent = parent
        self.index = parent._check_index(index)

    @property
    def value(self):
        return self.parent.get_directly(self.index)

    @value.setter
    def value(self, n):
        self.parent[self.index] = n

    def __repr__(self):
        return (
                f"[{self.identifier}"
                f"=={self.parent._value_for_repr(self.index)}]"
                )

    @property
    def identifier(self):
        return fr"\{self.parent.name}{self.index}"

    def set_from_tokens(self, tokens):
        """
        Sets the value from the tokeniser "tokens".
        """

        try:
            previous = self.value
        except KeyError:
            previous = None

        self.parent.doc.remember_restore(self.identifier, previous)

        tokens.eat_optional_char('=')

        self.parent.set_from_tokens(
                index = self.index,
                tokens = tokens,
                )

    def __call__(self, tokens):
        r"""
        Equivalent to set_from_tokens(), if self.parent.set_on_call is
        True; returns self.value if self.parent.set_on_call is False.

        Note that because the definition of self.value, this may have the
        side-effect of clearing the register if the array is Box.
        """
        if self.parent.set_on_call:
            self.set_from_tokens(tokens)
        else:
            return self.value

    def get_the(self, tokens):
        r"""
        Returns the list of tokens to use when we're representing
        this register with \the (see p212ff of the TeXbook).

        It is acceptable to return a string; it will be
        converted to a list of the appropriate character tokens.
        """
        return str(self.value)

    def get_type(self):
        return self.parent.our_type

    def __iadd__(self, other):
        self.value += other
        return self

    def __imul__(self, other):
        self.value *= other
        return self

    def __itruediv__(self, other):
        self.value /= other
        return self

    def __int__(self):
        # this may not work in all cases, but that's for the
        # parent object to figure out.
        return int(self.value)

    def __eq__(self, other):
        if isinstance(other, Register):
            if self.parent!=other.parent:
                raise IncomparableError(
                        left = f"{self.parent.__class__.__name__} Register",
                        right = f"{other.parent.__class__.__name__} Register,"
                        )
            return self.value==other.value
        elif isinstance(other, self.parent.our_type):
            return self.value==other
        else:
            try:
                return type(other)(self.value)==other
            except TypeError:
                raise IncomparableError(
                        left = f"{self.parent.__class__.__name__} Register",
                        right = {other.__class__.__name__},
                        )

    def __getstate__(self):
        return {
                'register': f'\\{self.parent.name}{self.index}',
                }

    @property
    def name(self):
        return f'{self.parent.name}{self.index}'

class Array(Unexpandable):
    r"""
    A set of registers of a particular type.

    For example, the Dimen parameters live in registers called \dimen0,
    \dimen1, and so on. All those registers are held in a subclass of
    Array.

    The Register class is a wrapper which accesses one particular item
    in our array.

    This is an abstract class.

    Fields:
        our_type -    the type of the array, such as Dimen
        set-on-call - if True, code which calls members of this array
                      directly will set the value; if False, calling
                      these members will return the value, as if the call
                      had been preceded by \the. Defaults to True.
    """

    is_array = True
    our_type = None
    set_on_call = True

    def __init__(self, doc, contents=None):

        self.doc = doc

        if contents is None:
            self.contents = self._default_contents()
        else:
            self.contents = contents

    def get_directly(self, index):
        index = self._check_index(index)

        try:
            return self.contents[index]
        except (KeyError, TypeError):
            return self._empty_register()

    def _value_for_repr(self, index):
        try:
            return str(self.contents[index])
        except (KeyError, TypeError):
            return str(self._empty_register()) + " (empty)"

    def __getitem__(self, index):
        return self.get_element(index=index)

    def get_element(self, index):
        try:
            index = self._check_index(index)
        except (KeyError, TypeError):
            return self._empty_register()

        return Register(
            parent = self,
            index = index,
            )

    def get_element_from_tokens(self, tokens):
        index = Value.get_value_from_tokens(tokens)

        return self.get_element(index=index)

    def __setitem__(self, index, value):
        """
        Set the value of an element of this array.

        If you're setting the value directly, rather than going through
        doc[...], you should also call self.doc.remember_restore().

        Args:
            index (int): the index into this array; will be checked
            value (our_type): the value to give this element.
                If this is None, the element will be deleted.

        Returns:
            None
        """
        index = self._check_index(index)
        value = self._check_value(value)

        if value is None:
            if index in self.contents:
                del self.contents[index]
        else:
            self.contents[index] = value

    def set_from_tokens(self, index, tokens):

        logger.debug("%s: set_from_tokens begins.",
                self)
        index = self._check_index(index)

        logger.debug("%s: set_from_tokens index==%s",
                self, index)

        v = self._get_a_value(tokens)

        logger.debug("%s: set_from_tokens value==%s",
                self, v)

        self.__setitem__(index, v)
        logger.debug("%s: done!",
                self)

    def _get_a_value(self, tokens):
        if self.our_type==int:
            return Number.from_tokens(tokens).value
        else:
            return self.our_type.from_tokens(tokens)

    @classmethod
    def _check_index(cls, index):
        if index<0 or index>255:
            raise KeyError(index)
        return index

    def _check_value(self, value):
        if value is None:
            return None
        elif isinstance(value, self.our_type):
            return value
        elif hasattr(value, 'value'):
            return value.value
        else:
            try:
                return self.our_type.from_serial(value)
            except ValueError as ve:
                logger.debug((
                    "%s: tried to set a member to %s, "
                    "but %s.from_serial raised %s"),
                    self, value, self.our_type, ve)

                raise yex.exception.ExpectedButFoundError(
                        expected = self.our_type.__name__,
                        found = value,
                        )

    def _empty_register(self):
        return self.our_type()

    def __contains__(self, index):
        index = self._check_index(index)
        return index in self.contents

    @classmethod
    def _default_contents(cls):
        return {}

    @property
    def _type_to_parse(self):
        return self.our_type

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def items(self):
        """
        All the items in this table. This can be used to recreate the table.

        Yields:
            a series of pairs. The first element is a string which could
                be passed to Document[...] to recreate this item.
                The second element is the value.
        """

        default = self._default_contents()

        # This design is necessary because "default" could
        # be dict or defaultdict, and the "in" test doesn't work well
        # with the latter.
        def different_from_default(f, v):
            try:
                return default[f]!=v
            except (KeyError, TypeError):
                return True

        def transform_index(idx):
            # Some subclasses use characters as indexes, which we must
            # represent by their codepoints.

            if isinstance(idx, str):
                return ord(idx)
            else:
                return idx

        for f,v in self.contents.items():
            if different_from_default(f, v):
                yield (
                        fr"\{self.name}{transform_index(f)}",
                        v,
                        )

    def keys(self):
        for k,v in self.items():
            yield k

    def values(self):
        for k,v in self.items():
            yield v

    def __contains__(self, value):
        # there may be a more efficient way!
        return value in self.values()

    def __call__(self, tokens):
        logger.warning(
                f'{self.name} array called directly. '
                'This should never happen; the "is_array" flag should have '
                'made the Expander dereference this object and get a '
                'Register object instead.')
        if not self.is_array:
            logger.warning(
                    "  -- further, is_array is not set on this array!")
        raise NotImplementedError()

class Defined_by_chardef(Unexpandable):

    is_queryable = True

    def __init__(self, char, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.char = char

    def __call__(self, tokens):
        tokens.push(
                yex.parse.Token.get(
                    ch = self.char,
                ),
                is_result = True,
                )

    def __str__(self):
        return "[chardef: %d]" % (ord(self.char),)

    def __repr__(self):
        return str(self)

    def __int__(self):
        return ord(self.char)

    @property
    def value(self):
        return self.char

    def __getstate__(self):

        result = {
                'char': ord(self.char),
                }

        # There is no need to return the modes:
        # they're derivable from the name of the control.

        return result

    def __eq__(self, other):
        try:
            other = other.value
        except:
            pass

        return self.value==other

class Registerdef(Expandable):

    def __call__(self, tokens):

        logger.debug(r"%s: off we go, redefining a symbol...",
                self,
                )

        newname = tokens.next(
                level='deep',
                )

        logger.debug(r"%s: the name will be %s",
                self,
                newname,
                )

        if newname.category != newname.CONTROL:
            raise yex.exception.ExpectedButFoundError(
                    expected = yex.parse.Control.__name__,
                    found = newname,
                    )

        tokens.eat_optional_char('=')

        index = yex.value.Number.from_tokens(tokens).value

        logger.debug(r"%s: the index of %s will be %s",
                self,
                newname,
                index,
                )

        existing = tokens.doc.get(self.block).get_element(index)

        logger.debug(r"%s: so we set %s to %s",
                self,
                newname.identifier,
                existing,
                )

        tokens.doc[newname.identifier] = existing


