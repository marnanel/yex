import io
import pytest
from yex.state import State
from yex.value import Number, Dimen, Glue
import yex.exception
from .. import *
import yex.put
import yex.box
import logging

general_logger = logging.getLogger('yex.general')

def test_hyphenchar_skewchar():

    for char, newvalue, expected in [
            ('hyphenchar', r'`\%', '4537'),
            ('skewchar', '42', '4542'), # -1 then 42
            ]:
        for font in [
            r'\wombat',
            r'\nullfont',
            ]:

            assert run_code((
                    fr'\font\wombat=cmr10'
                    fr'\the\hyphenchar{font}'
                    fr'\hyphenchar{font}={newvalue}'
                    fr'\the\hyphenchar{font}'),
                    find='chars',
                    )==expected

def test_badness():
    assert get_number(r'\badness q')==0

@pytest.mark.xfail
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

            found = run_code(
                    r'\font\wombat='+font+ \
                    r'\the\fontdimen'+str(i+1)+r'\wombat',
                    find='chars',
                    )

            assert found==expected, (
                    f"font dimensions for "
                    fr"\fontdimen{i+1}\{font}"
                    )

        assert run_code(
                r'\font\wombat='+font+ \
                r'\fontdimen5\wombat=12pt'
                r'\the\fontdimen5\wombat',
                find='chars',
                )=='12pt'

def test_nullfont():
    for i in range(10):
            found = run_code(
                    r'\the\fontdimen'+str(i+1)+r'\nullfont',
                    find='chars',
                    )

            assert found=='0pt', "all dimens of nullfont begin as zero"

            found = run_code((
                r'\fontdimen'+str(i+1)+r'\nullfont '
                '= '+str((i+1)*10) + 'pt'
                r'\the\fontdimen'+str(i+1)+r'\nullfont'
                ),
                find='chars',
                )

            assert found==str((i+1)*10)+'pt', \
                    "you can assign to dimens of nullfont"
