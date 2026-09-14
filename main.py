from market import MarketParameters
from simulator import run_simple_day

def main():
    # True parameters used by the simulated market
    true_params = MarketParameters(
        ajar_mean=50,
        ajar_std=10,
        theriodic_mean=100,
        theriodic_std=5,
        correlation=0.5
    )
    # Run one simulated trading day
    result = run_simple_day(
        true_params=true_params,
        n_history=1000,
        n_orders=100,
        half_spread=0.05,
        inventory_skew=0.0005,
        informed_probability=0.25,
        fok_probability=0.20,
        seed=42
    )
    print("=== Binary Options Market-Making Simulation ===")
    print()
    print(f"Our P&L:                  {result.our_pnl:.2f}")
    print(f"Competitor P&L:           {result.competitor_pnl:.2f}")
    print()
    print(f"Our informed trades:      {result.our_informed_trade_count}")
    print(f"Our uninformed trades:    {result.our_uninformed_trade_count}")
    print()
    print(
        f"Our peak gross inventory: "
        f"{result.our_peak_gross_inventory}"
    )
    print(
        f"Competitor peak inventory: "
        f"{result.competitor_peak_gross_inventory}"
    )

if __name__ == "__main__":
    main()

