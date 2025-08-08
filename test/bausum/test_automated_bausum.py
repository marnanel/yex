from test import *
from . import *
import yex

class MonthTest(BausumTest):
    SOURCE = r"""

    \def\mydate
    {%
         \number\day \ %
         \ifcase\month
              \or Jan\or Feb\or Mar%
              \or Apr\or May\or June%
              \or July\or Aug\or Sep%
              \or Oct\or Nov\or Dec%
         \fi
         \ \number\year
    }
    \mydate
    """

    EXPECTED = r"""
    19 July 2025
     """
