import yex
from test import *
import logging

logger = logging.getLogger('yex.test')

def run_end_test(
        doc=None,
        expect_finish=False,
        deadcycles = None,
        mode_list = [],
        ):
    # In each case, if expect_finish==True: we expect yex to end the job;
    # the remaining symbols will not be read.
    # If expect_finish==False: we expect the job to continue, and for
    # the equivalent of
    #
    #       \line{} \vfill \penalty=`10000000000
    #
    # to have been added. \line{} is defined in plain.tex as
    #
    #       \def\line{\hbox to\hsize}
    #
    # so we will be expecting:
    #
    #    - to be in vertical mode
    #    - a new hbox to have been added, with a width of \hsize
    #    - new vertical glue to have been added, with a height of zero
    #       and infinite stretchability
    #    - a penalty to have been added of 1x10E10, i.e. ten billion

    if doc is None:
        doc = yex.Document()

    if deadcycles is not None:
        doc[r'\deadcycles'] = deadcycles

    # Not elegant, but it's what we're directly testing for
    doc['_mode'].list.extend(mode_list)
    logger.debug("Outermost mode list is %s",
            doc['_mode'].list)

    TEN_BILLION = 10000000000

    class Tracer(yex.parse.Internal):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._called = False

        def __call__(self, *args, **kwargs):
            logger.debug("(Tracer item called)")
            self._called = True

    tracer = Tracer()

    e = yex.parse.Expander(
            doc=doc,
            source=['\\', 'e', 'n', 'd', tracer],
            on_eof='exhaust',
            )

    found_items = [item for item in e]

    if expect_finish:
        assert found_items==[]
        assert not tracer._called
    else:
        assert tracer._called

def test_end_simple():
    run_end_test(
            expect_finish = True,
            )

def test_end_with_deadcycles():
    run_end_test(
            deadcycles = 20,
            expect_finish = False,
            )

def _list_item_for_testing():
    return yex.box.HBox()

def test_end_with_list_items():
    run_end_test(
            mode_list = [_list_item_for_testing()],
            expect_finish = False,
            )

def test_end_with_list_items_and_deadcycles():
    run_end_test(
            mode_list = [_list_item_for_testing()],
            deadcycles = 20,
            expect_finish = False,
            )
