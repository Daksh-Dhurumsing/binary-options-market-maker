import numpy as np

from estimation import estimate_market_parameters
from exchange import *
from market import *
from bots import MarketMaker
from pricing import *
from dataclasses import dataclass

def generate_market_history(
        params: MarketParameters,
        n_observations: int,
        seed: int | None = None
) -> MarketHistory:
    mean = [
        params.ajar_mean,
        params.theriodic_mean
    ]
    covariance = [
        [
            params.ajar_std ** 2,
            params.correlation * params.ajar_std * params.theriodic_std
        ],
        [
            params.correlation * params.ajar_std * params.theriodic_std,
            params.theriodic_std ** 2
        ]
    ]
    if n_observations <= 0:
        raise ValueError("n_observations must be greater than 0")

    rng = np.random.default_rng(seed)
    samples = rng.multivariate_normal(
        mean=mean,
        cov=covariance,
        size=n_observations
    )
    ajar_values = samples[:,0].tolist()
    theriodic_values = samples[:,1].tolist()
    return MarketHistory(
        ajar_values=ajar_values,
        theriodic_values=theriodic_values
    )

@dataclass
class SimulationResult:
    our_pnl: float
    competitor_pnl: float
    our_informed_trade_count: int
    our_uninformed_trade_count: int
    competitor_informed_trade_count: int
    competitor_uninformed_trade_count: int
    our_peak_gross_inventory: int
    competitor_peak_gross_inventory: int


def run_simple_day(
        true_params: MarketParameters,
        n_history: int,
        n_orders: int,
        half_spread: float,
        inventory_skew: float,
        fok_probability: float = 0.3,
        informed_probability: float = 0.25,
        seed: int | None = None
) -> SimulationResult:
    rng = np.random.default_rng(seed)
    history = generate_market_history(
        params=true_params,
        n_observations=n_history,
        seed=seed
    )
    estimated_params = estimate_market_parameters(history)

    market_maker = MarketMaker(
        params=estimated_params,
        half_spread=half_spread,
        inventory_skew=inventory_skew,
        max_position=20,
        starting_capital=100
    )
    competitor = MarketMaker(
        params=estimated_params,
        half_spread=0.05,
        inventory_skew=0.0,
        max_position=20,
        starting_capital=100
    )
    options = [
        Option(OptionType.AJAR_ABOVE_STRIKE, strike=true_params.ajar_mean - true_params.ajar_std),
        Option(OptionType.AJAR_ABOVE_STRIKE, strike=true_params.ajar_mean),
        Option(OptionType.AJAR_ABOVE_STRIKE, strike=true_params.ajar_mean + true_params.ajar_std),

        Option(OptionType.THERIODIC_ABOVE_STRIKE, strike=true_params.theriodic_mean - true_params.theriodic_std),
        Option(OptionType.THERIODIC_ABOVE_STRIKE, strike=true_params.theriodic_mean),
        Option(OptionType.THERIODIC_ABOVE_STRIKE, strike=true_params.theriodic_mean + true_params.theriodic_std),
        Option(OptionType.AJAR_ABOVE_THERIODIC)
    ]
    fok_count = 0
    fok_accepted = 0
    our_informed_trade_count = 0
    our_uninformed_trade_count = 0
    competitor_informed_trade_count = 0
    competitor_uninformed_trade_count = 0
    for _ in range(n_orders):
        option = rng.choice(options)
        true_value = price_option_from_parameters(
            option,
            true_params
        )
        is_fok = rng.random() < fok_probability
        if not is_fok:
            rfq = RFQ(option=option, quantity=10)
            our_quote = market_maker.quote(rfq)
            competitor_quote = competitor.quote(rfq)
            if rng.random() < informed_probability:
                side = informed_counterparty_side(
                    our_quote=our_quote,
                    competitor_quote=competitor_quote,
                    true_value=true_value
                )
                if side is not None:
                    winner = choose_rfq_winner(
                        our_quote=our_quote,
                        competitor_quote=competitor_quote,
                        side=side,
                        rng=rng
                    )
                    if winner == 'ours':
                        trade = execute_rfq(rfq, our_quote, side)
                        if trade is not None:
                            market_maker.process_trade(trade)
                            our_informed_trade_count += 1
                    elif winner == 'competitor':
                        trade = execute_rfq(rfq, competitor_quote, side)
                        if trade is not None:
                            competitor.process_trade(trade)
                            competitor_informed_trade_count += 1
            else:
                side = rng.choice([
                    CounterpartySide.BUY,
                    CounterpartySide.SELL
                ])
                winner = choose_rfq_winner(
                    our_quote=our_quote,
                    competitor_quote=competitor_quote,
                    side=side,
                    rng=rng
                )
                customer_value = float(np.clip(true_value + rng.normal(0.005), 0, 1))
                asks = []
                if our_quote.ask_size > 0:
                    asks.append(our_quote.ask)
                if competitor_quote.ask_size > 0:
                    asks.append(competitor_quote.ask)
                bids = []
                if our_quote.bid_size > 0:
                    bids.append(our_quote.bid)
                if competitor_quote.bid_size > 0:
                    bids.append(competitor_quote.bid)
                best_ask = min(asks) if asks else None
                best_bid = max(bids) if bids else None
                if side == CounterpartySide.BUY:
                    if best_ask is not None and best_ask <= customer_value:
                        if winner == 'ours':
                            trade = execute_rfq(rfq, our_quote, side)
                            if trade is not None:
                                market_maker.process_trade(trade)
                                our_uninformed_trade_count += 1
                        elif winner == 'competitor':
                            trade = execute_rfq(rfq, competitor_quote, side)
                            if trade is not None:
                                competitor.process_trade(trade)
                                competitor_uninformed_trade_count += 1
                if side == CounterpartySide.SELL:
                    if best_bid is not None and best_bid >= customer_value:
                        if winner == 'ours':
                            trade = execute_rfq(rfq, our_quote, side)
                            if trade is not None:
                                market_maker.process_trade(trade)
                                our_uninformed_trade_count += 1
                        elif winner == 'competitor':
                            trade = execute_rfq(rfq, competitor_quote, side)
                            if trade is not None:
                                competitor.process_trade(trade)
                                competitor_uninformed_trade_count += 1
        else:
            counterparty_side = rng.choice([
                CounterpartySide.BUY,
                CounterpartySide.SELL
            ])
            fok_count += 1
            true_value = price_option_from_parameters(
                option,
                true_params
            )
            fok_price = float(
                np.clip(
                    true_value + rng.normal(0, 0.08),
                    0,
                    1
                )
            )
            fok = FOKOrder(
                option=option,
                price=fok_price,
                quantity=10,
                counterparty_side=counterparty_side
            )

            our_accept = market_maker.respond_to_fok(fok)
            competitor_accept = competitor.respond_to_fok(fok)
            if our_accept and competitor_accept:
                winner = rng.choice(["ours", "competitor"])
            elif our_accept:
                winner = "ours"
            elif competitor_accept:
                winner = "competitor"
            else:
                winner = None
            if winner == "ours":
                trade = execute_fok(fok, accepted=True)
                market_maker.process_trade(trade)

            elif winner == "competitor":
                trade = execute_fok(fok, accepted=True)
                competitor.process_trade(trade)

    mean = [
        true_params.ajar_mean,
        true_params.theriodic_mean
    ]

    covariance = [
        [
            true_params.ajar_std ** 2,
            true_params.correlation
            * true_params.ajar_std
            * true_params.theriodic_std
        ],
        [
            true_params.correlation
            * true_params.ajar_std
            * true_params.theriodic_std,
            true_params.theriodic_std ** 2
        ]
    ]
    final_values = rng.multivariate_normal(
        mean=mean,
        cov=covariance
    )
    market_maker.settle(
        ajar_final=float(final_values[0]),
        theriodic_final=float(final_values[1])
    )
    competitor.settle(
        ajar_final=float(final_values[0]),
        theriodic_final=float(final_values[1])
    )
    if market_maker.is_bankrupt():
        print('Bankrupt')
    return SimulationResult(
        our_pnl=market_maker.cash,
        competitor_pnl=competitor.cash,
        our_informed_trade_count=our_informed_trade_count,
        our_uninformed_trade_count=our_uninformed_trade_count,
        competitor_informed_trade_count=competitor_informed_trade_count,
        competitor_uninformed_trade_count=competitor_uninformed_trade_count,
        our_peak_gross_inventory=market_maker.peak_gross_inventory,
        competitor_peak_gross_inventory=competitor.peak_gross_inventory
    )


