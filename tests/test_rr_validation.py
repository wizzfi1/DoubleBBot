# tests/test_rr_validation.py

def rr(entry, sl, tp):
    return abs(tp - entry) / abs(entry - sl)


def test_rr_below_minimum():
    entry = 1.2000
    sl = 1.1995
    tp = 1.2008

    assert rr(entry, sl, tp) < 5


def test_rr_exact_minimum():
    entry = 1.2000
    sl = 1.1990
    tp = 1.2050

    assert rr(entry, sl, tp) >= 5
