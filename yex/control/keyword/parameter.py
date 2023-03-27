r"""
Parameters.

"""
import os
import datetime
import logging
import yex
from yex.control import (
        NumberParameter, DimenParameter, 
        GlueParameter, MuglueParameter,
        TokenlistParameter, TimeParameter,
        )

logger = logging.getLogger('yex.general')

class Adjdemerits(NumberParameter)              : pass
class Badness(NumberParameter)                  :
    "How badly the most recent line of text was set."
class Binoppenalty(NumberParameter)             : pass
class Brokenpenalty(NumberParameter)            : pass
class Clubpenalty(NumberParameter)              : pass
class Deadcycles(NumberParameter)               : pass
class Defaulthyphenchar(NumberParameter)        : pass
class Defaultskewchar(NumberParameter)          : pass
class Delimiterfactor(NumberParameter)          : pass
class Displaywidowpenalty(NumberParameter)      : pass
class Doublehyphendemerits(NumberParameter)     : pass
class Endlinechar(NumberParameter)              : initial_value = 13

class Errorcontextlines(NumberParameter)        : pass
class Escapechar(NumberParameter)               :
    r"""
    The symbol we print before control names.

    If this is between 0 and 255, we print the character with that codepoint
    before the names of controls. For example, if the value was 163, and we
    were printing the name of a control called "fx", we would print "sfx".
    If it's below 0 or above 255, we don't print any symbol there.

    This is the symbol used when we produce the name of a character.
    For the symbols we accept when we read the name of a character,
    see the catcodes table. There is nothing requiring agreement between
    these values in either direction.

    The initial value is 92, which produces a backslash.
    """
    initial_value = 92

class Exhyphenpenalty(NumberParameter)          : pass
class Fam(NumberParameter)                      : pass
class Finalhyphendemerits(NumberParameter)      : pass
class Floatingpenalty(NumberParameter)          : pass
class Globaldefs(NumberParameter)               : pass
class Hangafter(NumberParameter)                : initial_value = 1
class Hbadness(NumberParameter)                 : pass
class Holdinginserts(NumberParameter)           : pass
class Hyphenpenalty(NumberParameter)            : pass
class Insertpenalties(NumberParameter)          : pass
class Interlinepenalty(NumberParameter)         : pass
class Language(NumberParameter)                 : pass
class Lastpenalty(NumberParameter)              : pass
class Lefthyphenmin(NumberParameter)            : pass
class Linepenalty(NumberParameter)              : pass
class Looseness(NumberParameter)                : pass
class Mag(NumberParameter)                      : initial_value = 1000
class Maxdeadcycles(NumberParameter)            : pass
class Newlinechar(NumberParameter)              : pass
class Outputpenalty(NumberParameter)            : pass
class Pausing(NumberParameter)                  : pass
class Postdisplaypenalty(NumberParameter)       : pass
class Predisplaypenalty(NumberParameter)        : pass
class Pretolerance(NumberParameter)             :
    "How loose lines can get before we try hyphenation."
    initial_value = 1000
class Prevgraf(NumberParameter)                 : pass
class Relpenalty(NumberParameter)               : pass
class Righthyphenmin(NumberParameter)           : pass
class Showboxbreadth(NumberParameter)           : pass
class Showboxdepth(NumberParameter)             : pass
class Spacefactor(NumberParameter)              : initial_value = 1000
class Tolerance(NumberParameter)                : initial_value = 10000
class Uchyph(NumberParameter)                   : pass
class Vbadness(NumberParameter)                 : pass
class Widowpenalty(NumberParameter)             : pass

class Boxmaxdepth(DimenParameter)               : pass
class Delimitershortfall(DimenParameter)        : pass
class Displayindent(DimenParameter)             : pass
class Displaywidth(DimenParameter)              : pass
class Emergencystretch(DimenParameter)          : pass
class Hangindent(DimenParameter)                : pass
class Hfuzz(DimenParameter)                     : pass
class Hoffset(DimenParameter)                   : pass
class Hsize(DimenParameter)                     :
    r"The width of the current line."
    initial_value = yex.value.Dimen(495, 'pt') # A4 with margins of 50pj
