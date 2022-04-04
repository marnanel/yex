from test import *

def test_font_name_at_deep_level(fs):
    add_cmr_to_fakefs(fs)
    run_code(
            r"\font\wombat=cmr9 \font\wombat=cmr10"
            )
