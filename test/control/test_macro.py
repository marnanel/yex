# Most of the macro tests are in test/control/test_def.

import yex
from test import *
import pytest

def test_macro_serialise():

    def run(code,
            expected):

        doc = yex.Document()

        run_code(
                r'\def\wombat'+code,
                doc=doc,
                )

        original = doc[r'\wombat']
        assert original.__getstate__() == expected

        serialised = original.__getstate__()

        revenant = yex.control.Macro.from_serial(serialised)

        # there is no == for Macros, and there isn't much need for one,
        # so...
        for field in [
                'name',
                'definition',
                'parameter_text',
                'is_long',
                'is_outer',
                'starts_at',
                ]:
            lhs = getattr(revenant, field)
            rhs = getattr(original, field)

            assert lhs==rhs, f"{field}: {expected}"

    run(
            r"{Wombat}",
            expected={
                'macro': 'wombat',
                'definition': 'Wombat',
                'starts_at': '<str>:1:13',
                }
            )

    run(
            r"#1{Wom#1bat}",
            expected={
                'macro': 'wombat',
                'definition': 'Wom#1bat',
                'starts_at': '<str>:1:15',
                'parameters': 1,
                }
            )

    run(
            r" sp#1on#2g{Wom#1bat#2}",
            expected={
                'macro': 'wombat',
                'definition': 'Wom#1bat#2',
                'starts_at': '<str>:1:23',
                'parameters': ['sp', 'on', 'g'],
                }
            )

def test_macro_delimited_with_name_of_another():

    # It doesn't matter that the delimiter token happens to be the
    # name of an existing macro.

    assert run_code(
            (
                r'\both peace\s quiet'
                ),
            setup=(
                r'\def\s{such }'
                r'\def\both#1\s#2{#1 and #2}'
                ),
            find='ch',
            )=='peace and quiet'

    # Even if the delimiter is used in its ordinary sense in the definition.

    assert run_code(
            (
                r'\menu chicken\w rice'
                ),
            setup=(
                r'\def\w{with }'
                r'\def\menu#1\w#2{#1 soup \w #2}'
                ),
            find='ch',
            )=='chicken soup with rice'

    # And even if the delimiter is \par, which would ordinarily cause a
    # "runaway expansion" error.

    assert run_code(
            (
                r'\a meets \par\a kisses' '\n\n'
                r'\a loves' '\n\n'
                r'\a marries' '\n\n'
                r'Happy ending.'
                ),
            setup=(
                r'\def\a#1\par{Juliet #1Romeo. }'
                ),
            find='chars',
            )==(
                    'Juliet meets Romeo. '
                    'Juliet kisses Romeo. '
                    'Juliet loves Romeo. '
                    'Juliet marries Romeo. '
                    'Happy ending.'
                    )

    # But if the delimiter appears in the expansion of another macro,
    # it doesn't count.

    with pytest.raises(yex.exception.UnexpectedEOFError):
        assert run_code(
                (
                    r'\dinner\x'
                    ),
                setup=(
                    r'\def\dinner#1\y#2{#1 and #2}'
                    r'\def\x{fish \y chips}'
                    ),
                )

    # And you can use it in both places.

    assert run_code(
            (
                r'\both\sb peace\s\sb quiet'
                ),
            setup=(
                r'\def\s{such }'
                r'\def\sb{\s blessed }'
                r'\def\both#1\s#2{#1 and #2}'
                ),
            find='ch',
            )=='such blessed peace and such blessed quiet'
