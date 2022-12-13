import logging
import yex
from test import *

logger = logging.getLogger('yex.general')

def test_leader_from_another():
    glue = yex.value.Glue(
            space=1, stretch=2, shrink=3)
    first = yex.box.Leader(
            glue = glue)

    construct_from_another(first,
            fields=['glue'],
            )
