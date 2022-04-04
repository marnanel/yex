from test import *

def test_font_name_at_deep_level(yex_test_fs):

    yex_test_fs.add_real_file(
            source_path = 'fonts/cmr9.tfm',
            target_path = 'cmr9.tfm',
            )

    run_code(
            r"\font\wombat=cmr9 \font\wombat=cmr10"
            )
