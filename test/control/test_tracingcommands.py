from test import *
import yex
import pytest
import logging

logger = logging.getLogger('kepi.test')

@pytest.mark.xfail()
def test_tracingcommands_p88():
    found = run_code(
            r"""\tracingcommands=1
\hbox{
$
\vbox{
\noindent$$
x\showlists
$$}$}\bye""")
    assert found==r"""{vertical mode: \hbox}
{restricted horizontal mode: blank space }
{math shift character $}
{math mode: blank space }
{\vbox}
{internal vertical mode: blank space }
{\noindent}
{horizontal mode: math shift character $}
{display math mode: blank space }
{the letter x}"""

TRACING_BASICS_CODE = r"""
A
\iftrue
B
\fi
C

P
\iffalse
Q
\fi
R


\advance\count12 by 3
A
\iftrue
B
\fi
C

P
\iffalse
Q
\fi
R
"""

TRACING_BASIC_EXPECTED = {
        0: '',

        1: r"""
{vertical mode: the letter A}
{horizontal mode: the letter A}
{blank space  }
{the letter B}
{blank space  }
{the letter C}
{blank space  }
{\par}
{vertical mode: the letter P}
{horizontal mode: the letter P}
{blank space  }
{the letter R}
{blank space  }
{\par}
{vertical mode: \par}
{\advance}
{the letter A}
{horizontal mode: the letter A}
{blank space  }
{the letter B}
{blank space  }
{the letter C}
{blank space  }
{\par}
{vertical mode: the letter P}
{horizontal mode: the letter P}
{blank space  }
{the letter R}
{blank space  }
{\shipout}""",

    2: r"""
{vertical mode: the letter A}
{horizontal mode: the letter A}
{blank space  }
{\iftrue}
{true}
{the letter B}
{blank space  }
{\fi}
{the letter C}
{blank space  }
{\par}
{vertical mode: the letter P}
{horizontal mode: the letter P}
{blank space  }
{\iffalse}
{false}
{the letter R}
{blank space  }
{\par}
{vertical mode: \par}
{\advance}
{the letter A}
{horizontal mode: the letter A}
{blank space  }
{\iftrue}
{true}
{the letter B}
{blank space  }
{\fi}
{the letter C}
{blank space  }
{\par}
{vertical mode: the letter P}
{horizontal mode: the letter P}
{blank space  }
{\iffalse}
{false}
{the letter R}
{blank space  }
{\shipout}""",
}

class Monkeypatched_Output:

    def __init__(self):
        self.found = []

    def __enter__(self):
        def _output(_, s):
            self.found.append(s)

        self.old_output = yex.control.keyword.Tracingcommands._output
        yex.control.keyword.Tracingcommands._output = _output

        return self

    def __exit__(self, e1, e2, e3):
        yex.control.keyword.Tracingcommands._output = self.old_output

def test_tracingcommands_basic():

    for level, expected in TRACING_BASIC_EXPECTED.items():

        with Monkeypatched_Output() as mpo:

            run_code(
                    fr"\tracingcommands={level}" + TRACING_BASICS_CODE,
                    )

            assert '\n'.join(mpo.found)==expected.lstrip(), level

def do_conditional_trace(
        before,
        expected,
        after = r'\fi',
        middle_symbol = 'B',
        ):

    with Monkeypatched_Output() as mpo:

        call_code = (
            'A'
            f'{before}'
            f'{middle_symbol}'
            f'{after} '
            'C'
            )

        logger.debug("About to call: %s", call_code)

        run_code(
                setup = (
                    r'\tracingcommands=2'
                    ),
                call = call_code,
                )

        full_expected = [
                '{vertical mode: the letter A}',
                '{horizontal mode: the letter A}',
                ]

        full_expected += list(expected)
        full_expected += [
                '{the letter C}',
                '{blank space  }',
                r'{\shipout}'
                ]
        assert mpo.found==full_expected, f"{before} .. {after}"

def test_tracingcommands_iftrue():
    do_conditional_trace(
            before = r'\iftrue ',
            expected = [
                r'{\iftrue}',
                r'{true}',
                '{the letter B}',
                r'{\fi}',
                ])

def test_tracingcommands_iffalse():
    do_conditional_trace(
            before = r'\iffalse ',
            expected = [
                r'{\iffalse}',
                r'{false}',
                ])

def test_tracingcommands_ifcase():
    for i, include_else, expect_letter, expect_terminator in [
            (0, True,  'X',  r'\or',      ),
            (1, True,  'Y',  r'\or',      ),
            (2, True,  'Z',  r'\else',    ),
            (3, True,  'Q',  r'\fi',      ),

            (0, False, 'X',  r'\or',      ),
            (1, False, 'Y',  r'\or',      ),
            (2, False, 'Z',  r'\fi',      ),
            (3, False, None, None,        ),

            ]:

        if include_else:
            maybe_else = r'\else Q'
        else:
            maybe_else = ''

        expected = [
                r'{\ifcase}',
                '{case ' f'{i}' '}',
                ]

        if expect_letter is not None:
            expected.append(
                    '{the letter '
                    f'{expect_letter}'
                    '}')

        if expect_terminator is not None:
            expected.append(r'{'
                            f'{expect_terminator}'
                            '}')

        do_conditional_trace(
                before = (
                    r'\ifcase '
                    f'{i}'
                    r'X\or '
                    r'Y\or '
                    'Z'
                    f'{maybe_else}'
                    ),
                expected = expected,
                middle_symbol = '', # don't add the B
                )
