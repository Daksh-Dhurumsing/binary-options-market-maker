from market import MarketParameters, Option
from exchange import RFQ, Quote, Trade, FOKOrder, CounterpartySide
from pricing import price_option_from_parameters


class MarketMaker:
    def __init__(self, params: MarketParameters, half_spread: float, inventory_skew: float, max_position: int, starting_capital: float):
        self.params = params
        self.half_spread = half_spread
        self.inventory_skew = inventory_skew
        self.cash = 0.0
        self.max_position = max_position
        self.positions: dict[Option, int] = {}
        self.starting_capital = starting_capital
        self.peak_gross_inventory = 0
        if max_position <= 0:
            raise ValueError("max_position must be > 0")
        if inventory_skew < 0:
            raise ValueError("Inventory skew must be non-negative")
        if half_spread < 0:
            raise ValueError("Half spread must be non-negative")
        if starting_capital <= 0:
            raise ValueError("Starting capital must be > 0")
    def required_capital(self, trade: Trade) -> float:
        if trade.market_maker_bought:
            return trade.quantity*trade.price
        else:
            return trade.quantity*(1-trade.price)
    def worst_case_equity(self) -> float:
        worst_case_settlement = sum(
            min(position, 0) for position in self.positions.values()
        )
        return (
            self.starting_capital
            + self.cash
            + worst_case_settlement
        )
    def available_capital(self) -> float:
        return max(0.0, self.worst_case_equity())
    def quote(self, rfq: RFQ) -> Quote:
        fair_value = price_option_from_parameters(rfq.option, self.params)
        position = self.positions.get(rfq.option, 0)
        max_bid_size = self.max_position - position
        max_ask_size = self.max_position + position
        reservation_price = fair_value-(self.inventory_skew*position)
        bid = min(1,max(reservation_price-self.half_spread, 0))
        ask = min(1,max(reservation_price+self.half_spread, 0))
        available = self.available_capital()
        if bid > 0:
            capital_bid_size = int(available / bid)
        else:
            capital_bid_size = rfq.quantity
        capital_per_ask = 1-ask
        if capital_per_ask > 0:
            capital_ask_size = int(available / capital_per_ask)
        else:
            capital_ask_size = rfq.quantity
        bid_size = max(0, min(rfq.quantity, max_bid_size, capital_bid_size))
        ask_size = max(0, min(rfq.quantity, max_ask_size, capital_ask_size))
        return Quote(bid=bid, bid_size=bid_size, ask=ask, ask_size=ask_size)
    def process_trade(self, trade: Trade) -> None:
        if self.projected_worst_case_equity(trade) < 0:
            raise ValueError("Insufficient capital for trade")
        capital_needed = self.required_capital(trade)
        if capital_needed > self.available_capital():
            raise ValueError("Insufficient capital for trade")

        current_position = self.positions.get(trade.option, 0)
        if trade.market_maker_bought:
            new_position = current_position + trade.quantity
        else:
            new_position = current_position - trade.quantity
        if abs(new_position) > self.max_position:
            raise ValueError("Trade would exceed position limit")

        current_position = self.positions.get(trade.option, 0)
        if not trade.market_maker_bought:
            self.cash += trade.price*trade.quantity
            self.positions[trade.option] = current_position - trade.quantity
        else:
            self.cash -= trade.price*trade.quantity
            self.positions[trade.option] = current_position + trade.quantity
        total_abs_position = sum(abs(position) for position in self.positions.values())
        self.peak_gross_inventory = max(self.peak_gross_inventory, total_abs_position)
    def settle(
            self,
            ajar_final: float,
            theriodic_final: float
    ) -> None:
        for option, position in self.positions.items():
            payoff = option.payoff(ajar_final, theriodic_final)
            self.cash += payoff*position
        self.positions.clear()

    def projected_worst_case_equity(self, trade: Trade) -> float:
        current_position = self.positions.get(trade.option, 0)
        if trade.market_maker_bought:
            projected_cash = self.cash - trade.price * trade.quantity
            projected_position = current_position + trade.quantity
        else:
            projected_cash = self.cash + trade.price * trade.quantity
            projected_position = current_position - trade.quantity

        worst_case_settlement = 0

        for option, position in self.positions.items():
            if option != trade.option:
                worst_case_settlement += min(position, 0)
        worst_case_settlement += min(projected_position, 0)
        return (self.starting_capital + projected_cash + worst_case_settlement)

    def respond_to_fok(self, fok: FOKOrder) -> bool:
        fair_value = price_option_from_parameters(fok.option, self.params)
        position = self.positions.get(fok.option, 0)
        max_bid_size = self.max_position - position
        max_ask_size = self.max_position + position
        reservation_price = fair_value - (self.inventory_skew * position)
        acceptable_bid = min(1,max(reservation_price-self.half_spread, 0))
        acceptable_ask = min(1,max(reservation_price+self.half_spread, 0))

        if fok.counterparty_side == CounterpartySide.SELL:
            capital_needed = fok.quantity * fok.price
        elif fok.counterparty_side == CounterpartySide.BUY:
            capital_needed = fok.quantity * (1 - fok.price)
        if capital_needed > self.available_capital():
            return False

        if fok.counterparty_side == CounterpartySide.SELL:
            if max_bid_size < fok.quantity or fok.price > acceptable_bid:
                return False
            else:
                return True
        elif fok.counterparty_side == CounterpartySide.BUY:
            if max_ask_size < fok.quantity or fok.price < acceptable_ask:
                return False
            else:
                return True
        else:
            raise ValueError("Invalid counterparty side")
    def equity(self) -> float:
        return self.starting_capital + self.cash
    def is_bankrupt(self) -> bool:
        return self.equity() < 0


















