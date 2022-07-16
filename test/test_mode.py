from test import *
import yex.mode
import yex

def test_mode_switch_back():
    doc = yex.Document()

    startmode = doc['_mode']

    run_code(
        call = r"\hbox{X}",
        mode = None,
        doc = doc,
        )

    endmode = doc['_mode']
    assert isinstance(startmode, yex.mode.Vertical)
    assert startmode is endmode # the same instance, not just the same class

def test_mode_exercise_page_builder():

    doc = yex.Document()

    run_code(
            setup = r"\output={\global\box23=\box255}",
            call = r"\hbox{X}",
            doc = doc,
            mode = None,
            )
    # Don't call doc.save() here. It will exercise the page builder again,
    # which will overwrite \box23.

    copy23 = doc[r'\copy23'].value
    assert box_contents_to_string(copy23)=='[^ X]'

def test_word_boxes():
    doc = yex.Document()
    run_code("We'll travel to Venus, we'll sail away to Mars",
            mode = None,
            doc = doc,
            )
    doc.save() # force output

    contents = doc.contents[0]
    found = [x for x in contents if isinstance(x, yex.box.Box)]

    word_boxes = ';'.join([box.ch for box in found[0]
            if isinstance(box, yex.box.WordBox)])

    assert word_boxes==(
            "We'll;travel;to;Venus,;we'll;sail;away;to;Mars"), (
            f"list=str(contents)")

def test_mode_getstate():
    doc = yex.Document()
    assert doc['_mode'].__getstate__()=='vertical'

def test_mode_vertical_append():

    def new_doc():
        doc = yex.Document()
        assert isinstance(doc['_mode'], yex.mode.Vertical)
        return doc

    def try_appending(doc, item, expected_glue):
        before_list = list(doc.mode.list)
        doc.mode.append(item)
        after_list = list(doc.mode.list)

        context = 'before=%s; after=%s' % (
                yex.box.Box.list_to_symbols_for_repr(before_list),
                yex.box.Box.list_to_symbols_for_repr(after_list),
                )

        assert after_list[:len(before_list)]==before_list, context

        if expected_glue:
            assert len(after_list)==len(before_list)+2, context
            assert after_list[-1]==item, context
            assert isinstance(after_list[-2], yex.box.Leader), context
        else:
            assert len(after_list)==len(before_list)+1, context
            assert after_list[-1]==item, context

    doc = new_doc()
    try_appending(doc, yex.box.VBox(), expected_glue=False)
    try_appending(doc, yex.box.VBox(), expected_glue=True)

    doc = new_doc()
    try_appending(doc, yex.box.Rule(), expected_glue=False)
    try_appending(doc, yex.box.VBox(), expected_glue=False) # after a rule
    try_appending(doc, yex.box.Rule(), expected_glue=False)
    try_appending(doc, yex.box.Rule(), expected_glue=False)
    try_appending(doc, yex.box.VBox(), expected_glue=False)
    try_appending(doc, yex.box.VBox(), expected_glue=True)
    try_appending(doc, yex.box.Rule(), expected_glue=False)

    doc = new_doc()
    try_appending(doc, yex.box.Leader(), expected_glue=False)
    try_appending(doc, yex.box.VBox(), expected_glue=True) # extra
