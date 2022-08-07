import logging
import yex
import pytest
from test import *
from test.box.test_hvbox import box_getstate

logger = logging.getLogger('yex.general')

def test_wordbox_getstate():
    box_getstate(
            code = r'\hbox{Gilbert Keith}',
            setup = r'',
            expected = {
                'font': 'cmr10',
                'hbox': [
                    {'breakpoint': []},
                    'Gilb',
                    {'kern': -18219},
                    'ert',
                    {'breakpoint': []},
                    [218431, 109248, 0, 72810, 0],
                    'Keith',
                    ],
                },
            )

def test_wordbox_append_illegal_args():
    font = yex.font.Font.from_name(None)
    wb = yex.box.WordBox(font=font)

    with pytest.raises(TypeError):
        wb.append(123)

    with pytest.raises(TypeError):
        wb.append(None)

    with pytest.raises(TypeError):
        wb.append('Hello world')

    with pytest.raises(TypeError):
        wb.append('')

def test_wordbox_width():
    font = yex.font.Font.from_name(None)

    def total_lengths_of_chars(s):
        widths = max_height = max_depth = 0
        for c in s:
            metrics = font[c].metrics
            widths += metrics.width
            max_height = max(metrics.height, max_height)
            max_depth = max(metrics.depth, max_depth)
        return widths, max_height, max_depth

    # "expected" is the expected difference between the width of the word
    # and the total of the widths of all its characters.
    # The differences are caused by kerns and ligatures.
    for word, expected in [
            ('X',           0),
            ('XX',          0),
            ('I',           0),
            ('II',     -0.278), # there is a kern
            ('o',           0),
            ('of',          0),
            ('off',    -3.056), # "ff" ligature
            ('offi',   -5.834), # "ffi" ligature
            ('offic',  -5.834),
            ('office', -5.834),
            ]:
        wb = yex.box.WordBox(font=font)
        assert wb.width==0

        for c in word:
            wb.append(c)

        w, h, d = total_lengths_of_chars(word)

        # Height and depth aren't affected by kerns and ligatures
        assert wb.height == h, word
        assert wb.depth == d, word

        # But width is!
        difference = wb.width - w
        assert difference == yex.value.Dimen(expected), word

def test_wordbox_ligature_creation():

    # Also tests whether WordBoxes are created correctly.

    doc = yex.Document()

    run_code(r'\chardef\eff=102',
            mode = None,
            doc=doc,
            )

    for string, expected in [

            # all letters, but one ligature ("ff")
            # which becomes \x0b in the font cmr10
            (r'off',         'o\x0b'),

            # two non-letter characters and some letters;
            # "``" becomes an open quote, which is '\' in cmr10
            (r'``ABC',       r'\ABC'),

            # "off" again, except that the middle "f" is specified
            # using \char, which should make no difference
            (r'o\char102 f', 'o\x0b'),

            # "off" again, except that the middle "f" is specified
            # using \chardef
            (r'o\eff f', 'o\x0b'),

            # Also, let's test the em dash.
            (r'a---b', 'a|b'),
            ]:
        received = run_code(
                string,
                mode = None,
                doc=doc,
                find='list')
        doc.save()

        received = [x for x in received if isinstance(x, yex.box.VBox)]
        received = received[0]

        logger.info("Received: %s", received)
        logger.info("Received: %s", received.showbox())

        found = ''.join([x.split(' ')[1] for x in received.showbox()
            if 'cmr10' in x])

        assert expected==found, received.showbox()

def test_wordbox_remembers_ligature():
    doc = yex.Document()
    received = run_code(r'a---b``c',
            mode = None,
            doc=doc,
            find='list')
    doc.save()

    received = [x for x in received if isinstance(x, yex.box.VBox)]
    received = received[0]

    found = [x.split(' ', maxsplit=1)[1] for x in received.showbox()
            if 'cmr10' in x]

    assert found==['a', '| (ligature ---)', 'b', r'\ (ligature ``)', 'c']
