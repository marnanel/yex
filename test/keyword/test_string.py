from test import *
import yex

def test_string_activechar():
    run_code(r"""\def\tstring#1{\string #1}\tstring{H}""")

def test_string_controlname():
    assert run_code(
            call=(
                r"\string\wombat"
                ),
            find='chars',
            )==r'\wombat'

    assert [(t.ch, t.category) for t in
            run_code(
            setup=(
                r"\catcode32=11"
                ),
            call=(
                r"\string\wombat spong"
                ),
            find='saw',
            )]==[
                    ('\\', 12), ('w', 12), ('o', 12), ('m', 12), ('b', 12), ('a', 12), ('t', 12),
                    (' ', 10), # see TeXbook p40
                    ('s', 12), ('p', 12), ('o' , 12), ('n', 12), ('g', 12),
                    ]
