from test import *
import yex

def test_box_from_tokens():
    def run(s,
            expected_class,
            expected_contents,
            ):
        doc = yex.Document()
        e = yex.parse.Expander(s, doc=doc)

        box = yex.box.Box.from_tokens(e)

        assert isinstance(box, expected_class), s
        assert box_contents_to_string(box)==expected_contents, s

    run(r'\hbox{123}',
            expected_class = yex.box.HBox,
            expected_contents = '^ 123',
            )

    run(r'\vbox{abc}',
            expected_class = yex.box.VBox,
            expected_contents = '[[] abc [penalty: 10000] _ _]',
            )

def test_box_mode_list_passed_up():
    """
    The contents of a box can either be passed up to the outside mode
    or pushed onto the stack, but not both.
    """

    doc = yex.Document()

    assert doc['_mode'].is_vertical
    assert len(doc['_mode'].list)==0

    doc.read("""J

    """)

    assert doc['_mode'].is_vertical
    assert len(doc['_mode'].list)==1
    assert isinstance(doc['_mode'].list[0], yex.box.HBox)
    assert box_contents_to_string(doc['_mode'].list[0])==(
            '[] J [penalty: 10000] _ _'
            )

    ##############

    doc = yex.Document()

    assert doc['_mode'].is_vertical
    assert len(doc['_mode'].list)==0

    e = doc.open(r'\hbox{J}')
    found = e.next(level='executing', on_eof='raise')

    assert isinstance(found, yex.box.HBox)
    assert box_contents_to_string(found)==(
            '^ J'
            )

    assert e.next(level='executing', on_eof='none').ch == ' '
    assert e.next(level='executing', on_eof='none') is None

    assert doc['_mode'].is_vertical
    assert len(doc['_mode'].list)==0
