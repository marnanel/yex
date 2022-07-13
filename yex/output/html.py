import logging
import copy
import collections
import base64
import io
import string
import os
import importlib.resources
import yex
from yex.output import Output
from bs4 import BeautifulSoup

logger = logging.getLogger('yex.general')

class Html(Output):

    filename_extension = 'html'

    def __init__(self,
            doc,
            filename):

        self.filename = filename

        with (importlib.resources.files(
                yex) / "res" / "output" / "html" / "base.html"
                ).open('r') as base:
            self.result = BeautifulSoup(base,
            features="lxml",
                    )

        logger.debug("html: loaded base from base.html")

    @classmethod
    def can_handle(cls, file_extension):
        return file_extension in ['html', 'htm']

    def render(self):
        logger.debug("html: writing to %s", self.filename)
        with open(self.filename, 'w') as out:
            out.write(str(self.result))

        base_dir = os.path.dirname(self.filename)
        for extra in [
                'cmr10.ttf',
                ]:
            logger.debug("html: copying %s", self.filename)
            with (importlib.resources.files(
                    yex) / "res" / "output" / "html" / extra
                    ).open('rb') as f:
                content = f.read()

            with open(
                    os.path.join(base_dir, extra), 'wb') as f:
                f.write(content)

        logger.debug("html: done!")
