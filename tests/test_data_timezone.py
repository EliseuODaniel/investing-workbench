import pandas as pd

from src.data import _normalize_required_columns


def test_normalize_required_columns_removes_timezone_from_index():
    index = pd.date_range("2024-01-01", periods=2, freq="D", tz="UTC")
    df = pd.DataFrame(
        {
            "Open": [1.0, 2.0],
            "High": [1.0, 2.0],
            "Low": [1.0, 2.0],
            "Close": [1.0, 2.0],
            "Volume": [10.0, 20.0],
        },
        index=index,
    )
    normalized = _normalize_required_columns(df)

    assert normalized.index.tz is None
