"""ブートストラップ法を用いた95%信頼区間を計算する関数"""

import numpy as np
import pandas as pd


def bootstrap_mean_difference(
    data,
    group_col,
    value_col,
    n_boot=2000,
    random_state=42,
):
    rng = np.random.default_rng(random_state)

    group_0 = data.loc[data[group_col] == 0, value_col].to_numpy()

    group_1 = data.loc[data[group_col] == 1, value_col].to_numpy()

    observed_diff = group_1.mean() - group_0.mean()

    boot_diffs = np.empty(n_boot)

    for i in range(n_boot):
        sample_0 = rng.choice(
            group_0,
            size=len(group_0),
            replace=True,
        )

        sample_1 = rng.choice(
            group_1,
            size=len(group_1),
            replace=True,
        )

        boot_diffs[i] = sample_1.mean() - sample_0.mean()

    ci_lower, ci_upper = np.percentile(
        boot_diffs,
        [2.5, 97.5],
    )

    return {
        "mean_difference": observed_diff,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }


"""ブロック（クラスター）ブートストラップ法を用いて95%信頼区間を計算する関数"""


def cluster_bootstrap_gmv_difference(
    data,
    cluster_col="customer_unique_id",
    group_col="low_review",
    value_col="future_90d_gmv",
    repeat_col="future_90d_repeat",
    n_boot=2000,
    random_state=42,
):
    # 顧客・評価群ごとに集計
    grouped = (
        data.groupby([cluster_col, group_col])
        .agg(
            n=(value_col, "size"),
            gmv_sum=(value_col, "sum"),
            repeat_n=(repeat_col, "sum"),
        )
        .unstack(group_col, fill_value=0)
    )

    # 各顧客の集計値を配列として保持
    summary = np.column_stack(
        [
            grouped[("n", 0)].to_numpy(),
            grouped[("n", 1)].to_numpy(),
            grouped[("gmv_sum", 0)].to_numpy(),
            grouped[("gmv_sum", 1)].to_numpy(),
            grouped[("repeat_n", 0)].to_numpy(),
            grouped[("repeat_n", 1)].to_numpy(),
        ]
    )

    n_clusters = len(summary)
    rng = np.random.default_rng(random_state)

    boot_all = []
    boot_repeat = []

    for _ in range(n_boot):
        # 顧客単位の復元抽出
        sampled_indices = rng.integers(0, n_clusters, size=n_clusters)

        # 同じ顧客が複数回選ばれることもある
        weights = np.bincount(
            sampled_indices,
            minlength=n_clusters,
        )

        totals = weights @ summary

        n0, n1, gmv0, gmv1, repeat0, repeat1 = totals

        if n0 > 0 and n1 > 0:
            boot_all.append(gmv1 / n1 - gmv0 / n0)

        if repeat0 > 0 and repeat1 > 0:
            boot_repeat.append(gmv1 / repeat1 - gmv0 / repeat0)

    # 観測された平均値の差
    observed = summary.sum(axis=0)
    n0, n1, gmv0, gmv1, repeat0, repeat1 = observed

    return pd.DataFrame(
        [
            {
                "analysis": "All orders",
                "mean_difference": gmv1 / n1 - gmv0 / n0,
                "ci_lower": np.percentile(boot_all, 2.5),
                "ci_upper": np.percentile(boot_all, 97.5),
            },
            {
                "analysis": "Repeat orders only",
                "mean_difference": (gmv1 / repeat1 - gmv0 / repeat0),
                "ci_lower": np.percentile(boot_repeat, 2.5),
                "ci_upper": np.percentile(boot_repeat, 97.5),
            },
        ]
    )
