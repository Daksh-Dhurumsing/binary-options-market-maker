from market import MarketParameters, Option, OptionType
from statistics import NormalDist

def price_option_from_parameters(
        option: Option,
        params: MarketParameters
) -> float:
    if option.option_type == OptionType.AJAR_ABOVE_STRIKE:
        z = (option.strike - params.ajar_mean) / params.ajar_std
        return 1 - NormalDist().cdf(z)
    if option.option_type == OptionType.THERIODIC_ABOVE_STRIKE:
        z = (option.strike - params.theriodic_mean) / params.theriodic_std
        return 1 - NormalDist().cdf(z)
    if option.option_type == OptionType.AJAR_ABOVE_THERIODIC:
        mean_difference = params.ajar_mean - params.theriodic_mean
        variance_difference = (params.theriodic_std)**2 + (params.ajar_std)**2 - 2*params.correlation*params.ajar_std*params.theriodic_std
        std_difference = (variance_difference)**0.5
        z = (0 - mean_difference) / std_difference
        return 1 - NormalDist().cdf(z)
    raise ValueError("Unsupported option type")







