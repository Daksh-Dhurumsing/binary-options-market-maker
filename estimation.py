from market import MarketHistory, MarketParameters


def estimate_market_parameters(history: MarketHistory) -> MarketParameters:
    import numpy as np
    ajar = np.array(history.ajar_values)
    theriodic = np.array(history.theriodic_values)
    return MarketParameters(
        ajar_mean=float(np.mean(ajar)),
        ajar_std=float(np.std(ajar)),
        theriodic_mean=float(np.mean(theriodic)),
        theriodic_std=float(np.std(theriodic)),
        correlation=float(np.corrcoef(ajar, theriodic)[0, 1])
    )

