import yex.util

def test_util_fraction_to_str():
    assert yex.util.fraction_to_str(8192, 16)=="0.125"
    assert yex.util.fraction_to_str(8192, 15)=="0.25"
    assert yex.util.fraction_to_str(8192, 14)=="0.5"

    assert yex.util.fraction_to_str(21845, 16)=="0.33333"
    assert yex.util.fraction_to_str(21845*2, 16)=="0.66666"

    assert yex.util.fraction_to_str(8292, 16)=="0.12653"
    assert yex.util.fraction_to_str(8392, 16)=="0.12805"

    assert yex.util.fraction_to_str(0, 16)=="0.0"
    assert yex.util.fraction_to_str(65536, 16)=="1.0"

    assert yex.util.fraction_to_str(123, 0)=="123.0"
