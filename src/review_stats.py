"""レビュー別・州別の順位比較に使う共通計算。"""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu


def kruskal_by_group(data: pd.DataFrame, group_col: str, value_col: str):
    """欠損値を除き、グループ間のKruskal–Wallis検定を行う。"""
    groups = [
        group[value_col].dropna().to_numpy()
        for _, group in data.groupby(group_col)
        if group[value_col].notna().any()
    ]
    return kruskal(*groups)


def epsilon_squared(h_statistic: float, n: int, k: int) -> float:
    """Kruskal–Wallisの効果量ε²を計算する。"""
    return (h_statistic - k + 1) / (n - k)


def rank_biserial_from_u(u_statistic: float, n_first: int, n_second: int) -> float:
    """U統計量から符号付き順位相関係数を計算する。"""
    return 2 * u_statistic / (n_first * n_second) - 1


def pairwise_effect_sizes(
    data: pd.DataFrame, value_col: str, group_col: str,
    adjusted_p: pd.DataFrame,
) -> pd.DataFrame:
    """全組の中央値差、調整済みp値、Cliff's deltaをまとめる。"""
    rows = []
    groups = sorted(data[group_col].dropna().unique())
    for first, second in combinations(groups, 2):
        x = data.loc[data[group_col] == first, value_col].dropna().to_numpy()
        y = data.loc[data[group_col] == second, value_col].dropna().to_numpy()
        u = mannwhitneyu(x, y, alternative="two-sided", method="asymptotic").statistic
        delta = rank_biserial_from_u(u, len(x), len(y))
        rows.append({
            "group_1": first, "group_2": second,
            "n_1": len(x), "n_2": len(y),
            "median_1": np.median(x), "median_2": np.median(y),
            "median_diff_1_minus_2": np.median(x) - np.median(y),
            "dunn_p_adjusted": adjusted_p.loc[first, second],
            "cliffs_delta": delta, "abs_cliffs_delta": abs(delta),
        })
    return pd.DataFrame(rows)


def cliffs_delta_label(delta: float) -> str:
    """レビュー比較で用いた閾値に沿ってCliff's deltaを区分する。"""
    value = abs(delta)
    if value < 0.147:
        return "negligible"
    if value < 0.330:
        return "small"
    if value < 0.474:
        return "medium"
    return "large"


def state_effect_size_label(value: float) -> str:
    """州別注文額分析で用いた閾値に沿って効果量を区分する。"""
    value = abs(value)
    if value >= 0.5:
        return "large"
    if value >= 0.3:
        return "medium"
    if value >= 0.1:
        return "small"
    return "negligible"


def significant_dunn_pairs(dunn_result: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """対称なDunn行列の上三角から有意な組だけ取り出す。"""
    states = dunn_result.columns.tolist()
    rows = [
        {"state_1": first, "state_2": second,
         "adjusted_p_value": dunn_result.loc[first, second]}
        for i, first in enumerate(states)
        for second in states[i + 1:]
        if dunn_result.loc[first, second] < alpha
    ]
    columns = ["state_1", "state_2", "adjusted_p_value"]
    return pd.DataFrame(rows, columns=columns).sort_values(
        "adjusted_p_value"
    ).reset_index(drop=True)


def state_pair_effect_sizes(
    data: pd.DataFrame, significant_pairs: pd.DataFrame
) -> pd.DataFrame:
    """有意だった州の組の注文額分布差を符号付きで示す。"""
    state_values = {
        state: group["order_gmv"].dropna().to_numpy()
        for state, group in data.groupby("customer_state")
    }
    rows = []
    for pair in significant_pairs.itertuples(index=False):
        x, y = state_values[pair.state_1], state_values[pair.state_2]
        u = mannwhitneyu(x, y, alternative="two-sided", method="asymptotic").statistic
        effect = rank_biserial_from_u(u, len(x), len(y))
        rows.append({
            "state_1": pair.state_1, "state_2": pair.state_2,
            "higher_state": pair.state_1 if effect > 0 else pair.state_2 if effect < 0 else "same",
            "adjusted_p_value": pair.adjusted_p_value,
            "rank_biserial": effect, "absolute_effect_size": abs(effect),
            "median_state_1": np.median(x), "median_state_2": np.median(y),
        })
    columns = [
        "state_1", "state_2", "higher_state", "adjusted_p_value",
        "rank_biserial", "absolute_effect_size", "median_state_1", "median_state_2",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values(
        "absolute_effect_size", ascending=False
    ).reset_index(drop=True)
