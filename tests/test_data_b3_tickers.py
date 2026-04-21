from src.data import _candidate_symbols


def test_candidate_symbols_adds_sa_suffix_for_b3_equities():
    assert _candidate_symbols('PETR4') == ['PETR4.SA', 'PETR4']
    assert _candidate_symbols('VALE3') == ['VALE3.SA', 'VALE3']
    assert _candidate_symbols('CMIG4') == ['CMIG4.SA', 'CMIG4']


def test_candidate_symbols_prefers_sa_for_wege3_alias():
    assert _candidate_symbols('WEGE3') == ['WEGE3.SA', 'WEGE3']
