import tempfile
from bs4 import BeautifulSoup
from test import *
import os
import pytest
import yex
import glob
import logging

logger = logging.getLogger('yex.general')

@pytest.fixture
def html_driver():

    directory_to_remove = None

    def get_driver(
            code = None,
            ):

        doc = yex.Document()

        directory_to_remove = output_dir = tempfile.mkdtemp(prefix='yex-test')
        filename = os.path.join(
                output_dir,
                'wombat.html')

        result = yex.output.html.Html(doc, filename)

        if code is not None:
            run_code(code,
                    doc=doc,
                    output=result,
                    )

        return result

    yield get_driver

    if directory_to_remove is None:
        logger.debug("Nothing to clean up.")
        return

    logger.debug("Cleaning up directory: %s", directory_to_remove)

    for n in glob.glob(os.path.join(directory_to_remove, '*')):
        try:
            logger.debug("  -- %s", n)
        except Exception as e:
            logger.debug("    -- failed, %s", e)

    try:
        logger.debug("  -- %s", directory_to_remove)
        os.removedir(directory_to_remove)
    except Exception as e:
        logger.debug("    -- failed, %s", e)

    logger.debug("Cleanup finished.")

def test_output_html_init(html_driver):
    h = html_driver()

    # h.result is BeautifulSoup

    assert h.result.find('title').string=='Yex output'

def test_output_html_can_handle():
    assert yex.output.html.Html.can_handle('html')
    assert yex.output.html.Html.can_handle('htm')
    assert not yex.output.html.Html.can_handle('pdf')

def test_output_html_render(html_driver):

    STRING = "Where have all the flowers gone?"

    h = html_driver(STRING)

    h.render()

    with open(h.filename, 'r') as f:
        html = f.read()

    logger.debug("==== Rendered HTML: ====\n%s\n==== ends ====", html)
    results = BeautifulSoup(html, features='lxml')

    main = results.find('main')

    assert [s for s in main.strings if s.strip()!='']==[
            'Where', 'have', 'all', 'the', 'flowers', 'gone?',
            ]

def make_example_lines(
        para_indent,
        first_line_spacing,
        second_line_spacing,
        split_at,
        ):

    font = yex.font.Default()

    contents = [[]]
    space_width = first_line_spacing

    for i, word in enumerate(
            'My face is my fortune, sir; nobody asked you to'.split()):

        if i==0:
            # start of first line
            contents[-1].append(
                    yex.box.Leader(glue=yex.value.Glue(para_indent)))
        elif not contents[-1]:
            pass # start of subsequent line; do nothing
        else:
            glue = yex.value.Glue(space_width)
            leader = yex.box.Leader(glue=glue)
            contents[-1].append(leader)

        wordbox = yex.box.WordBox(font)
        for letter in word:
            wordbox.append(letter)

        contents[-1].append(wordbox)

        if i==split_at:
            contents.append([])
            space_width = second_line_spacing

    result = [
            yex.box.HBox.from_contents(line) for line in contents
            ]
    return result

