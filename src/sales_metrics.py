"""売上の集計単位を明示して、州・カテゴリ・期間別の指標を作る。"""

import numpy as np
import pandas as pd


def aggregate_sales(data: pd.DataFrame, by: str) -> pd.DataFrame:
    """月×州の集計を指定単位へ合算し、AOVを合計値から再計算する。"""
    result = data.groupby(by, as_index=False).agg(
        order_count=("order_count", "sum"),
        gmv=("gmv", "sum"),
        total_freight=("total_freight", "sum"),
    )
    result["average_order_value"] = result["gmv"] / result["order_count"]
    return result


def add_sales_shares(state_sales: pd.DataFrame) -> pd.DataFrame:
    """州全体のユニークな注文数とGMVを分母にした構成比を付ける。"""
    result = state_sales.copy()
    result["order_share_pct"] = result["order_count"] / result["order_count"].sum() * 100
    result["gmv_share_pct"] = result["gmv"] / result["gmv"].sum() * 100
    return result


def state_totals(baseline: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ表を使わず、月×州の基準表から州注文数・州GMVを求める。"""
    result = aggregate_sales(baseline, "customer_state")
    return result.rename(columns={"order_count": "state_orders", "gmv": "state_gmv"})[
        ["customer_state", "state_orders", "state_gmv", "average_order_value"]
    ]


def category_state_metrics(
    category_data: pd.DataFrame, baseline: pd.DataFrame
) -> pd.DataFrame:
    """カテゴリを含む注文割合、GMVシェア、州AOVへの構成額を付ける。"""
    result = category_data.merge(
        state_totals(baseline), on="customer_state", how="left", validate="many_to_one"
    )
    result["category_order_rate_pct"] = (
        result["category_order_count"] / result["state_orders"] * 100
    )
    result["category_gmv_share_pct"] = result["category_gmv"] / result["state_gmv"] * 100
    result["category_gmv_per_category_order"] = (
        result["category_gmv"] / result["category_order_count"]
    )
    result["aov_part"] = result["category_gmv"] / result["state_orders"]
    return result


def aggregate_category_sales(category_data: pd.DataFrame, by) -> pd.DataFrame:
    """カテゴリ表を指定単位で合計し、金額÷件数を合計後に求め直す。"""
    result = category_data.groupby(by, as_index=False).agg(
        category_order_count=("category_order_count", "sum"),
        order_item_line_count=("order_item_line_count", "sum"),
        category_gmv=("category_gmv", "sum"),
    )
    result["category_gmv_per_category_order"] = (
        result["category_gmv"] / result["category_order_count"]
    )
    result["average_order_line_value"] = (
        result["category_gmv"] / result["order_item_line_count"]
    )
    return result.sort_values("category_gmv", ascending=False).reset_index(drop=True)


def state_aov_difference_by_category(
    category_metrics: pd.DataFrame, target: str, reference: str = "SP"
) -> pd.DataFrame:
    """州AOVの差をカテゴリGMVの構成額で分解する。存在しないカテゴリは0。"""
    selected = category_metrics.loc[
        category_metrics["customer_state"].isin([target, reference])
    ]
    parts = selected.pivot(
        index="product_category", columns="customer_state", values="aov_part"
    ).fillna(0)
    counts = selected.pivot(
        index="product_category", columns="customer_state", values="category_order_count"
    ).fillna(0).astype(int)
    result = pd.DataFrame({
        "product_category": parts.index,
        f"{target}_category_orders": counts[target].to_numpy(),
        f"{reference}_category_orders": counts[reference].to_numpy(),
        f"{target}_aov_part": parts[target].to_numpy(),
        f"{reference}_aov_part": parts[reference].to_numpy(),
    })
    result["aov_part_difference"] = (
        result[f"{target}_aov_part"] - result[f"{reference}_aov_part"]
    )
    return result


def season_start(month_start: pd.Timestamp) -> pd.Timestamp:
    """南半球の四季について、その季節が始まる月を返す。"""
    year, month = month_start.year, month_start.month
    if month in (12, 1, 2):
        return pd.Timestamp(year if month == 12 else year - 1, 12, 1)
    if month in (3, 4, 5):
        return pd.Timestamp(year, 3, 1)
    if month in (6, 7, 8):
        return pd.Timestamp(year, 6, 1)
    return pd.Timestamp(year, 9, 1)


SEASON_NAMES = {12: "Summer", 3: "Autumn", 6: "Winter", 9: "Spring"}


def monthly_category_metrics(
    category_data: pd.DataFrame, baseline: pd.DataFrame, states: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """月×州×カテゴリのGMVと州全体の注文数を結び付ける。"""
    categories = category_data.copy()
    sales = baseline.copy()
    categories["month_start"] = pd.to_datetime(categories["purchase_month"], format="%Y-%m")
    sales["month_start"] = pd.to_datetime(sales["purchase_month"], format="%Y-%m")
    state_month = sales.loc[
        sales["customer_state"].isin(states),
        ["month_start", "customer_state", "order_count", "gmv"],
    ].rename(columns={"order_count": "state_orders", "gmv": "state_gmv"})
    monthly = categories.loc[categories["customer_state"].isin(states)].merge(
        state_month, on=["month_start", "customer_state"],
        how="left", validate="many_to_one",
    )
    monthly = add_period_category_metrics(monthly)
    reconciliation = monthly.groupby(
        ["month_start", "customer_state"], as_index=False
    ).agg(category_gmv_sum=("category_gmv", "sum"), state_gmv=("state_gmv", "first"))
    reconciliation["gmv_difference"] = (
        reconciliation["category_gmv_sum"] - reconciliation["state_gmv"]
    )
    return monthly, state_month, reconciliation


def add_period_category_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ注文のAOVと、州全体AOVへのカテゴリ構成額を区別して計算する。"""
    result = data.copy()
    result["category_order_aov"] = (
        result["category_order_total_gmv"] / result["category_order_count"]
    )
    result["category_gmv_per_category_order"] = (
        result["category_gmv"] / result["category_order_count"]
    )
    result["aov_part"] = result["category_gmv"] / result["state_orders"]
    return result


def seasonal_category_metrics(
    monthly: pd.DataFrame, state_month: pd.DataFrame,
    start: pd.Timestamp, end: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """月の合計から季節指標を作る。月AOVの単純平均は用いない。"""
    monthly_period = monthly.loc[monthly["month_start"].between(start, end)].copy()
    state_period = state_month.loc[state_month["month_start"].between(start, end)].copy()
    monthly_period["season_start"] = monthly_period["month_start"].map(season_start)
    state_period["season_start"] = state_period["month_start"].map(season_start)
    season_state = state_period.groupby(
        ["season_start", "customer_state"], as_index=False
    ).agg(state_orders=("state_orders", "sum"), state_gmv=("state_gmv", "sum"))
    season_category = monthly_period.groupby(
        ["season_start", "customer_state", "product_category"], as_index=False
    ).agg(
        category_order_count=("category_order_count", "sum"),
        category_gmv=("category_gmv", "sum"),
        category_order_total_gmv=("category_order_total_gmv", "sum"),
    )
    seasonal = season_category.merge(
        season_state, on=["season_start", "customer_state"],
        how="left", validate="many_to_one",
    )
    seasonal = add_period_category_metrics(seasonal)
    seasonal["season_label"] = seasonal["season_start"].map(
        lambda day: f"{day.year + (day.month == 12)} {SEASON_NAMES[day.month]}"
    )
    return monthly_period, state_period, seasonal, season_state


def category_plot_data(
    state_totals_by_period: pd.DataFrame,
    category_data: pd.DataFrame,
    period_column: str,
    periods: pd.DatetimeIndex,
    states: list[str],
    categories: list[str],
) -> pd.DataFrame:
    """カテゴリの注文がない期間は0、州注文がない期間は欠損として図示する。"""
    grid = pd.MultiIndex.from_product(
        [periods, states, categories],
        names=[period_column, "customer_state", "product_category"],
    ).to_frame(index=False)
    grid = grid.merge(
        state_totals_by_period[[period_column, "customer_state", "state_orders"]],
        on=[period_column, "customer_state"], how="left",
    )
    grid = grid.merge(
        category_data[[period_column, "customer_state", "product_category",
                       "category_order_count", "category_gmv"]],
        on=[period_column, "customer_state", "product_category"], how="left",
    )
    grid["category_order_count"] = grid["category_order_count"].fillna(0)
    grid["category_gmv"] = grid["category_gmv"].fillna(0)
    grid["aov_part"] = np.where(
        grid["state_orders"] > 0, grid["category_gmv"] / grid["state_orders"], np.nan
    )
    return grid
