r"""
Parameters.

"""
import os
import yex.value
import yex.mode
import yex.exception
import yex.font
from yex.control import C_Unexpandable
import datetime
import logging

logger = logging.getLogger('yex.general')

class C_Parameter(C_Unexpandable):
    r"""
    Parameters are a specialised form of control: they have a value, with a type.
    For example, \hsize holds the width of the current line.


    Like all controls, they can be called. This is equivalent
    to assigning them a value. For example,
    ```
        \hsize 3pt
    ```
    assigns the value 3pt to \hsize.

    Each document instantiates a singleton instance of each parameter class.

    You can learn more about parameters from pp269-271 of the TeXbook, and
    lines 275ff of plain.tex.

    Attributes:
        our_type (type): the class we represent, in the form we use
            to store it. If this is a tuple, we can contain multiple types;
            the first one listed will be used to initialise a new control.
        initial_value: the value this parameter has on startup
        do_not_initialise (bool): if True, _value will not be initialised.
            If False (the default), _value will be initialised with a new
            instance of our_type (or our_type[0] if our_type is a tuple).
    """
    our_type = None
    initial_value = 0
    is_outer = False
    do_not_initialise = False

    def __init__(self, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self._value = value
        elif self.do_not_initialise:
            pass
        elif isinstance(self.initial_value, self.our_type):
            self._value = self.initial_value
        elif isinstance(self.our_type, tuple):
            self._value = self.our_type[0](self.initial_value)
        else:
            self._value = self.our_type(self.initial_value)

    # The property setter/getter methods are implemented weirdly
    # to make sure inheritance works properly. Python has a baroque
    # structure for this.
    @property
    def value(self):
        return self._get_value()

    @value.setter
    def value(self, v):
        self._set_value(v)

    def _get_value(self):
        return self._value

    def _set_value(self, n):
        if not isinstance(n, self.our_type):
            raise yex.exception.YexError(
                    f'Expecting a {self.our_type.__name__}, '
                    f'but found {n} (which is a '
                    f'{n.__class__.__name__})'
                    )

        self._value = n

    def set_from(self, tokens):
        """
        Sets the value from a token stream.
        """
        tokens.eat_optional_equals()
        v = self.our_type.from_tokens(tokens)
        logger.debug("Setting %s=%s",
                self, v)
        self.value = v

    def get_the(self, tokens):
        r"""
        Finds a representation of this parameter's value, as used by
        the control \the.

        Returns:
            a string representing the value.
        """
        if isinstance(self.value, str):
            return self.value
        else:
            return repr(self.value)

    def __call__(self, tokens):
        self.set_from(tokens)

    def __repr__(self):
        try:
            return '['+repr(self._get_value())+']'
        except Exception as e:
            return '[broken '+self.__class__.__name__+': '+repr(e)+']'

    def __int__(self):
        return int(self._value)

    def __getstate__(self):
        result = {
                'control': self.name,
                }
        value = self._get_value()
        if value != self.initial_value:
            result['value'] = value

        return result

class C_NumberParameter(C_Parameter):
    r"""
    Number parameters.

    Parameter controls whose value is an integer. The numbers are stored
    as an `int` internally, but we set and get them as `yex.value.Number`s.
    """
    our_type = int

    def set_from(self, tokens):
        tokens.eat_optional_equals()
        number = yex.value.Number.from_tokens(tokens)
        self.value = number.value
        logger.debug("Setting %s=%s",
                self, self.value)

    def _set_value(self, n):
        self._value = int(n)

class Adjdemerits(C_NumberParameter)              : pass
class Badness(C_NumberParameter)                  :
    "How badly the most recent line of text was set."
class Binoppenalty(C_NumberParameter)             : pass
class Brokenpenalty(C_NumberParameter)            : pass
class Clubpenalty(C_NumberParameter)              : pass
class Deadcycles(C_NumberParameter)               : pass
class Defaulthyphenchar(C_NumberParameter)        : pass
class Defaultskewchar(C_NumberParameter)          : pass
class Delimiterfactor(C_NumberParameter)          : pass
class Displaywidowpenalty(C_NumberParameter)      : pass
class Doublehyphendemerits(C_NumberParameter)     : pass
class Endlinechar(C_NumberParameter)              : initial_value = 13
class Errorcontextlines(C_NumberParameter)        : pass
class Escapechar(C_NumberParameter)               : initial_value = 92
class Exhyphenpenalty(C_NumberParameter)          : pass
class Fam(C_NumberParameter)                      : pass
class Finalhyphendemerits(C_NumberParameter)      : pass
class Floatingpenalty(C_NumberParameter)          : pass
class Globaldefs(C_NumberParameter)               : pass
class Hangafter(C_NumberParameter)                : initial_value = 1
class Hbadness(C_NumberParameter)                 : pass
class Holdinginserts(C_NumberParameter)           : pass
class Hyphenpenalty(C_NumberParameter)            : pass
class Insertpenalties(C_NumberParameter)          : pass
class Interlinepenalty(C_NumberParameter)         : pass
class Language(C_NumberParameter)                 : pass
class Lastpenalty(C_NumberParameter)              : pass
class Lefthyphenmin(C_NumberParameter)            : pass
class Linepenalty(C_NumberParameter)              : pass
class Looseness(C_NumberParameter)                : pass
class Mag(C_NumberParameter)                      : initial_value = 1000
class Maxdeadcycles(C_NumberParameter)            : pass
class Newlinechar(C_NumberParameter)              : pass
class Outputpenalty(C_NumberParameter)            : pass
class Pausing(C_NumberParameter)                  : pass
class Postdisplaypenalty(C_NumberParameter)       : pass
class Predisplaypenalty(C_NumberParameter)        : pass
class Pretolerance(C_NumberParameter)             :
    "How loose lines can get before we try hyphenation."
    initial_value = 1000
class Prevgraf(C_NumberParameter)                 : pass
class Relpenalty(C_NumberParameter)               : pass
class Righthyphenmin(C_NumberParameter)           : pass
class Showboxbreadth(C_NumberParameter)           : pass
class Showboxdepth(C_NumberParameter)             : pass
class Spacefactor(C_NumberParameter)              : initial_value = 1000
class Tolerance(C_NumberParameter)                : initial_value = 10000
class Uchyph(C_NumberParameter)                   : pass
class Vbadness(C_NumberParameter)                 : pass
class Widowpenalty(C_NumberParameter)             : pass

class C_DimenParameter(C_Parameter):
    r"""
    Dimen parameters.

    Parameter controls whose value is a Dimen-- that is, a physical length.
    """
    our_type = yex.value.Dimen

class Boxmaxdepth(C_DimenParameter)               : pass
class Delimitershortfall(C_DimenParameter)        : pass
class Displayindent(C_DimenParameter)             : pass
class Displaywidth(C_DimenParameter)              : pass
class Emergencystretch(C_DimenParameter)          : pass
class Hangindent(C_DimenParameter)                : pass
class Hfuzz(C_DimenParameter)                     : pass
class Hoffset(C_DimenParameter)                   : pass
class Hsize(C_DimenParameter)                     :
    r"The width of the current line."
    initial_value = yex.value.Dimen(495, 'pt') # A4 with margins of 50pj
class Lastkern(C_DimenParameter)                  : pass
class Lineskiplimit(C_DimenParameter)             : pass
class Mathsurround(C_DimenParameter)              : pass
class Maxdepth(C_DimenParameter)                  : pass
class Nulldelimiterspace(C_DimenParameter)        : pass
class Overfullrule(C_DimenParameter)              : pass
class Pagedepth(C_DimenParameter)                 : pass
class Pagefilllstretch(C_DimenParameter)          : pass
class Pagefillstretch(C_DimenParameter)           : pass
class Pagefilstretch(C_DimenParameter)            : pass
class Pagegoal(C_DimenParameter)                  : pass
class Pageshrink(C_DimenParameter)                : pass
class Pagestretch(C_DimenParameter)               : pass
class Pagetotal(C_DimenParameter)                 : pass
class Parindent(C_DimenParameter)                 :
    r"The width of the indentation for new paragraphs."
    initial_value = yex.value.Dimen(20, 'pt')

class Predisplaysize(C_DimenParameter)            : pass
class Prevdepth(C_DimenParameter)                 :
    r"The depth of the most recent box, or -1000 for none."
    initial_value = yex.value.Dimen(-1000, 'pt')
class Scriptspace(C_DimenParameter)               : pass
class Splitmaxdepth(C_DimenParameter)             : pass
class Vfuzz(C_DimenParameter)                     : pass
class Voffset(C_DimenParameter)                   : pass
class Vsize(C_DimenParameter)                     : pass

class C_GlueParameter(C_Parameter):
    r"""
    Glue parameters.

    Parameter controls whose value is a Glue-- the distance between two
    items on a page, which can stretch or shrink.
    """
    our_type = yex.value.Glue

class Abovedisplayshortskip(C_GlueParameter)      : pass
class Abovedisplayskip(C_GlueParameter)           : pass
class Baselineskip(C_GlueParameter)               : pass
class Belowdisplayshortskip(C_GlueParameter)      : pass
class Belowdisplayskip(C_GlueParameter)           : pass
class Lastskip(C_GlueParameter)                   : pass
class Leftskip(C_GlueParameter)                   : pass
class Lineskip(C_GlueParameter)                   : pass
class Parfillskip(C_GlueParameter)                :
    r"""The amount of space to add at the end of a paragraph."""
    initial_value = yex.value.Glue(0,
            stretch=1, stretch_unit='fil')

class Parskip(C_GlueParameter)                    : pass
class Rightskip(C_GlueParameter)                  : pass
class Spaceskip(C_GlueParameter)                  : pass
class Splittopskip(C_GlueParameter)               : pass
class Tabskip(C_GlueParameter)                    : pass
class Topskip(C_GlueParameter)                    : pass
class Xspaceskip(C_GlueParameter)                 : pass

class C_MuglueParameter(C_GlueParameter):
    r"""
    Muglue parameters.

    Parameter controls whose value is a Muglue-- a special kind of glue
    used for setting maths.
    """
    our_type = yex.value.Muglue

class Medmuskip(C_MuglueParameter)                : pass
class Thickmuskip(C_MuglueParameter)              : pass
class Thinmuskip(C_MuglueParameter)               : pass

class C_TokenlistParameter(C_Parameter):
    r"""
    Tokenlist parameters.

    Parameter controls whose value is a Tokenlist-- a list of symbols.
    """
    our_type = yex.value.Tokenlist
    initial_value = []

    def _set_value(self, v):
        if isinstance(v, yex.value.Tokenlist):
            self._value = yex.value.Tokenlist.from_another(v)
        elif isinstance(v, (list, str)):
            self._value = yex.value.Tokenlist(v)
        else:
            raise yex.exception.YexError(
                    f'Expecting a Tokenlist, but found '
                    f'{v} (of type {type(v)})'
                    )

class Errhelp(C_TokenlistParameter)               : pass
class Everycr(C_TokenlistParameter)               : pass
class Everydisplay(C_TokenlistParameter)          : pass
class Everyhbox(C_TokenlistParameter)             : pass
class Everyjob(C_TokenlistParameter)              : pass
class Everymath(C_TokenlistParameter)             : pass
class Everypar(C_TokenlistParameter)              : pass
class Everyvbox(C_TokenlistParameter)             : pass
class Jobname(C_TokenlistParameter)               : pass

class Output(C_TokenlistParameter):
    r"""
    Runs every time we have enough text typeset to produce a new page.

    The text to handle will be in \box255. If you don't do something with
    this text, it will cause an error.

    The default value is

        \shipout\box255
    """

    def _get_value(self):
        if len(self._value)==0:
            # See foot of p251 in the TeXbook
            result = [
                    yex.parse.Control(r'shipout', None, None),
                    yex.parse.Control(r'box', None, None),
                    yex.parse.Other('2'),
                    yex.parse.Other('5'),
                    yex.parse.Other('5'),
                ]

            result = yex.value.Tokenlist(result)
            return result

        else:
            return self._value

class Inputlineno(C_NumberParameter):
    r"""
    The current line in the input file.

    You can't write to this:

        The moving finger writes, and having writ
        Moves on; nor all your piety nor wit
        Shall lure it back to cancel half a line,
        Nor all your tears wash out a word of it.
    """

    def __int__(self):
        return self._value

    def _set_value(self, n):
       raise ValueError(
                f"Can't set value of inputlineno")

    def update(self, n):
        """
        Sets the line number.

        This is used by `yex.parse.source.Source` to keep the line number
        correct. We're not doing this via the `value` property because
        it shouldn't be generally accessible in the way other parameters'
        values are.

        Args:
            n (`int`): The line number.
        """
        self._value = n
        logger.debug("%s: line number is now %s",
                self, n)

    def __str__(self):
        return str(self._value)

    def __getstate__(self):
        # don't attempt to return the value; that will only cause trouble
        # when someone tries to recreate the state later
        result = {
                'control': self.name,
                }

file_load_time = datetime.datetime.now()

class C_TimeParameter(C_NumberParameter):
    def __init__(self, **kwargs):
        value = self._extract_field(file_load_time)
        super().__init__(value, **kwargs)

    def _extract_field(value):
        raise NotImplementedError()

class Time(C_TimeParameter):
    def _extract_field(self, now):
        return now.hour*60 + now.minute

class Day(C_TimeParameter):
    def _extract_field(self, now):
        return now.day

class Month(C_TimeParameter):
    def _extract_field(self, now):
        return now.month

class Year(C_TimeParameter):
    def _extract_field(self, now):
        return now.year
