import pytest
from market import Option, OptionType, MarketParameters
from pricing import price_option_from_parameters

def make_params():
    return MarketParameters(
        ajar_mean=50,
        ajar_std=10,
        theriodic_mean=100,
        theriodic_std=5,
        correlation=0.5
    )

def test_ajar_option_at_mean_is_half():
    params = make_params()
    option = Option(
        OptionType.AJAR_ABOVE_STRIKE,
        strike=50
    )
    price = price_option_from_parameters(option, params)
    assert price == pytest.approx(0.5)

def test_theriodic_option_at_mean_is_half():
    params = make_params()
    option = Option(
        OptionType.THERIODIC_ABOVE_STRIKE,
        strike=100
    )
    price = price_option_from_parameters(option, params)
    assert price == pytest.approx(0.5)

def test_comparison_option_equal_means_is_half():
    params = MarketParameters(
        ajar_mean=50,
        ajar_std=10,
        theriodic_mean=50,
        theriodic_std=5,
        correlation=0.3
    )
    option = Option(
        OptionType.AJAR_ABOVE_THERIODIC
    )
    price = price_option_from_parameters(option, params)
    assert price == pytest.approx(0.5)

def test_ajar_above_strike():
    option = Option(
        option_type=OptionType.AJAR_ABOVE_STRIKE,
        strike=50
    )
    assert option.payoff(60, 100) == 1.0
    assert option.payoff(40, 100) == 0.0
    assert option.payoff(50, 100) == 0.0


def test_theriodic_above_strike():
    option = Option(
        option_type=OptionType.THERIODIC_ABOVE_STRIKE,
        strike=50
    )
    assert option.payoff(100, 60) == 1.0
    assert option.payoff(100, 40) == 0.0
    assert option.payoff(100, 50) == 0.0

def test_ajar_above_theriodic():
    option = Option(
        option_type=OptionType.AJAR_ABOVE_THERIODIC,
    )
    assert option.payoff(100, 60) == 1.0
    assert option.payoff(60, 100) == 0.0
    assert option.payoff(100, 100) == 0.0

