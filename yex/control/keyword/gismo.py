"""
Gismo controls.

These controls deal with gismos, which are items inside lists.
Boxes are also gismos, but are covered in yex.control.box;
we may merge these two modules later.
"""
from yex.control.control import Unexpandable
import yex.box
import logging

logger = logging.getLogger("yex.commands")

@yex.decorator.control()
def Kern(width: yex.value.Dimen):
    return yex.box.Kern(
                width = width,
                explicit = True,
                )

@yex.decorator.control()
def Mkern(width: yex.value.Dimen):
    # TODO we have no general way of representing mudimen
    raise NotImplementedError()
