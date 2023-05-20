import datetime
from yex.document import Document, Group
import yex.output
from test import *
import os.path
import pytest
import os
import pickle

def test_group_simple():
    doc = Document()

    doc[r'\count0']=100
    assert doc[r'\count0']==100

    doc.begin_group()

    doc[r'\count0']=100
    doc[r'\count1']=0

    doc[r'\count0']=200

    doc[r'\count0']=200
    doc[r'\count1']=0

    doc.end_group()

    doc[r'\count0']=100
    doc[r'\count1']=0

def test_group_matching():
    doc = Document()

    g1 = doc.begin_group()
    assert g1 is not None
    g2 = doc.begin_group()
    assert g2 is not None
    doc.end_group(group=g2)
    doc.end_group(group=g1)

    g1 = doc.begin_group()
    g2 = doc.begin_group()
    doc.end_group()
    doc.end_group(group=g1)

    g1 = doc.begin_group()
    g2 = doc.begin_group()
    doc.end_group(group=g2)
    doc.end_group()

    g1 = doc.begin_group()
    g2 = doc.begin_group()
    doc.end_group()
    doc.end_group()

    g1 = doc.begin_group()
    g2 = doc.begin_group()
    with pytest.raises(ValueError):
        doc.end_group(group=g1)

def test_group_set_global():
    doc = Document()

    assert doc[r'\count0']==0

    doc[r'\count0'] = 1
    assert doc[r'\count0']==1

    doc.begin_group()
    doc[r'\count0'] = 2
    assert doc[r'\count0']==2

    doc.end_group()
    assert doc[r'\count0']==1

    doc.begin_group()
    doc.next_assignment_is_global = True
    doc[r'\count0'] = 2
    assert doc[r'\count0']==2

    doc.end_group()
    assert doc[r'\count0']==2

def test_document_end_all_groups(fs):

    doc = yex.Document()

    for i in range(10):
        assert len(doc.groups)==i
        doc.begin_group()

    doc.end_all_groups()
    assert len(doc.groups)==0

def test_document_save_ends_all_groups(yex_test_fs):

    FILENAME = "x.svg"

    doc = yex.Document()

    run_code(
            r"\hbox{X}",
            output = yex.output.Output.driver_for(doc, FILENAME),
            doc = doc,
            )

    doc.save()

    assert os.access(FILENAME, os.F_OK), "it didn't save"
    assert check_svg(FILENAME)==['X']