class Lastkern(DimenParameter)                  : pass
class Lineskiplimit(DimenParameter)             : pass
class Mathsurround(DimenParameter)              : pass
class Maxdepth(DimenParameter)                  : pass
class Nulldelimiterspace(DimenParameter)        : pass
class Overfullrule(DimenParameter)              : pass
class Pagedepth(DimenParameter)                 : pass
class Pagefilllstretch(DimenParameter)          : pass
class Pagefillstretch(DimenParameter)           : pass
class Pagefilstretch(DimenParameter)            : pass
class Pagegoal(DimenParameter)                  : pass
class Pageshrink(DimenParameter)                : pass
class Pagestretch(DimenParameter)               : pass
class Pagetotal(DimenParameter)                 : pass
class Parindent(DimenParameter)                 :
    r"The width of the indentation for new paragraphs."
    initial_value = yex.value.Dimen(20, 'pt')

class Predisplaysize(DimenParameter)            : pass
class Prevdepth(DimenParameter)                 :
    r"The depth of the most recent box, or -1000 for none."
    initial_value = yex.value.Dimen(-1000, 'pt')
class Scriptspace(DimenParameter)               : pass
class Splitmaxdepth(DimenParameter)             : pass
class Vfuzz(DimenParameter)                     : pass
class Voffset(DimenParameter)                   : pass
class Vsize(DimenParameter)                     :
    r"""
    The height of a page.

    We're using the height of A4 here. Plain TeX overrides this anyway.
    """
    initial_value = yex.value.Dimen(842, 'pt')

class Abovedisplayshortskip(GlueParameter)      : pass
class Abovedisplayskip(GlueParameter)           : pass
class Baselineskip(GlueParameter)               : pass
class Belowdisplayshortskip(GlueParameter)      : pass
class Belowdisplayskip(GlueParameter)           : pass
class Lastskip(GlueParameter)                   : pass
class Leftskip(GlueParameter)                   : pass
class Lineskip(GlueParameter)                   : pass
class Parfillskip(GlueParameter)                :
    r"""The amount of space to add at the end of a paragraph."""
    initial_value = yex.value.Glue(0,
            stretch=1, stretch_unit='fil')

class Parskip(GlueParameter)                    : pass
class Rightskip(GlueParameter)                  : pass
class Spaceskip(GlueParameter)                  : pass
class Splittopskip(GlueParameter)               : pass
class Tabskip(GlueParameter)                    : pass
class Topskip(GlueParameter)                    : pass
class Xspaceskip(GlueParameter)                 : pass

class Medmuskip(MuglueParameter)                : pass
class Thickmuskip(MuglueParameter)              : pass
class Thinmuskip(MuglueParameter)               : pass

class Errhelp(TokenlistParameter)               : pass
class Everycr(TokenlistParameter)               : pass
class Everydisplay(TokenlistParameter)          : pass
class Everyhbox(TokenlistParameter)             : pass
class Everyjob(TokenlistParameter)              : pass
class Everymath(TokenlistParameter)             : pass
class Everypar(TokenlistParameter)              : pass
class Everyvbox(TokenlistParameter)             : pass
class Jobname(TokenlistParameter)               : pass

class Output(TokenlistParameter):
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

class Inputlineno(NumberParameter):
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
        return result

class Time(TimeParameter):
    def _extract_field(self, now):
        return now.hour*60 + now.minute

class Day(TimeParameter):
    def _extract_field(self, now):
        return now.day

class Month(TimeParameter):
    def _extract_field(self, now):
        return now.month

class Year(TimeParameter):
    def _extract_field(self, now):
        return now.year
