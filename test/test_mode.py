from test import *
import yex.mode
import yex
import logging

logger = logging.getLogger('yex.general')

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
            setup = r"\output={\global\setbox23=\box255}",
            call = "X\n\n",
            doc = doc,
            auto_save = False,
            )
    # Don't call doc.save() here. It will exercise the page builder again,
    # which will overwrite \box23.

    doc.outermost_mode.exercise_page_builder()
    copy23 = doc[r'\copy23']
    assert box_contents_to_string(copy23)=='[[] X [penalty: 10000] _ _]'

def test_word_boxes():
    doc = yex.Document()
    contents = run_code("We'll travel to Venus, we'll sail away to Mars",
            mode = None,
            doc = doc,
            output = 'dummy',
            find = 'hboxes',
            )
    assert len(contents)==1

    word_boxes = ';'.join([box.ch for box in contents[0]
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
        context = 'list [%s]; adding %s; expecting glue? %s' % (
                yex.box.Box.list_to_symbols_for_repr(before_list),
                item,
                expected_glue,
                )

        logger.debug("")
        logger.debug("=== try_appending: %s ===", context)

        doc.mode.append(item)
        after_list = list(doc.mode.list)

        context += '; found [%s]' % (
                yex.box.Box.list_to_symbols_for_repr(after_list),
                )
        logger.debug("  -- done: %s", context)

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

def test_mode_inner_page_builder_exercised():

    def it_gets_exercised(set_mode):
        doc = yex.Document()

        e1 = doc.open(r'\hbox{A}',
                on_eof='exhaust',
                )

        hbox = e1.next()

        if set_mode is not None:
            doc['_mode'] = set_mode(
                    doc = doc,
                    recipient = doc['_mode'],
                    )

        mode = doc['_mode']
        # append hbox ourselves,
        # so as not to exercise page builder accidentally
        mode.append(hbox)
        assert mode.list!=[], set_mode
        mode.exercise_page_builder()
        return mode.list==[]

    assert it_gets_exercised(None)
    assert not it_gets_exercised(yex.mode.Vertical)
    assert not it_gets_exercised(yex.mode.Horizontal)
    assert not it_gets_exercised(yex.mode.Restricted_Horizontal)
    assert not it_gets_exercised(yex.mode.Internal_Vertical)
