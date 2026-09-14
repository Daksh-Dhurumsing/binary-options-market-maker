from market import MarketParameters
from simulator import run_simple_day, SimulationResult

def test_simple_day_runs():
    params = MarketParameters(
        ajar_mean=50,
        ajar_std=10,
        theriodic_mean=100,
        theriodic_std=5,
        correlation=0.5
    )
    result = run_simple_day(
        true_params=params,
        n_history=100,
        n_orders=10,
        half_spread=0.05,
        inventory_skew=0.0005,
        seed=42
    )
    assert isinstance(result, SimulationResult)
    assert isinstance(result.our_pnl, float)
    assert isinstance(result.competitor_pnl, float)

def test_simple_day_runs_with_only_foks():
    params = MarketParameters(
        ajar_mean=50,
        ajar_std=10,
        theriodic_mean=100,
        theriodic_std=5,
        correlation=0.5
    )
    result = run_simple_day(
        true_params=params,
        n_history=100,
        n_orders=20,
        half_spread=0.05,
        inventory_skew=0.0005,
        seed=42,
        fok_probability=1.0
    )
    assert isinstance(result, SimulationResult)
    assert isinstance(result.our_pnl, float)
    assert isinstance(result.competitor_pnl, float)