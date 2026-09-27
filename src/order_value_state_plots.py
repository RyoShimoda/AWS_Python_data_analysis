"""注文単位のGMV分布を顧客州別の箱ひげ図として保存する。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "order_level_sales_by_state.csv"
IMAGE_DIR = PROJECT_ROOT / "images"


def main() -> None:
    df_orders = pd.read_csv(DATA_PATH)
    state_values = df_orders.groupby("customer_state")["order_gmv"]

    # 色はGMV上位州と、注文額平均の上位州を区別するために使う。
    top_gmv_states = ["SP", "RJ", "MG", "RS", "PR"]
    top_mean_states = state_values.mean().nlargest(5).index.tolist()
    colors = dict(
        zip(
            top_gmv_states,
            sns.color_palette("Blues_r", n_colors=len(top_gmv_states)).as_hex(),
        )
    )
    colors.update(
        zip(
            top_mean_states,
            sns.color_palette("Oranges_r", n_colors=len(top_mean_states)).as_hex(),
        )
    )

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    for statistic, filename in [
        ("mean", "Order_Value_Distribution_by_State_Sorted_by_Mean.png"),
        ("median", "Order_Value_Distribution_by_State_Sorted_by_Median.png"),
    ]:
        # 並べ替えだけを変え、箱ひげ図に使う注文単位データは同じにする。
        state_order = (
            state_values.mean() if statistic == "mean" else state_values.median()
        ).sort_values(ascending=False).index.tolist()

        fig, ax = plt.subplots(figsize=(12, 7.5))
        sns.boxplot(
            data=df_orders,
            x="customer_state",
            y="order_gmv",
            order=state_order,
            hue="customer_state",
            hue_order=state_order,
            palette=[colors.get(state, "#cacdd1") for state in state_order],
            dodge=False,
            legend=False,
            showfliers=False,
            showmeans=True,
            meanprops={
                "marker": "D",
                "markerfacecolor": "white",
                "markeredgecolor": "black",
                "markeredgewidth": 1.2,
                "markersize": 6,
            },
            ax=ax,
        )
        ax.set_title(f"Order GMV by Customer State — Sorted by {statistic.title()}")
        ax.set_xlabel("Customer State")
        ax.set_ylabel("Order GMV (product prices, excluding freight)")
        ax.tick_params(axis="x", labelrotation=45)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(IMAGE_DIR / filename, dpi=160)
        plt.close(fig)


if __name__ == "__main__":
    main()
