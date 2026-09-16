from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreBand:
    code: str
    label: str
    minimum: float
    maximum: float
    color: str


SCORE_BANDS = (
    ScoreBand("red", "Rojo", 0.0, 5.9, "#D64545"),
    ScoreBand("yellow", "Amarillo", 6.0, 7.9, "#D9A404"),
    ScoreBand("green", "Verde", 8.0, 10.0, "#2E8B57"),
)


def get_score_band(score: float | int | None) -> ScoreBand | None:
    if score is None:
        return None

    value = float(score)
    for band in SCORE_BANDS:
        if band.minimum <= value <= band.maximum:
            return band

    if 5.9 < value < 6.0:
        return SCORE_BANDS[0]
    if 7.9 < value < 8.0:
        return SCORE_BANDS[1]
    raise ValueError("El puntaje debe estar entre 0 y 10.")
