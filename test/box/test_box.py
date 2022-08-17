from test import *
import yex

def test_box_from_tokens():
    def run(s,
            expected_class,
            expected_contents,
            ):
        doc = yex.Document()
        t = yex.parse.Tokeniser(
                doc=doc,
                source=s)
        e = yex.parse.Expander(t)

        box = yex.box.Box.from_tokens(e)

        assert isinstance(box, expected_class), s
        assert box_contents_to_string(box)==expected_contents, s

    run(r'\hbox{123}',
            expected_class = yex.box.HBox,
            expected_contents = '^ 123',
            )

    run(r'\vbox{abc}',
            expected_class = yex.box.VBox,
            expected_contents = '[[] abc [penalty: 10000] _]',
            )
