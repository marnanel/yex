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
            expected = [{
                    'font': 'tenrm',
                    'hbox': [
                        {'breakpoint': []},
                        'Gilb',
                        {'kern': 18205},
                        'ert',
                        {'breakpoint': []},
                        [218453, 109226, 0, 72818, 0],
                        'Keith',
                        ],
                    }],
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
            ('X',       '0.0'),
            ('XX',      '0.0'),
            ('I',       '0.0'),
            ('II',      '0.27779'), # there is a kern
            ('o',       '0.0'),
            ('of',      '0.0'),
            ('off',    '-0.27779'), # "ff" ligature
            ('offi',   '-0.55557'), # "ffi" ligature
            ('offic',  '-0.55557'),
            ('office', '-0.55557'),
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
        assert yex.util.fraction_to_str(difference.value, 16) \
                == expected, word

def test_wordbox_ligature_creation():

    # Also tests whether WordBoxes are created correctly.

    for string, expected in [

            # all letters, but one ligature ("ff")
            # which becomes \x0b in the font tenrm
            (r'off',         'o\x0b'),

            # two non-letter characters and some letters;
            # "``" becomes an open quote, which is '\' in tenrm
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
                setup = r'\chardef\eff=102',
                call = string,
                mode = None,
                find='hboxes')[0]

        found = ''.join([x.split(' ')[1] for x in received.showbox()
            if 'tenrm' in x])

        assert expected==found, received.showbox()

def test_wordbox_remembers_ligature():
    doc = yex.Document()
    received = run_code(r'a---b``c',
            output='dummy',
            doc=doc,
            find='hboxes')
    assert len(received)==1

    found = [x.split(' ', maxsplit=1)[1]
            for x in received[0].showbox()
            if 'tenrm' in x]

    assert found==['a', '| (ligature ---)', 'b', r'\ (ligature ``)', 'c']
