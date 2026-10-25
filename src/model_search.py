import pandas as pd
from sklearn.base import clone
from sklearn.metrics import average_precision_score, roc_auc_score

from src.model_training import train_classifier_model


def evaluate_parameter_candidates(
    df,
    fold_configs,
    numeric_features,
    categorical_features,
    base_classifier,
    parameter_candidates,
):
    """
    複数のパラメータ候補を時系列4-Fold CVで評価する。

    Returns
    -------
    fold_results : DataFrame
        候補・Foldごとの評価結果
    summary : DataFrame
        候補ごとの平均・標準偏差
    """

    results = []

    for trial_id, params in enumerate(parameter_candidates, start=1):
        classifier = clone(base_classifier).set_params(**params)

        print(f"候補 {trial_id}/{len(parameter_candidates)}")

        for fold_name, start, end in fold_configs:
            start = pd.Timestamp(start)
            end = pd.Timestamp(end)

            train = df.loc[
                (df["delivered_timestamp"] < start)
                & (df["last_review_timestamp"] < start)
            ]

            validation = df.loc[
                (df["delivered_timestamp"] >= start) & (df["delivered_timestamp"] < end)
            ]

            _, y_val, probabilities = train_classifier_model(
                train,
                validation,
                numeric_features,
                categorical_features,
                classifier,
            )

            results.append(
                {
                    "trial": trial_id,
                    "fold": fold_name,
                    **params,
                    "roc_auc": roc_auc_score(y_val, probabilities),
                    "average_precision": average_precision_score(y_val, probabilities),
                }
            )

    fold_results = pd.DataFrame(results)

    summary = (
        fold_results.groupby("trial")
        .agg(
            roc_auc_mean=("roc_auc", "mean"),
            roc_auc_std=("roc_auc", "std"),
            ap_mean=("average_precision", "mean"),
            ap_std=("average_precision", "std"),
        )
        .sort_values("ap_mean", ascending=False)
    )

    return fold_results, summary
