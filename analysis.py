import matplotlib.pyplot as plt
from pyparsing import results

from simulator import run_simple_day
from market import MarketParameters
import numpy as np
def run_inventory_skew_experiment(
    params,
    skews,
    n_simulations=2000
):
    results = []
    for skew in skews:
        our_pnls = []
        competitor_pnls = []
        our_peak_inventories = []
        for seed in range(n_simulations):
            result = run_simple_day(
                true_params=params,
                n_history=1000,
                n_orders=100,
                half_spread=0.05,
                inventory_skew=skew,
                seed=seed
            )
            our_pnls.append(result.our_pnl)
            competitor_pnls.append(result.competitor_pnl)
            our_peak_inventories.append(result.our_peak_gross_inventory)
        inventory_error = (1.96 * np.std(our_peak_inventories, ddof=1) / np.sqrt(len(our_peak_inventories)))
        results.append({
            "skew": skew,
            "mean_pnl": sum(our_pnls) / len(our_pnls),
            "competitor_mean_pnl": sum(competitor_pnls) / len(competitor_pnls),
            "win_rate": sum(ours > competitor for ours, competitor in zip(our_pnls, competitor_pnls)) / len(our_pnls),
            "peak_inventory": sum(our_peak_inventories) / len(our_peak_inventories),
            "inventory_error": inventory_error
        })

    return results

def run_half_spread_experiment(
    params,
    spreads,
    n_simulations=2000
):
    results = []
    for spread in spreads:
        our_pnls = []
        competitor_pnls = []
        our_peak_inventories = []
        competitor_peak_inventories = []
        for seed in range(2000):
            result = run_simple_day(
                true_params=params,
                n_history=1000,
                n_orders=100,
                half_spread=spread,
                inventory_skew=0.0005,
                seed=seed
            )
            our_pnls.append(result.our_pnl)
            competitor_pnls.append(result.competitor_pnl)
            our_peak_inventories.append(result.our_peak_gross_inventory)
        standard_error = (np.std(our_pnls, ddof=1) / np.sqrt(len(our_pnls)))
        confidence_interval = 1.96 * standard_error
        results.append({
            "half_spread": spread,
            "mean_pnl": sum(our_pnls) / len(our_pnls),
            "pnl_error": confidence_interval,
            "competitor_mean_pnl":
                sum(competitor_pnls) / len(competitor_pnls),
            "win_rate": sum(ours > competitor for ours, competitor in zip(our_pnls, competitor_pnls)) / len(
                our_pnls),
            "peak_inventory":
                sum(our_peak_inventories) / len(our_peak_inventories)
        })
    return results

def monte_carlo_simulation(
        params,
        n_simulations=5000,
        half_spread=0.05,
        inventory_skew=0.0005
):
    our_pnls = []
    competitor_pnls = []
    peak_inventories = []
    wins = 0
    losses = 0
    for seed in range(n_simulations):
        result = run_simple_day(
            true_params=params,
            n_history=1000,
            n_orders=100,
            half_spread=half_spread,
            inventory_skew=inventory_skew,
            seed=seed
        )
        our_pnls.append(result.our_pnl)
        competitor_pnls.append(result.competitor_pnl)

        peak_inventories.append(
            result.our_peak_gross_inventory
        )
        if result.our_pnl > result.competitor_pnl:
            wins += 1
        if result.our_pnl < 0:
            losses += 1

    cumulative_mean = (np.cumsum(our_pnls) / np.arange(1, len(our_pnls) + 1))
    mean_pnl = sum(our_pnls) / n_simulations
    win_rate = wins / n_simulations
    loss_rate = losses / n_simulations
    mean_peak_inventory = (sum(peak_inventories) / n_simulations)

    return {
        "mean_pnl": mean_pnl,
        "win_rate": win_rate,
        "loss_rate": loss_rate,
        "mean_peak_inventory": mean_peak_inventory,
        "our_pnls": our_pnls,
        "competitor_pnls": competitor_pnls,
        "cumulative_mean": cumulative_mean
    }

