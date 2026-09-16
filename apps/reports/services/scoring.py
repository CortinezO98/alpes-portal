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
    if not 0 <= value <= 10:
        raise ValueError("El puntaje debe estar entre 0 y 10.")
    if value < 6:
        return SCORE_BANDS[0]
    if value < 8:
        return SCORE_BANDS[1]
    return SCORE_BANDS[2]
