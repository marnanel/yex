from test import *

def test_font_name_at_deep_level(fs):

    for filename in ['cmr10.tfm', 'cmr9.tfm']:
        fs.add_real_file(
                source_path = f'fonts/{filename}',
                target_path = filename,
                )

    run_code(
            r"\font\wombat=cmr9 \font\wombat=cmr10"
            )
