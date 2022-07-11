import logging
import copy
import collections
import base64
import io
import string
import yex
import importlib.resources
from yex.output import Output
from bs4 import BeautifulSoup

logger = logging.getLogger('yex.general')

class Html(Output):

    filename_extension = 'html'

    def __init__(self,
            doc,
            filename):

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
        raise ValueError()
