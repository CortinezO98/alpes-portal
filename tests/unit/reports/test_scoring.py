import pytest

from apps.reports.services.scoring import get_score_band


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "red"),
        (5.9, "red"),
        (5.99, "red"),
        (6, "yellow"),
        (7.9, "yellow"),
        (7.99, "yellow"),
        (8, "green"),
        (10, "green"),
    ],
)
def test_score_band_boundaries(score, expected):
    assert get_score_band(score).code == expected


def test_score_band_none_is_unclassified():
    assert get_score_band(None) is None


@pytest.mark.parametrize("score", [-0.1, 10.1])
def test_score_band_rejects_out_of_range_values(score):
    with pytest.raises(ValueError):
        get_score_band(score)
