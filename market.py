from dataclasses import dataclass
from enum import Enum


@dataclass
class MarketParameters:
    ajar_mean: float
    ajar_std: float

    theriodic_mean: float
    theriodic_std: float

    correlation: float
    def __post_init__(self):
        if self.ajar_std <= 0:
            raise ValueError("Ajar std must be greater than 0")
        if self.theriodic_std <= 0:
            raise ValueError("Theriodic std must be greater than 0")
        if not -1 <= self.correlation <= 1:
            raise ValueError("Correlation must be between -1 and 1")

class OptionType(Enum):
    AJAR_ABOVE_STRIKE = 'ajar_above_strike'
    THERIODIC_ABOVE_STRIKE = 'theriodic_above_strike'
    AJAR_ABOVE_THERIODIC = 'ajar_above_theriodic'

@dataclass(frozen=True)
class Option:
    option_type: OptionType
    strike: float | None = None
    def __post_init__(self):
        if self.option_type in (
                OptionType.AJAR_ABOVE_STRIKE,
                OptionType.THERIODIC_ABOVE_STRIKE
        ):
            if self.strike is None:
                raise ValueError("Strike must be provided")
    def payoff(self, ajar_final: float, theriodic_final: float) -> float:
        if self.option_type == OptionType.AJAR_ABOVE_STRIKE:
            return float(self.strike < ajar_final)
        if self.option_type == OptionType.THERIODIC_ABOVE_STRIKE:
            return float(self.strike < theriodic_final)
        if self.option_type == OptionType.AJAR_ABOVE_THERIODIC:
            return float(theriodic_final < ajar_final)
        raise ValueError('Invalid option type')

@dataclass
class MarketHistory:
    ajar_values: list[float]
    theriodic_values: list[float]
    def __post_init__(self):
        if len(self.ajar_values) != len(self.theriodic_values):
            raise ValueError("Ajar and theriodic values must be the same length")
        if len(self.ajar_values) == 0:
            raise ValueError("Market history cannot be empty")
