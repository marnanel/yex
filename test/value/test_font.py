import io
import pytest
from yex.document import Document
from yex.value import Number, Dimen, Glue
import yex.exception
from .. import *
import yex.put
import yex.box
import logging

logger = logging.getLogger('yex.general')

def test_hyphenchar_skewchar(yex_test_fs):

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

def test_fontdimen():
    for font in ['cmr10']:
        for i, expected in enumerate([
            # Values from p429 of the TeXbook; it rounds them to 2dp,
            # so we do as well
            0,
            3.33,
            1.67, # Knuth rounds down, so he gives 1.66
            1.11,
            4.31,
            10.00,
            1.11,
            ]):

            found = run_code(
                    fr'\font\wombat={font}\the\fontdimen{i+1}\wombat',
                    find='chars',
                    )

            assert found.endswith('pt')
            found = found[:-2]
            found = round(float(found), 2)

            assert found==expected, (
                    fr"font dimensions for \fontdimen{i+1}\{font}"
                    )

        assert run_code(
                fr'\font\wombat={font}\fontdimen5\wombat=12.0pt'
                fr'\the\fontdimen5\wombat',
                find='chars',
                )=='12.0pt'

        doc = yex.Document()
        run_code(
                fr'\font\wombat={font}',
                doc=doc,
                )
        _check_silly_fontdimens(doc, 'wombat')

def _check_silly_fontdimens(doc, fontname):
    for silly in [0, 8, 1000]:
        with pytest.raises(yex.exception.NoSuchFontdimenError):
            found = run_code(
                    fr'\the\fontdimen{silly}\{fontname}',
                    doc=doc,
                    )

        with pytest.raises(yex.exception.NoSuchFontdimenError):
            found = run_code(
                    fr'\fontdimen{silly}\{fontname}=12.0pt',
                    doc=doc,
                    )

def test_nullfont(yex_test_fs):
    for i in range(1, 8):
        found = run_code(
                fr'\the\fontdimen{i}\nullfont',
                find='chars',
                )

        assert found=='0.0pt', "all dimens of nullfont begin as zero"

        found = run_code((
            fr'\fontdimen{i}\nullfont={i*10}.0pt'
            fr'\the\fontdimen{i}\nullfont'
            ),
            find='chars',
            )

        assert found==fr"{i*10}.0pt", \
                "you can assign to dimens of nullfont"

    doc = yex.Document()
    _check_silly_fontdimens(doc, 'nullfont')
