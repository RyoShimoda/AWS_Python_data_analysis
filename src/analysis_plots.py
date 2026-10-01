"""複数Notebookで使う図の描画処理。集計表はNotebook側で確認する。"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

from .sales_metrics import SEASON_NAMES


STATE_COLORS = {"SP": "#0072B2", "PB": "#D55E00", "AP": "#009E73"}
STATE_STYLES = {"SP": "-", "PB": "--", "AP": ":"}
STATE_MARKERS = {"SP": "o", "PB": "s", "AP": "^"}
CATEGORY_STYLES = {
    "bed_bath_table": "-", "health_beauty": "--",
    "watches_gifts": ":", "computers_accessories": "-.",
}
CATEGORY_MARKERS = {
    "bed_bath_table": "o", "health_beauty": "s",
    "watches_gifts": "^", "computers_accessories": "D",
}


def _finish(fig, image_path=None, show=True):
    fig.tight_layout()
    if image_path is not None:
        fig.savefig(image_path, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    return fig


def plot_review_boxplot(data, value_col, title, ylabel, ylim=None, reference_line=None):
    """レビュー点数別の箱ひげ図。外れ値は集計に残して描画だけ省く。"""
    scores = sorted(data["review_score"].dropna().unique())
    palette = dict(zip(scores, sns.color_palette("Blues", n_colors=len(scores))))
    if ylim is None:
        whiskers = []
        for score in scores:
            values = data.loc[data["review_score"] == score, value_col].dropna()
            q1, q3 = values.quantile([0.25, 0.75])
            iqr = q3 - q1
            whiskers.extend([
                values.loc[values >= q1 - 1.5 * iqr].min(),
                values.loc[values <= q3 + 1.5 * iqr].max(),
            ])
        low, high = min(whiskers), max(whiskers)
        padding = (high - low) * 0.08
        ylim = (low - padding, high + padding)
    fig, ax = plt.subplots(figsize=(5, 3))
    sns.boxplot(
        data=data, x="review_score", y=value_col, order=scores,
        hue="review_score", hue_order=scores, palette=palette,
        dodge=False, legend=False, showfliers=False, showmeans=True,
        width=0.7,
        meanprops={"marker": "D", "markerfacecolor": "white",
                   "markeredgecolor": "black", "markeredgewidth": 1.2,
                   "markersize": 6},
        ax=ax,
    )
    ax.set(ylim=ylim, title=title, xlabel="Review Score", ylabel=ylabel)
    if reference_line is not None:
        ax.axhline(reference_line, color="#666666", linewidth=1,
                   linestyle="--", alpha=0.7)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    return _finish(fig)


def plot_order_value_by_state(
    data: pd.DataFrame, statistic: str, image_path: Path | None = None,
    show: bool = True,
):
    """注文単位GMVを平均または中央値の州順位で並べる。"""
    values = data.groupby("customer_state")["order_gmv"]
    averages = values.mean()
    ranking = averages if statistic == "mean" else values.median()
    order = ranking.sort_values(ascending=False).index.tolist()
    top_gmv = ["SP", "RJ", "MG", "RS", "PR"]
    top_mean = averages.nlargest(5).index.tolist()
    colors = dict(zip(top_gmv, sns.color_palette("Blues_r", n_colors=5).as_hex()))
    colors.update(zip(top_mean, sns.color_palette("Oranges_r", n_colors=5).as_hex()))
    fig, ax = plt.subplots(figsize=(12, 7.5))
    sns.boxplot(
        data=data, x="customer_state", y="order_gmv", order=order,
        hue="customer_state", hue_order=order,
        palette=[colors.get(state, "#cacdd1") for state in order],
        dodge=False, legend=False, showfliers=False, showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "white",
                   "markeredgecolor": "black", "markeredgewidth": 1.2,
                   "markersize": 6}, ax=ax,
    )
    ax.set(
        title=f"Order GMV by Customer State — Sorted by {statistic.title()}",
        xlabel="Customer State",
        ylabel="Order GMV (product prices, excluding freight)",
    )
    ax.tick_params(axis="x", labelrotation=45)
    ax.grid(axis="y", alpha=0.25)
    return _finish(fig, image_path, show)


def plot_category_trends(
    plot_data: pd.DataFrame, period_column: str, categories: list[str],
    states: list[str], title: str, image_path: Path,
):
    """カテゴリごとの小図で3州のAOV構成額を州色で比較する。"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), sharex=True, sharey=False)
    for category, ax in zip(categories, axes.flat):
        for state in states:
            rows = plot_data.loc[
                (plot_data["product_category"] == category)
                & (plot_data["customer_state"] == state)
            ].sort_values(period_column)
            ax.plot(
                rows[period_column], rows["aov_part"],
                color=STATE_COLORS[state], linestyle=STATE_STYLES[state],
                marker=STATE_MARKERS[state], markersize=7, linewidth=2,
            )
        ax.set(title=category.replace("_", " ") ,
               ylabel="Category GMV / all state orders")
        ax.grid(alpha=0.25)
        if period_column == "season_start":
            ticks = sorted(pd.to_datetime(plot_data[period_column].dropna().unique()))
            labels = [f"{d.year + (d.month == 12)} {SEASON_NAMES[d.month]}" for d in ticks]
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, rotation=45, ha="right")
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.tick_params(axis="x", rotation=45)
    legend = [
        Line2D([0], [0], color=STATE_COLORS[state], linestyle=STATE_STYLES[state],
               marker=STATE_MARKERS[state], label=state)
        for state in states
    ]
    fig.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, 0.96), ncol=3)
    fig.suptitle(title, fontsize=15, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(image_path, dpi=200, bbox_inches="tight")
    plt.show()
    return fig


def plot_sp_category_trends(
    monthly_plot: pd.DataFrame, seasonal_plot: pd.DataFrame,
    categories: list[str], image_path: Path,
):
    """SPだけを拡大し、カテゴリは線種と記号で区別する。"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 5), sharey=True)
    for category in categories:
        for ax, data, column, marker_size in [
            (axes[0], monthly_plot, "period_start", 7),
            (axes[1], seasonal_plot, "season_start", 8),
        ]:
            rows = data.loc[
                (data["customer_state"] == "SP")
                & (data["product_category"] == category)
            ].sort_values(column)
            ax.plot(
                rows[column], rows["aov_part"], color=STATE_COLORS["SP"],
                linestyle=CATEGORY_STYLES[category],
                marker=CATEGORY_MARKERS[category], markersize=marker_size,
                linewidth=2, label=category.replace("_", " "),
            )
    axes[0].set_title("SP: monthly category contribution to AOV")
    axes[0].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    axes[0].tick_params(axis="x", rotation=45)
    axes[1].set_title("SP: seasonal category contribution to AOV")
    ticks = sorted(pd.to_datetime(seasonal_plot["season_start"].dropna().unique()))
    axes[1].set_xticks(ticks)
    axes[1].set_xticklabels(
        [f"{d.year + (d.month == 12)} {SEASON_NAMES[d.month]}" for d in ticks],
        rotation=45, ha="right",
    )
    for ax in axes:
        ax.set_ylabel("Category GMV / all SP orders")
        ax.grid(alpha=0.25)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center",
               bbox_to_anchor=(0.5, 1.04), ncol=4)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(image_path, dpi=200, bbox_inches="tight")
    plt.show()
    return fig


def plot_state_category_bars(
    category_data: pd.DataFrame, states: list[str], color_map: dict,
    top_n: int = 20,
):
    """各州のGMV上位カテゴリを、全体図と同じカテゴリ配色で描く。"""
    for state in states:
        bars = category_data.loc[category_data["customer_state"] == state]
        bars = bars.groupby("product_category", as_index=False).agg(
            category_gmv=("category_gmv", "sum")
        ).sort_values("category_gmv", ascending=False).head(top_n)
        bars = bars.assign(display_name=bars["product_category"].str.replace("_", " "))
        names = bars["display_name"].tolist()
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.barplot(
            data=bars, x="display_name", y="category_gmv", hue="display_name",
            order=names, hue_order=names,
            palette=[color_map.get(cat, "#86888c") for cat in bars["product_category"]],
            dodge=False, legend=False, errorbar=None, ax=ax,
        )
        ax.set(title=f"Top {top_n} Product Categories by GMV in {state}",
               xlabel="Product Category", ylabel="Category GMV (Sum)")
        ax.tick_params(axis="x", rotation=45)
        _finish(fig)


def plot_category_gmv_share(
    category_data: pd.DataFrame, color_map: dict, state: str | None = None,
    image_path: Path | None = None, top_n: int = 10,
):
    """全体または1州のカテゴリGMV上位とその他を円グラフにする。"""
    data = category_data if state is None else category_data.loc[
        category_data["customer_state"] == state
    ]
    ranked = data.groupby("product_category", as_index=False).agg(
        category_gmv=("category_gmv", "sum")
    ).sort_values("category_gmv", ascending=False)
    top = ranked.head(top_n)
    labels = top["product_category"].tolist()
    values = top["category_gmv"].tolist()
    if len(ranked) > top_n:
        labels.append("others")
        values.append(ranked["category_gmv"].iloc[top_n:].sum())
    colors = [color_map.get(label, "#cacdd1") for label in labels]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"aspect": "equal"})
    ax.pie(
        values, labels=[label.replace("_", " ") for label in labels],
        autopct="%1.1f%%", startangle=0, counterclock=True,
        labeldistance=1.1, textprops={"fontsize": 10},
        wedgeprops={"linewidth": 0.5, "edgecolor": "white"}, colors=colors,
    )
    suffix = f" in {state}" if state else ""
    ax.set_title(f"Top {top_n} GMV Share by Product Category{suffix}", fontsize=14)
    return _finish(fig, image_path)


def plot_monthly_sales_trend(monthly: pd.DataFrame):
    """月別GMVと注文数を上下に並べる。"""
    dates = pd.to_datetime(monthly["purchase_month"], format="%Y-%m")
    fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
    axes[0].plot(dates, monthly["gmv"], marker="o")
    axes[0].set(title="Monthly GMV", ylabel="GMV")
    axes[1].plot(dates, monthly["order_count"], marker="o", color="orange")
    axes[1].set(title="Monthly Order Count", ylabel="Orders", xlabel="Purchase Month")
    for ax in axes:
        ax.grid(True)
    return _finish(fig)


def plot_state_share_pie(
    state_sales: pd.DataFrame, value_col: str,
    top_states: list[str], high_aov_states: list[str], title: str,
):
    """選んだ州とその他のシェアを同じ配色で描く。"""
    selected = list(dict.fromkeys(top_states + high_aov_states))
    others = [state for state in state_sales["customer_state"] if state not in selected]
    labels = selected + ["others"]
    values = [
        state_sales.loc[state_sales["customer_state"] == state, value_col].iloc[0]
        for state in selected
    ] + [state_sales.loc[state_sales["customer_state"].isin(others), value_col].sum()]
    colors = dict(zip(top_states, sns.color_palette("Blues_r", n_colors=len(top_states)).as_hex()))
    colors.update(zip(high_aov_states, sns.color_palette(
        "Oranges_r", n_colors=len(high_aov_states)
    ).as_hex()))
    fig, ax = plt.subplots(figsize=(7, 6))
    wedges, _, _ = ax.pie(
        values,
        labels=[label if value >= 3 else "" for label, value in zip(labels, values)],
        autopct=lambda percent: f"{percent:.1f}%" if percent >= 3 else "",
        startangle=90, counterclock=False,
        wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
        colors=[colors.get(label, "#cacdd1") for label in labels],
        pctdistance=0.75, textprops={"fontsize": 10},
    )
    legend_labels = [f"{label} ({value:.1f}%)" for label, value in zip(labels, values)]
    ax.legend(wedges, legend_labels, title="Customer State", loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
    ax.set_title(title, fontsize=12)
    if others:
        fig.text(0.5, 0.01, f"others = {', '.join(others)}", ha="center", fontsize=8)
    return _finish(fig)


def plot_monthly_state_aov_box(
    monthly_state_sales: pd.DataFrame, statistic: str,
    top_gmv_states: list[str], top_aov_states: list[str],
):
    """州ごとの月別平均注文額の分布。注文単位の中央値ではない。"""
    ranking = monthly_state_sales.groupby("customer_state")["average_order_value"]
    values = ranking.mean() if statistic == "mean" else ranking.median()
    order = values.sort_values(ascending=False).index.tolist()
    colors = dict(zip(top_gmv_states, sns.color_palette(
        "Blues_r", n_colors=len(top_gmv_states)
    ).as_hex()))
    colors.update(zip(top_aov_states, sns.color_palette(
        "Oranges_r", n_colors=len(top_aov_states)
    ).as_hex()))
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(
        data=monthly_state_sales, x="customer_state", y="average_order_value",
        order=order, hue="customer_state", hue_order=order,
        palette=[colors.get(state, "#cacdd1") for state in order],
        dodge=False, legend=False, showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "white",
                   "markeredgecolor": "black", "markersize": 7}, ax=ax,
    )
    ax.set(title=f"Monthly Average Order Value by State — Sorted by {statistic.title()}",
           xlabel="Customer State", ylabel="Monthly Average Order Value")
    ax.tick_params(axis="x", labelrotation=45)
    return _finish(fig)


def plot_monthly_state_gmv_box(
    monthly_state_sales: pd.DataFrame,
    top_gmv_states: list[str], top_aov_states: list[str],
):
    """月×州GMVの分布を州の合計GMV順で表示する。"""
    order = monthly_state_sales.groupby("customer_state")["gmv"].sum().sort_values(
        ascending=False
    ).index.tolist()
    colors = dict(zip(top_gmv_states, sns.color_palette(
        "Blues_r", n_colors=len(top_gmv_states)
    ).as_hex()))
    colors.update(zip(top_aov_states, sns.color_palette(
        "Oranges_r", n_colors=len(top_aov_states)
    ).as_hex()))
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(
        data=monthly_state_sales, x="customer_state", y="gmv", order=order,
        hue="customer_state", hue_order=order,
        palette=[colors.get(state, "#cacdd1") for state in order], ax=ax,
    )
    ax.set(title="Monthly GMV by Customer State", xlabel="Customer State", ylabel="GMV")
    ax.tick_params(axis="x", labelrotation=45)
    return _finish(fig)
