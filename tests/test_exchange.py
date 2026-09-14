from market import Option, OptionType
from exchange import (
    RFQ,
    Quote,
    Trade,
    FOKOrder,
    CounterpartySide,
    execute_rfq,
    execute_fok
)

def make_option():
    return Option(
        OptionType.AJAR_ABOVE_STRIKE,
        strike=50
    )

def test_counterparty_buy_hits_ask():
    option = make_option()

    rfq = RFQ(
        option=option,
        quantity=10
    )
    quote = Quote(
        bid=0.40,
        bid_size=5,
        ask=0.60,
        ask_size=7
    )
    trade = execute_rfq(
        rfq,
        quote,
        CounterpartySide.BUY
    )
    assert trade.price == 0.60
    assert trade.quantity == 7
    assert trade.market_maker_bought is False


def test_counterparty_sell_hits_bid():
    option = make_option()
    rfq = RFQ(
        option=option,
        quantity=10
    )
    quote = Quote(
        bid=0.40,
        bid_size=5,
        ask=0.60,
        ask_size=7
    )
    trade = execute_rfq(
        rfq,
        quote,
        CounterpartySide.SELL
    )
    assert trade.price == 0.40
    assert trade.quantity == 5
    assert trade.market_maker_bought is True

def test_rejected_fok_produces_no_trade():
    option = make_option()
    fok = FOKOrder(
        option=option,
        price=0.40,
        quantity=10,
        counterparty_side=CounterpartySide.SELL
    )
    trade = execute_fok(fok, accepted=False)
    assert trade is None

def test_accepted_fok_executes_full_quantity():
    option = make_option()
    fok = FOKOrder(
        option=option,
        price=0.40,
        quantity=10,
        counterparty_side=CounterpartySide.SELL
    )
    trade = execute_fok(fok, accepted=True)
    assert trade.price == 0.40
    assert trade.quantity == 10
    assert trade.market_maker_bought is True