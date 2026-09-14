import pytest
from market import MarketParameters, Option, OptionType
from exchange import RFQ, Trade, FOKOrder, CounterpartySide
from bots import MarketMaker

def make_params():
    return MarketParameters(
        ajar_mean=50,
        ajar_std=10,
        theriodic_mean=100,
        theriodic_std=5,
        correlation=0.5
    )

def make_option():
    return Option(
        OptionType.AJAR_ABOVE_STRIKE,
        strike=50
    )

def make_market_maker(inventory_skew=0.0005):
    return MarketMaker(
        params=make_params(),
        half_spread=0.05,
        inventory_skew=inventory_skew,
        max_position=20,
        starting_capital=100
    )

def test_buy_trade_updates_cash_and_position():
    maker = make_market_maker()
    option = make_option()
    trade = Trade(
        option=option,
        price=0.40,
        quantity=10,
        market_maker_bought=True
    )
    maker.process_trade(trade)
    assert maker.cash == pytest.approx(-4.0)
    assert maker.positions[option] == 10
def test_sell_trade_updates_cash_and_position():
    maker = make_market_maker()
    option = make_option()
    trade = Trade(
        option=option,
        price=0.60,
        quantity=10,
        market_maker_bought=False
    )
    maker.process_trade(trade)
    assert maker.cash == pytest.approx(6.0)
    assert maker.positions[option] == -10

def test_round_trip_releases_capital():
    maker = make_market_maker()
    option = make_option()
    buy_trade = Trade(
        option=option,
        price=0.40,
        quantity=10,
        market_maker_bought=True
    )
    sell_trade = Trade(
        option=option,
        price=0.60,
        quantity=10,
        market_maker_bought=False
    )
    maker.process_trade(buy_trade)
    maker.process_trade(sell_trade)
    assert maker.positions[option] == 0
    assert maker.cash == pytest.approx(2.0)
    assert maker.available_capital() == pytest.approx(102.0)

def test_winning_long_option_settlement():
    maker = make_market_maker()
    option = make_option()
    trade = Trade(
        option=option,
        price=0.40,
        quantity=10,
        market_maker_bought=True
    )
    maker.process_trade(trade)
    maker.settle(
        ajar_final=60,
        theriodic_final=100
    )
    assert maker.cash == pytest.approx(6.0)
    assert maker.positions == {}

def test_long_inventory_moves_quotes_down():
    maker = make_market_maker(
        inventory_skew=0.0005
    )
    option = make_option()
    rfq = RFQ(
        option=option,
        quantity=5
    )
    initial_quote = maker.quote(rfq)
    trade = Trade(
        option=option,
        price=0.40,
        quantity=10,
        market_maker_bought=True
    )
    maker.process_trade(trade)
    new_quote = maker.quote(rfq)
    assert new_quote.bid < initial_quote.bid
    assert new_quote.ask < initial_quote.ask

def test_accepts_favourable_counterparty_sell_fok():
    maker = make_market_maker(inventory_skew=0)
    option = make_option()
    fok = FOKOrder(
        option=option,
        price=0.40,
        quantity=10,
        counterparty_side=CounterpartySide.SELL
    )
    assert maker.respond_to_fok(fok) is True

def test_rejects_unfavourable_counterparty_sell_fok():
    maker = make_market_maker(inventory_skew=0)
    option = make_option()
    fok = FOKOrder(
        option=option,
        price=0.50,
        quantity=10,
        counterparty_side=CounterpartySide.SELL
    )
    assert maker.respond_to_fok(fok) is False

def test_accepts_favourable_counterparty_buy_fok():
    maker = make_market_maker(inventory_skew=0)
    option = make_option()
    fok = FOKOrder(
        option=option,
        price=0.60,
        quantity=10,
        counterparty_side=CounterpartySide.BUY
    )
    assert maker.respond_to_fok(fok) is True

def test_rejects_unfavourable_counterparty_buy_fok():
    maker = make_market_maker(inventory_skew=0)
    option = make_option()
    fok = FOKOrder(
        option=option,
        price=0.50,
        quantity=10,
        counterparty_side=CounterpartySide.BUY
    )
    assert maker.respond_to_fok(fok) is False

def test_fok_rejected_if_full_quantity_breaks_position_limit():
    maker = make_market_maker(inventory_skew=0)
    option = make_option()
    trade = Trade(
        option=option,
        price=0.40,
        quantity=15,
        market_maker_bought=True
    )
    maker.process_trade(trade)
    fok = FOKOrder(
        option=option,
        price=0.40,
        quantity=10,
        counterparty_side=CounterpartySide.SELL
    )
    assert maker.respond_to_fok(fok) is False

def test_fok_rejected_if_insufficient_capital():
    maker = MarketMaker(
        params=make_params(),
        half_spread=0.05,
        inventory_skew=0,
        max_position=1000,
        starting_capital=1
    )
    option = make_option()
    fok = FOKOrder(
        option=option,
        price=0.40,
        quantity=10,
        counterparty_side=CounterpartySide.SELL
    )
    assert maker.respond_to_fok(fok) is False