def test_output_html_internals_realistic(html_driver):

    h = html_driver()

    lines = make_example_lines(
        para_indent = 5,
        first_line_spacing = 3,
        second_line_spacing = 7,
        split_at = 4,
    )

    words = h._generate_written_words(lines)

    assert str(words)==('['
            '[ 5.0 [wordbox;My] 3.0], '
            '[ [wordbox;face] 3.0], '
            '[ [wordbox;is] 3.0], '
            '[ [wordbox;my] 3.0], '
            '[ [wordbox;fortune,] br], '
            '[ [wordbox;sir;] 7.0], '
            '[ [wordbox;nobody] 7.0], '
            '[ [wordbox;asked] 7.0], '
            '[ [wordbox;you] 7.0], '
            '[ [wordbox;to] br]'
            ']'
            )

    lines = make_example_lines(
        para_indent = 3,
        first_line_spacing = 4,
        second_line_spacing = 5,
        split_at = 2,
    )

    words = h._generate_written_words(lines,
            merge_with = words,
            )

    assert str(words)==('['
            '[ 5.0,3.0 [wordbox;My] 3.0,4.0], '
            '[ [wordbox;face] 3.0,4.0], '
            '[ [wordbox;is] 3.0,br], '
            '[ [wordbox;my] 3.0,5.0], '
            '[ [wordbox;fortune,] br,5.0], '
            '[ [wordbox;sir;] 7.0,5.0], '
            '[ [wordbox;nobody] 7.0,5.0], '
            '[ [wordbox;asked] 7.0,5.0], '
            '[ [wordbox;you] 7.0,5.0], '
            '[ [wordbox;to] br,br]'
            ']'
            )

    assert [x.contains_breaks for x in words] == [
            False, False, True, False, True, False, False, False, False, True,
            ], f'words={words}'

    assert [x.has_lhs for x in words] == [
            True,
            False, False, False, False, False, False, False, False, False,
            ], f'words={words}'

    width_boxes = h._generate_width_boxes(words)
    assert str(width_boxes)==(
            '[[5.0,3.0 My face is 3.0,4.0], [my fortune, 3.0,5.0], '
            '[sir; nobody asked you to 7.0,5.0]]'
            )

    words[-2].rhs = [
            yex.value.Dimen(1),
            yex.value.Dimen(2),
            ]

    words[-1].rhs = words[-2].rhs

    width_boxes = h._generate_width_boxes(words)
    assert str(width_boxes)==(
            '[[5.0,3.0 My face is 3.0,4.0], [my fortune, 3.0,5.0], '
            '[sir; nobody asked 7.0,5.0], [you to 1.0,2.0]]'
            )

    # Edge case where the "br"s are (correctly) visible
    # in the repr for the width boxes.
    # They will be replaced as appropriate in the final HTML.
    words[3].rhs[1] = None

    width_boxes = h._generate_width_boxes(words)
    assert str(width_boxes)==(
            '[[5.0,3.0 My face is 3.0,4.0], [my 3.0,br], [fortune, br,5.0], '
            '[sir; nobody asked 7.0,5.0], [you to 1.0,2.0]]'
            )

def test_output_html_width_box_classes(html_driver):

    h = html_driver()

    words = h._generate_written_words(
            make_example_lines(
                para_indent = 0,
                first_line_spacing = 1,
                second_line_spacing = 2,
                split_at = 4,
            ),
            )

    words = h._generate_written_words(
            make_example_lines(
                para_indent = 0,
                first_line_spacing = 3,
                second_line_spacing = 4,
                split_at = 2,
            ),
            merge_with = words,
            )

    def analyse(words):
        width_boxes = h._generate_width_boxes(words)
        return [
                (
                    str(wb),
                    wb.css_class,
                    )
                for wb in width_boxes
                ]

    widths_1 = analyse(words)

    assert [w[0] for w in widths_1] == [
                   '[My face is 1.0,3.0]',
                   '[my fortune, 1.0,4.0]',
                   '[sir; nobody asked you to 2.0,4.0]',
                   ], 'each box is different'

    assert len(set(
        [w[1] for w in widths_1]))==3, (
                'each box gets a different CSS class name'
                )

    words[7].rhs[0]=yex.value.Dimen(9)

    widths_2 = analyse(words)

    assert [w[0] for w in widths_2] == [
                   '[My face is 1.0,3.0]',
                   '[my fortune, 1.0,4.0]',
                   '[sir; nobody 2.0,4.0]',
                   '[asked 9.0,4.0]',
                   '[you to 2.0,4.0]',
                   ], 'it returns to the previous values after interpolation'

    assert [
            (
                w2[0],
                dict(widths_1).get(w2[0]) == dict(widths_2).get(w2[0]),
                w2[1] not in [w1[1] for w1 in widths_1],
                )
            for w2 in widths_2
            ]==[
                    # repr                     same?      new class?
                    ('[My face is 1.0,3.0]',   True,      False, ),
                    ('[my fortune, 1.0,4.0]',  True,      False, ),
                    ('[sir; nobody 2.0,4.0]',  False,     False, ),
                    ('[asked 9.0,4.0]',        False,     True,  ),
                    ('[you to 2.0,4.0]',       False,     False, ),

                    ], (
                            'it reuses the earlier CSS class names'
                            )
