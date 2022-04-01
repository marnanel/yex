def test_expand_long_def():
    doc = Document()

    run_code(r"\long\def\ab#1{a#1b}",
            doc=doc)
    run_code(r"\def\cd#1{c#1d}",
            doc=doc)

    assert doc[r'\ab'].is_long == True
    assert run_code(r"\ab z",
            doc=doc,
            find='ch',
            )=="azb"
    assert run_code(r"\ab \par",
            doc=doc,
            find='ch',
            )==r"a\parb"

    assert doc[r'\cd'].is_long == False
    assert run_code(r"\cd z",
            doc=doc,
            find='ch',
            )=="czd"
    with pytest.raises(yex.exception.ParseError):
        run_code(r"\cd \par",
                doc=doc,
                find='ch',
                )

def test_expand_outer():

    # Per the TeXbook, p.205, \outer macros may not appear
    # in several places. We don't test all of them yet
    # (marked with a *), but we will. (TODO.) They are:
    #
    #  - In a macro argument
    #  - Param text of definition *
    #  - Replacement text of definition
    #  - Preamble to alignment *
    #  - Conditional text which is being skipped over *

    SETUP = (
            r"\outer\def\wombat{W}"
            r"\def\notwombat{W}"
            r"\def\spong#1{Spong}"
            )

    doc = Document()
    run_code(SETUP,
            doc=doc)

    assert doc[r'\wombat'].is_outer == True
    assert doc[r'\notwombat'].is_outer == False

    ##############################

    for (forbidden, context) in [
            (
                r'\spong{%s}',
                'macro argument',
                ),
            (
                r'\def\fred#1%s#2{fred}',
                'param text',
                ),
            (
                r'\def\fred#1{fred#1}\fred %s',
                'replacement text',
                ),
            ]:

        try:
            reason = f"outer macro called in {context}"
            run_code(
                    setup = SETUP,
                    call = forbidden % (r'\wombat',),
                    find = 'chars',
                    # not reusing doc
                    )
            assert False, reason + " succeeded"
        except yex.exception.YexError:
            assert True, reason + " failed"

    ##############################

        try:
            reason = f'non-outer called in {context}'
            run_code(
                    setup = SETUP,
                    call = forbidden % (r'\notwombat',),
                    find = 'chars',
                    )
            assert True, reason + " succeeded"
        except yex.exception.YexError:
            assert False, reason + " failed"

def test_expand_edef_p214():

    assert run_code(
            setup=(
                r'\def\double#1{#1#1}'
                r'\edef\a{\double{xy}}'
                ),
            call=(
                r"\a"
                ),
            find='chars',
            )=='xy'*2

    assert run_code(
            setup=(
                r'\def\double#1{#1#1}'
                r'\edef\a{\double{xy}}'
                r'\edef\a{\double\a}\a'
                ),
            call=(
                r"\a"
                ),
            find='chars',
            )=='xy'*4

def test_expand_long_long_long_def_flag():
    doc = Document()
    string = "\\long\\long\\long\\def\\wombat{Wombat}\\wombat"
    assert run_code(string,
            find='chars',
            doc=doc,
            )=="Wombat"
    assert doc[r'\wombat'].is_long == True

# XXX TODO Integration testing of edef is best done when
# XXX macro parameters are working.

def _test_expand_global_def(form_of_def, doc=None):

    if doc is None:
        doc = Document()

    result = run_code(
            r"\def\wombat{Wombat}"
            r"\wombat",
            find='chars',
            doc=doc,
            )
    assert result=="Wombat"

    doc.begin_group()

    result = run_code(
            r"\wombat"
            r"\def\wombat{Spong}"
            r"\wombat",
            find='chars',
            doc=doc,
            )
    assert result=="WombatSpong"

    doc.end_group()

    result = run_code(
            "\\wombat",
            find='chars',
            doc=doc)
    assert result=="Wombat"

    doc.begin_group()

    result = run_code(
            r"\wombat" +\
            form_of_def + r"\wombat{Spong}"
            r"\wombat",
            find='chars',
            doc=doc)
    assert result=="WombatSpong"

    doc.end_group()

    result = run_code(
            r"\wombat",
            find='chars',
            doc=doc)
    assert result=="Spong"

def test_expand_global_def():
    _test_expand_global_def(r"\global\def")

def test_expand_gdef():
    _test_expand_global_def(r"\gdef")
