import logging
import yex
import yex.decorator
import pytest
from test import *

logger = logging.getLogger('yex.general')

DECORATOR_CONTROL_NAME = 'decoratortest'

def run_decorator_test(
        control,
        parameters=[],
        expected_types=None,
        expected_values=None,
        superclass=yex.control.Unexpandable,
        level='executing',
        ):

    logger.debug("=== run_decorator_test begins ===")

    doc = yex.Document()
    e = yex.parse.Expander(source='', doc=doc, level=level, on_eof='exhaust')

    instance = control()
    assert isinstance(instance, superclass)

    for parameter in reversed(parameters):
        logger.debug("Pushing parameter: %s", parameter)
        e.pushback.push(parameter)

    doc['\\'+DECORATOR_CONTROL_NAME] = instance

    e.pushback.push(yex.parse.Control(
        name=DECORATOR_CONTROL_NAME,
        doc=doc,
        location=e.location,
        ))

    found_values = []
    for n in e:
        found_values.append(n)

    if expected_types is not None:
        found_types = [x.__class__.__name__ for x in found_values]

        assert found_types == expected_types, control

    if expected_values is not None:
        for i, (found, expected) in enumerate(
                zip(found_values, expected_values)):
            assert str(found)==expected, f'{control} #{i}'

    return found_values

def test_decorator_simple():
    @yex.decorator.control()
    def Thing():
        result = 123
        logger.debug("Thing called; returning %s", result)
        return result

    run_decorator_test(
            control=Thing,
            expected_types = ['Number'],
            expected_values = ['123'],
            )

def test_decorator_returns_list():
    @yex.decorator.control()
    def Thing():
        result = yex.parse.Token.deserialise_list('abc')
        logger.debug("Thing called; returning %s", result)
        return result

    items = run_decorator_test(
            control=Thing,
            expected_types = ['Letter', 'Letter', 'Letter'],
            )

    assert [n.ch for n in items]==['a', 'b', 'c']

def test_decorator_int_param():
    @yex.decorator.control()
    def Thing(param1: int):
        result = param1 * 2
        logger.debug("Thing called with param1=%s; returning %s",
                param1, result)
        return result

    run_decorator_test(
            control=Thing,
            parameters=[100],
            expected_types = ['Number'],
            expected_values = ['200'],
            )

def test_decorator_location_param():

    where = {}

    @yex.decorator.control()
    def Thing(param1: yex.parse.Location):
        logger.debug("Thing called with param1=%s", param1)
        where['where'] = str(param1)

    run_decorator_test(
            control=Thing,
            parameters=[],
            expected_types = [],
            expected_values = [],
            )

    assert where['where']=='<str>:0:1'

def test_decorator_tokens_param():

    @yex.decorator.control()
    def Thing(tokens):
        logger.debug("Thing called")
        assert isinstance(tokens, yex.parse.Expander)
        tokens.push(yex.value.Number(177))

    run_decorator_test(
            control=Thing,
            expected_types = ['Number'],
            expected_values = ['177'],
            )

def test_decorator_doc_param():

    @yex.decorator.control()
    def Thing(doc):
        logger.debug("Thing called")
        assert isinstance(doc, yex.Document)
        return yex.value.Number(177)

    run_decorator_test(
            control=Thing,
            expected_types = ['Number'],
            expected_values = ['177'],
            )

def test_decorator_token_param():

    @yex.decorator.control()
    def Thing(a: yex.parse.Letter):
        logger.debug("Thing called")
        assert isinstance(a, yex.parse.Letter)
        return a.ch.upper()

    run_decorator_test(
            control=Thing,
            parameters=[
                yex.parse.Letter('x'),
                ],
            expected_types = ['Letter'],
            expected_values = ['X'],
            )

    run_decorator_test(
            control=Thing,
            parameters=[
                'y',
                ],
            expected_types = ['Letter'],
            expected_values = ['Y'],
            )

    with pytest.raises(yex.exception.NeededSomethingElseError):
        run_decorator_test(
                control=Thing,
                parameters=[
                    yex.parse.Other('9'),
                    ],
                )

def test_decorator_control_param():

    found = {}

    @yex.decorator.control()
    def Thing(a: yex.control.Control):
        logger.debug("Thing called")
        assert isinstance(a, yex.control.Control)
        found['thing'] = str(a)

    run_decorator_test(
            control=Thing,
            parameters=[
                yex.control.keyword.Advance(),
                ],
            )

    assert found['thing']==r'\advance'

def test_decorator_doc():

    @yex.decorator.control()
    def Thing(tokens):
        "I like cheese"
        logger.debug("Thing called")

    instance = Thing()
    assert isinstance(instance, yex.control.Unexpandable)
    assert instance.__doc__=="I like cheese"

def test_decorator_modes():
    @yex.decorator.control(
            horizontal = 'vertical',
            vertical = 'horizontal',
            math = False,
            )
    def Thing(tokens):
        "I like cheese"
        logger.debug("Thing called")

    instance = Thing()
    assert isinstance(instance, yex.control.Unexpandable)
    assert instance.horizontal == 'vertical'
    assert instance.vertical == 'horizontal'
    assert instance.math == False

def test_decorator_push_result():

    @yex.decorator.control(
            )
    def Thing1():
        logger.debug("Thing1 called")
        return 1

    @yex.decorator.control(
            push_result=False,
            )
    def Thing2():
        logger.debug("Thing2 called")
        return 1

    run_decorator_test(
            Thing1,
            expected_types=['Number'],
            expected_values=['1'],
            )

    run_decorator_test(
            Thing2,
            expected_types=['int'],
            expected_values=['1'],
            )

def test_decorator_expandable():

    @yex.decorator.control(
            expandable=True,
            )
    def Thing(tokens):
        "I like cheese"
        logger.debug("Thing called")

    run_decorator_test(
            control=Thing,
            superclass=yex.control.Expandable,
            expected_types = [],
            expected_values = [],
            )

def test_decorator_conditional():
    @yex.decorator.control(
            conditional = True,
            )
    def Thing1():
        logger.debug("Thing1 called")

    @yex.decorator.control(
            conditional = False,
            )
    def Thing2():
        logger.debug("Thing2 called")

    @yex.decorator.control(
            )
    def Thing3():
        logger.debug("Thing3 called")

    assert Thing1.conditional == True
    assert Thing2.conditional == False
    assert Thing3.conditional == False

def test_decorator_query_simple():

    @yex.decorator.control()
    def Thing():
        result = 123
        logger.debug("Thing called; returning %s", result)
        return result

    @Thing.on_query()
    def Thing(doc):
        result = yex.value.Number(456)
        logger.debug("Thing queried; returning %s", result)
        return result

    @yex.decorator.control()
    def Wombat():
        result = 789
        logger.debug("Wombat called; returning %s", result)
        return result

    run_decorator_test(
            control=Thing,
            level='executing',
            expected_types = ['Number'],
            expected_values = ['123'],
            )

    run_decorator_test( control=Thing,
            level='querying',
            expected_types = ['Number'],
            expected_values = ['456'],
            )

    run_decorator_test(
            control=Wombat,
            level='executing',
            expected_types = ['Number'],
            expected_values = ['789'],
            )

    run_decorator_test(
            control=Wombat,
            level='querying',
            expected_types = ['Number'],
            expected_values = ['789'],
            )
