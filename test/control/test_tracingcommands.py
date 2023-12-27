from test import *
import yex
import pytest

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

def test_tracingcommands_basic():

    for level, expected in TRACING_BASIC_EXPECTED.items():
        found = []

        def monkeypatched_output(self, s):
            found.append(s)

        yex.control.keyword.Tracingcommands._output = monkeypatched_output

        run_code(
                fr"\tracingcommands={level}" + TRACING_BASICS_CODE,
                find = 'chars',
                )

        assert '\n'.join(found)==expected.lstrip(), level
