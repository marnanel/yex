import logging
import yex
import yex.decorator
from test import *

logger = logging.getLogger('yex.general')

def run_decorator_test(
        control,
        parameters=[],
        expected_types=None,
        expected_values=None,
        ):

    doc = yex.Document()
    t = yex.parse.Tokeniser(source='', doc=doc)
    s = t.source
    e = yex.parse.Expander(tokeniser=t)

    assert isinstance(control, yex.control.C_Unexpandable)

    for parameter in reversed(parameters):
        logger.debug("Pushing parameter: %s", parameter)
        t.push(parameter)

    control(e)

    if expected_types is not None:
        found_types = [x.__class__.__name__ for x in s.push_back]

        assert found_types == expected_types, control

    if expected_values is not None:
        for i, (found, expected) in enumerate(
                zip(s.push_back, expected_values)):
            assert found==expected, f'{control} #{i}'

    return e

def test_decorator_simple():
    @yex.decorator.control
    def Thing():
        result = 123
        logger.debug("Thing called; returning %s", result)
        return result

    run_decorator_test(
            control=Thing,
            expected_types = ['Number'],
            expected_values = [123],
            )

def test_decorator_returns_list():
    @yex.decorator.control
    def Thing():
        result = yex.parse.Token.deserialise_list('abc')
        logger.debug("Thing called; returning %s", result)
        return result

    e = run_decorator_test(
            control=Thing,
            expected_types = ['Letter', 'Letter', 'Letter'],
            )

    assert [x.ch for x in e.tokeniser.source.push_back]==['c', 'b', 'a']

def test_decorator_int_param():
    @yex.decorator.control
    def Thing(param1: int):
        result = param1 * 2
        logger.debug("Thing called with param1=%s; returning %s",
                param1, result)
        return result

    run_decorator_test(
            control=Thing,
            parameters=[100],
            expected_types = ['Number'],
            expected_values = [200],
            )

def test_decorator_tokens_param():
    @yex.decorator.control
    def Thing(tokens):
        logger.debug("Thing called")
        assert isinstance(tokens, yex.parse.Expander)
        tokens.push(yex.value.Number(177))

    run_decorator_test(
            control=Thing,
            expected_types = ['Number'],
            expected_values = [177],
            )
