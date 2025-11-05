from test import *
import os, sys
import pytest

@pytest.mark.filterwarnings('error')
def test_mkdocs_build():
    starting_dir = os.getcwd()

    try:
        import mkdocs.commands.build, mkdocs.config

        os.chdir(sys.path[0])

        config = mkdocs.config.load_config()

        mkdocs.commands.build.build(config)
    except:
        os.chdir(starting_dir)
        raise