def informed_counterparty_side(
        our_quote: Quote,
        competitor_quote: Quote,
        true_value: float
) -> CounterpartySide | None:
    asks = []
    if our_quote.ask_size > 0:
        asks.append(our_quote.ask)
    if competitor_quote.ask_size > 0:
        asks.append(competitor_quote.ask)
    bids = []
    if our_quote.bid_size > 0:
        bids.append(our_quote.bid)
    if competitor_quote.bid_size > 0:
        bids.append(competitor_quote.bid)
    best_ask = min(asks) if asks else None
    best_bid = max(bids) if bids else None
    buy_edge = true_value - best_ask if best_ask else 0
    sell_edge = true_value + best_bid if best_bid else 0
    if buy_edge <= 0 and sell_edge <= 0:
        return None
    if buy_edge > sell_edge:
        return CounterpartySide.BUY
    if sell_edge > buy_edge:
        return CounterpartySide.SELL
    return CounterpartySide.BUY

def choose_rfq_winner(
        our_quote: Quote,
        competitor_quote: Quote,
        side: CounterpartySide,
        rng
) -> str | None:
    if side == CounterpartySide.BUY:
        if our_quote.ask_size == 0 and competitor_quote.ask_size == 0:
            return None
        if our_quote.ask_size == 0:
            return 'competitor'
        if competitor_quote.ask_size == 0:
            return 'ours'
        if competitor_quote.ask < our_quote.ask:
            return 'competitor'
        if our_quote.ask < competitor_quote.ask:
            return 'ours'
        return rng.choice(['ours','competitor'])
    if side == CounterpartySide.SELL:
        if our_quote.bid_size == 0 and competitor_quote.bid_size == 0:
            return None
        if our_quote.bid_size == 0:
            return 'competitor'
        if competitor_quote.bid_size == 0:
            return 'ours'
        if competitor_quote.bid > our_quote.bid:
            return 'competitor'
        if our_quote.bid > competitor_quote.bid:
            return 'ours'
        return rng.choice(['ours','competitor'])










