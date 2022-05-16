from test import *

def test_par():
    saw = [repr(x) for x in run_code(r"a b\par c", find='saw')]

    assert saw == [
            'the letter a',
            'blank space  ',
            'the letter b',
            '[paragraph]',
            'the letter c',
            'blank space  ',
            ]

def test_controlspace():
    saw = [repr(x) for x in run_code(r"a b\ c", find='saw')]

    assert saw == [
            'the letter a',
            'blank space  ',
            'the letter b',
            'the character  ',
            'the letter c',
            'blank space  ',
            ]
