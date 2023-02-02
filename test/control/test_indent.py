import yex
from test import *
import logging

logger = logging.getLogger('yex.general')

def test_indent():

    def run(everypar, parindent, parskip,
            noindent,
            begin_with_stuff):

        doc = yex.Document()

        doc[r'\everypar'] = everypar
        doc[r'\spacefactor'] = 177
        doc[r'\parindent'] = parindent
        doc[r'\parskip'] = parskip

        doc[r'\hsize'] = yex.value.Dimen(10000, 'pt')

        if noindent:
            command = r'\noindent'
        else:
            command = r'\indent'

        context = (
                f"everypar: {everypar}, parindent: {parindent}, "
                f"parskip: {parskip}, command: {command}, "
                f"begin_with_stuff: {begin_with_stuff}"
                )

        starting_mode = doc[r'_mode']
        assert isinstance(starting_mode, yex.mode.Vertical), context

        # We begin in vertical mode, which causes the first
        # \indent to flip us to horizontal mode. The second \indent is
        # already in horizontal mode, so it behaves slightly differently.

        logger.debug('==='*8)
        logger.debug('===')
        logger.debug('=== test_indent begins ==')
        logger.debug('  -- %s', context)
        logger.debug('===')
        logger.debug('==='*8)

        if begin_with_stuff:
            doc[r'_mode'].list.append(yex.box.Rule())
            logger.debug("pushed new Rule to doc.mode.list: it's now: %s",
                doc.mode.list)

        run_code(fr"{command} oranges \indent lemons\hfill",
                doc=doc,
                output='dummy',
                mode=None,
                )
        assert isinstance(doc[r'_mode'], yex.mode.Horizontal), context
        assert doc[r'\spacefactor']==1000, context

        doc.save()

        context += f'; starting_mode.list='
        context += yex.box.Box.list_to_symbols_for_repr(starting_mode.list)

        assert len(doc.output.found)==1, context
        toplevel = doc.output.found[0]

        context += f'; toplevel={toplevel}'

        # top of page
        assert isinstance(toplevel[0], yex.box.Leader), context

        if begin_with_stuff:
            # the rule we put there
            assert isinstance(toplevel[1], yex.box.Rule), context

            toplevel = toplevel[2:]
            """
            # the parskip glue that got added
            assert isinstance(toplevel[2], yex.box.Leader), context
            assert toplevel[2]==parskip, context

            boxes = [item for item in toplevel[3:]
                    if not isinstance(item, yex.box.Leader)][0]
                    """
            boxes = toplevel[2]
        else:
            boxes = toplevel[1]

        assert isinstance(boxes, yex.box.HBox), context

        found = [item for item in boxes
                if not isinstance(item,
                    (yex.box.Breakpoint, yex.box.Penalty))]

        logger.debug("Found: %s", len(found))
        logger.debug("  %s", found)

        if noindent:
            found.insert(0, "adjust numbering")
        else:
            assert found[0].width==parindent, context

        assert isinstance(found[1], yex.box.WordBox), context
        assert found[1].ch==everypar+"oranges", context

        assert isinstance(found[2], yex.box.Leader), context

        assert found[3].width==parindent, context

        assert isinstance(found[4], yex.box.WordBox), context
        assert found[4].ch=="lemons", context

        assert isinstance(found[5], yex.box.Leader), context

    for parindent_size in [10, 100, 1000]:
        for parskip_size in [10, 30, 100]:
            for begin_with_stuff in [False, True]:
                for noindent in [False, True]:
                    for everypar in ['', 'juicy']:
                        run(
                                parindent = yex.value.Dimen(parindent_size),
                                parskip = yex.value.Glue(parskip_size),
                                begin_with_stuff = begin_with_stuff,
                                noindent = noindent,
                                everypar = everypar,
                                )