def plot_inventory_skew_pnl(results):
    skews = [r["skew"] for r in results]
    pnls = [r["mean_pnl"] for r in results]
    errors = [r["inventory_error"] for r in results]
    plt.figure()
    plt.scatter(skews, pnls, label="Monte Carlo estimates")
    plt.errorbar(
        skews,
        pnls,
        yerr=errors,
        fmt="o",
        capsize=4,
        label="Monte Carlo estimates"
    )
    plt.plot(skews, pnls, alpha = 0.6)
    plt.xlabel("Inventory skew")
    plt.ylabel("Mean P&L")
    plt.title("Inventory Skew vs Mean P&L")
    plt.tight_layout()
    plt.savefig("figures/inventory_skew_pnl.png")
    plt.close()

def plot_inventory_skew_exposure(results):
    skews = [r["skew"] for r in results]
    inventories = [r["peak_inventory"] for r in results]
    errors = [r["inventory_error"] for r in results]
    plt.figure()
    plt.scatter(skews, inventories, label="Monte Carlo estimates")
    plt.errorbar(
        skews,
        inventories,
        yerr=errors,
        fmt="o",
        capsize=4,
        label="Monte Carlo estimates"
    )
    plt.plot(skews, inventories, alpha = 0.6)
    plt.xlabel("Inventory skew")
    plt.ylabel("Average daily peak gross inventory")
    plt.title("Inventory Skew vs Inventory Exposure")
    plt.tight_layout()
    plt.savefig("figures/inventory_skew_exposure.png")
    plt.close()

def plot_spread_vs_PnL(results):
    spreads = [r["half_spread"] for r in results]
    pnls = [r["mean_pnl"] for r in results]
    errors = [r["pnl_error"] for r in results]
    plt.figure()
    plt.scatter(spreads, pnls, label="Monte Carlo estimates")
    plt.errorbar(
        spreads,
        pnls,
        yerr=errors,
        fmt="o",
        capsize=4,
        label="Monte Carlo estimates"
    )
    plt.plot(spreads, pnls, alpha = 0.6)
    plt.xlabel("half spread")
    plt.ylabel("Estimated mean P&L")
    plt.title("Half Spread vs Mean P&L")
    plt.tight_layout()
    plt.savefig("figures/half_spread_mean_pnl.png")
    plt.close()

def plot_monte_carlo_convergence(results):
    cumulative_mean = results["cumulative_mean"]
    plt.figure()
    plt.plot(range(1, len(cumulative_mean) + 1), cumulative_mean)
    plt.xlabel("Number of simulated trading days")
    plt.ylabel("Estimated cumulative mean P&L")
    plt.title("Monte Carlo Convergence of Mean P&L")
    plt.tight_layout()
    final_mean = cumulative_mean[-1]
    plt.axhline(
        final_mean,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Final estimate = {final_mean:.2f}"
    )
    plt.legend()
    plt.savefig("figures/monte_carlo_convergence.png")
    plt.close()

if __name__ == "__main__":
    params = MarketParameters(
        ajar_mean=50,
        ajar_std=10,
        theriodic_mean=100,
        theriodic_std=5,
        correlation=0.5
    )
    skews = np.linspace(0, 0.003, 13)
    results1 = run_inventory_skew_experiment(
        params=params,
        skews=skews,
        n_simulations=2000
    )

    plot_inventory_skew_pnl(results1)
    plot_inventory_skew_exposure(results1)

    spreads = np.linspace(0.01, 0.10, 19)
    results2 = run_half_spread_experiment(
        params=params,
        spreads=spreads,
        n_simulations=2000
    )

    plot_spread_vs_PnL(results2)

    results3 = monte_carlo_simulation(
        params=params,
        n_simulations=5000,
        half_spread=0.05,
        inventory_skew=0.0005
    )

    plot_monte_carlo_convergence(results3)

