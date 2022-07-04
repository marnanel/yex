# Most of the macro tests are in test/control/test_def.

import yex
from test import *

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

        revenant = yex.control.C_Macro.from_serial(serialised)

        # there is no == for C_Macros, and there isn't much need for one,
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
