from dataclasses import dataclass
from market import Option
from enum import Enum
@dataclass
class RFQ:
    option: Option
    quantity: int
    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

@dataclass
class Quote:
    bid:float
    bid_size: int
    ask: float
    ask_size: int
    def __post_init__(self):
        if not 0 <= self.bid <= 1:
            raise ValueError("Bid must be between 0 and 1")
        if not 0 <= self.ask <= 1:
            raise ValueError("Ask must be between 0 and 1")
        if self.bid > self.ask:
            raise ValueError("Bid must be less than or equal to ask")
        if self.bid_size < 0 or self.ask_size < 0:
            raise ValueError("Quote sizes must be non-negative")

class CounterpartySide(Enum):
    BUY = ("buy")
    SELL = ("sell")
@dataclass
class Trade:
    option: Option
    price: float
    quantity: int
    market_maker_bought: bool
def execute_rfq(
        rfq: RFQ,
        quote: Quote,
        counterparty_side: CounterpartySide
) -> Trade | None:
    if counterparty_side == CounterpartySide.BUY:
        price = quote.ask
        quantity = min(rfq.quantity, quote.ask_size)
        market_maker_bought = False
    elif counterparty_side == CounterpartySide.SELL:
        price = quote.bid
        quantity = min(rfq.quantity, quote.bid_size)
        market_maker_bought = True
    else:
        raise ValueError("Invalid counterparty side")
    if quantity == 0:
        return None
    else:
        return Trade(
            option=rfq.option,
            price=price,
            quantity=quantity,
            market_maker_bought=market_maker_bought
        )
@dataclass
class FOKOrder:
    option: Option
    price: float
    quantity: int
    counterparty_side: CounterpartySide
    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if not (0<=self.price<=1):
            raise ValueError("Price must be between 0 and 1")
def execute_fok(fok: FOKOrder, accepted: bool) -> Trade | None:
    if not accepted:
        return None
    if fok.counterparty_side == CounterpartySide.SELL:
        market_maker_bought = True
    elif fok.counterparty_side == CounterpartySide.BUY:
        market_maker_bought = False
    else:
        raise ValueError("Invalid counterparty side")
    return Trade(
        option=fok.option,
        price=fok.price,
        quantity=fok.quantity,
        market_maker_bought=market_maker_bought
    )