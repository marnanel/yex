import pytest
from test import *
import yex

def test_begingroup():
    doc = yex.Document()
    run_code(
            doc=doc,
            call=r'\count10=1{\count10=2\begingroup\count10=3{\count10=4',
            auto_save = False,
            )
    assert doc[r'\count10']==4

    with pytest.raises(yex.exception.WrongKindOfGroupError):
        run_code(
                doc=doc,
                call=r'\endgroup',
                auto_save = False,
                )
    assert doc[r'\count10']==4

    run_code(
            doc=doc,
            call=r'}',
            auto_save = False,
            )
    assert doc[r'\count10']==3

    with pytest.raises(yex.exception.WrongKindOfGroupError):
        run_code(
                doc=doc,
                call=r'}',
                auto_save = False,
                )
    assert doc[r'\count10']==3

    run_code(
            doc=doc,
            call=r'\endgroup',
            auto_save = False,
            )
    assert doc[r'\count10']==2

    with pytest.raises(yex.exception.WrongKindOfGroupError):
        run_code(
                doc=doc,
                call=r'\endgroup',
                auto_save = False,
                )
    assert doc[r'\count10']==2

    run_code(
            doc=doc,
            call=r'}',
            auto_save = False,
            )

    assert doc[r'\count10']==1
