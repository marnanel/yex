from test import *
import yex
import pytest

@pytest.mark.xfail()
def test_tracingparagraphs_p98(capsys):

    def split(s):
        # This only exists to make comparisons easier if the test fails
        return s.rstrip().split('\n')

    doc = yex.Document()

    run_code(
            call=EXAMPLE_DOCUMENT,
            doc=doc,
            mode='vertical',
            )

    doc.save()

    assert split(capsys.readouterr().out)==split(EXPECTED_TRACE)

EXAMPLE_DOCUMENT = r"""
\hsize=2.5in
\tolerance=1000
\tracingparagraphs=1
\tracingoutput=1
\def\-{\discretionary{-}{}{}}
\def~{\penalty 10000 \ }
Mr.~Drofnats---or ``R. J.,'' as
he pre\-ferred to be called---
was hap\-pi\-est when he was at work
type\-set\-ting beau\-ti\-ful doc\-u\-ments.
"""

EXPECTED_TRACE = r"""[]\tenrm Mr. Drofnats---or ``R. J.,'' as he pre-
@\discretionary via @@0 b=0 p=50 d=2600
@@1: line 1.2- t=2600 -> @@0
ferred to be called---was hap-pi-est when
@ via @@1 b=131 p=0 d=29881
@@2: line 2.0 t=32481 -> @@1
he
@ via @@1 b=25 p=0 d=1225
@@3: line 2.3 t=3825 -> @@1
was at work type-set-ting beau-ti-ful doc-
@\discretionary via @@2 b=1 p=50 d=12621
@\discretionary via @@3 b=291 p=50 d=103101
@@4: line 3.2- t=45102 -> @@2
u-
@\discretionary via @@3 b=44 p=50 d=15416
@@5: line 3.1- t=19241 -> @@3
ments.
@\par via @@4 b=0 p=-10000 d=5100
@\par via @@5 b=0 p=-10000 d=5100
@@6: line 4.2- t=24341 -> @@5"""
