import io
import pytest
from mex.state import State
from mex.parse import Token, Tokeniser, Expander
from mex.value import Number, Dimen, Glue
import mex.exception
from .. import *
import mex.put
import mex.box
import logging

general_logger = logging.getLogger('mex.general')

def test_hyphenchar_skewchar():

    for char, newvalue, expected in [
            ('hyphenchar', r'`\%', '4537'),
            ('skewchar', '42', '4542'), # -1 then 42
            ]:
        for font in [
            r'\wombat',
            r'\nullfont',
            ]:

            assert _test_expand(
                    fr'\font\wombat=cmr10'
                    fr'\the\hyphenchar{font}'
                    fr'\hyphenchar{font}={newvalue}'
                    fr'\the\hyphenchar{font}',
                    )==expected

def test_badness():
    assert _get_number(r'\badness q')==0

def test_fontdimen():
    for font in ['cmr10']:
        for i, expected in enumerate([
            # Values from p429 of the TeXbook
            '0pt',
            '3.3333pt',
            '1.6667pt',
            '1.1111pt',
            '4.3056pt',
            '10pt',
            '1.1111pt',
            ]):

            found =_test_expand(
                    r'\font\wombat='+font+ \
                    r'\the\fontdimen'+str(i+1)+r'\wombat'
                    )

            assert found==expected, f"font dimensions for \\fontdimen{i+1}\\{font}"

        assert _test_expand(
                r'\font\wombat='+font+ \
                r'\fontdimen5\wombat=12pt'
                r'\the\fontdimen5\wombat'
                )=='12pt'

def test_nullfont():
    for i in range(10):
            found =_test_expand(
                    r'\the\fontdimen'+str(i+1)+r'\nullfont'
                    )

            assert found=='0pt', "all dimens of nullfont begin as zero"

            found =_test_expand(
                    r'\fontdimen'+str(i+1)+r'\nullfont = '+ \
                            str((i+1)*10) + 'pt' \
                            r'\the\fontdimen'+str(i+1)+r'\nullfont'
                    )

            assert found==str((i+1)*10)+'pt', \
                    "you can assign to dimens of nullfont"
