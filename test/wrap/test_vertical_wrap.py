import yex
import pytest
from test import *
import logging

logger = logging.getLogger('yex.general')

EXPECTED = [
        '%% goal height=643.20255, max depth=4.0',

        # t = total height if we break here
        # g = goal height (always the same, unless footnotes etc are in use)
        # b = badness
        # p = penalty
        # c = cost, with a "#" if it's the best so far
        #
        # If they're infinite, we show b=* or c=*.

        '% t=10.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=22.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=34.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=46.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=58.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=70.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=82.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=94.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=106.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=118.0 plus 1.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=130.0 plus 1.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=142.0 plus 1.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=154.0 plus 1.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=166.0 plus 1.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=178.0 plus 1.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=190.0 plus 1.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=202.0 plus 1.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=214.0 plus 1.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=226.0 plus 2.0 g=643.20255 b=10000 p=250 c=100000#',
        '% t=238.0 plus 2.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=250.0 plus 2.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=262.0 plus 2.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=274.0 plus 2.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=286.0 plus 3.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=298.0 plus 3.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=310.0 plus 3.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=322.0 plus 3.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=334.0 plus 4.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=346.0 plus 4.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=358.0 plus 4.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=370.0 plus 4.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=382.0 plus 4.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=394.0 plus 4.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=406.0 plus 5.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=418.0 plus 5.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=430.0 plus 5.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=442.0 plus 5.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=454.0 plus 5.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=466.0 plus 5.0 g=643.20255 b=10000 p=150 c=100000#',
        '% t=478.0 plus 5.0 g=643.20255 b=10000 p=0 c=100000#',
        '% t=479.94444 plus 5.0 plus 1.0fill g=643.20255 b=0 p=0 c=0#',
        ('% t=479.94444 plus 5.0 plus 2.0fill g=643.20255 b=0 '
            'p=-1073741824 c=-1073741824'),
        ]

# Based on the first few paras of ch15 of the TeXbook
SOURCE = r"""
\tracingpages=1 \vsize=643.20255pt \maxdepth=4pt \font\tenrm=cmr10 \tenrm
\topskip=10pt
\def\TeX{T\kern-.2em\lower.5ex\hbox{E}\kern-.06em X}
\TeX\ attempts to choose desirable places to divide your document into
individual pages, and its technique for doing this usually works pretty

well. But the problem of {page make-up} is considerably more difficult
than the problem of line breaking that we considered in the previous chapter,
because pages often have much less flexibility than lines do. If the
vertical glue on a page has little or no ability to stretch or to shrink,
\TeX\ usually has no choice about where to start a new page; conversely, if
there is too much variability in the glue, the result will look bad because
different pages will be too irregular. Therefore if you are fussy about the
appearance of pages, you can expect to do some rewriting of the manuscript
until you achieve an appropriate balance, or you might need to fiddle
with the looseness as described in Chapter 14; no automated system will
be able to do this as well as you.

Mathematical papers that contain a lot of displayed equations have an
advantage in this regard, because the glue that surrounds a display tends to
be quite flexible. \TeX\ also gets valuable room to maneuver when you
have occasion to use smallskip or medskip or bigskip spacing
between certain paragraphs. For example, consider a page that contains
a dozen or so exercises, and suppose that there is 3pt of additional
space between exercises, where this space can stretch to 4pt or
shrink to 2pt. Then there is a chance to squeeze an extra line on the page,
or to open up the page by removing one line, in order to avoid splitting
an exercise between pages. Similarly, it is possible to use flexible
glue in special publications like membership rosters or company telephone
directories, so that individual entries need not be split between columns
or pages, yet every column appears to be the same height.

For ordinary purposes you will probably find that \TeX's automatic method
of page breaking is satisfactory. And when it occasionally gives
unpleasant results, you can force the machine to break at your favorite
place by typing `eject'. But be careful: eject will cause \TeX\ to
stretch the page out, if necessary, so that the top and bottom baselines
agree with those on other pages. If you want to eject a short page,
filling it with blank space at the bottom, type `vfilleject' instead.

If you say `eject' in the middle of a paragraph, the paragraph
will end first, as if you typed `pareject'. But Chapter 14 mentions
that you can say `vadjust{eject}' in mid-paragraph, if you want to
force a page break after whatever line contains your current position
when the full paragraph is eventually broken up into lines; the rest of the
paragraph will go on the following page.

To prevent a page break, you can say `nobreak' in vertical
mode, just as nobreak in horizontal mode prevents breaks between lines.
For example, it is wise to say nobreak between the title of a subsection
and the first line of text in that subsection. But nobreak does not
cancel the effect of other commands like eject that tell \TeX\ to
break; it only inhibits a break at glue that immediately follows. You
should become familiar with \TeX's rules for line breaks and page breaks
if you want to maintain fine control over everything. The remainder of
this chapter is devoted to the intimate details of page breaking.

\TeX\ breaks lists of lines into pages by computing badness ratings
and penalties, more or less as it does when breaking paragraphs into lines.
But pages are made up one at a time and removed from \TeX's memory; there is
no looking ahead to see how one page break will affect the next one.
In other words, \TeX\ uses a special method to find the optimum
breakpoints for the lines in an entire paragraph, but it doesn't attempt
to find the optimum breakpoints for the pages in an entire document. The
computer doesn't have enough high-speed memory capacity to remember the
contents of several pages, so \TeX\ simply chooses each page break as best
it can, by a process of ``local'' rather than ``global'' optimization.

\vfill
"""

class FakeLogControl(yex.control.keyword.TracingParameter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.received = []

    def info(self, s):
        if self._value>=1:
            logger.debug("Fake logger received: %s", s)
            self.received.append(s)
        else:
            logger.debug("Fake logger ignored: %s", s)

    @yex.control.keyword.TracingParameter.value.setter
    def value(self, n):
        if n>=1:
            logger.debug("Fake logger enabled.")
        else:
            logger.debug("Fake logger disabled.")

        self._value = n

@pytest.mark.xfail
def test_vertical_wrapping():

    doc = yex.Document()
    fl = FakeLogControl()

    doc.controls |= {
            r'\tracingpages': fl,
            }

    found = [line for line in run_code(SOURCE,
            doc=doc,
            mode='vertical',
            output='dummy',
            find='ch').split('\n')
            if line.startswith('%')]
    doc.save()

    assert fl.received==EXPECTED

def test_wrap_with_width_of_inherit():
    run_code(
            r"\vbox{\hbox{a}\hrule height-10sp\hbox{b}}",
            find='ch')
