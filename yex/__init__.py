__title__ = 'yex'
__version__ = '0.1.4'
VERSION = __version__
__author__ = 'Marnanel Thurman'
__license__ = 'GPL-2'
__copyright__ = 'Copyright (c) 2022 Marnanel Thurman'

import sys
import types

from yex.document import Document

__all__ = [
        'Document',
        ]

# Cast ourselves to a subtype. This means we can call yex().
# See https://stackoverflow.com/questions/1060796/callable-modules .
class YexModule(types.ModuleType):
    def __call__(self, *args, **kwargs):
        import yex.put

        return yex.put.put(*args, **kwargs)

sys.modules[__name__].__class__ = YexModule
