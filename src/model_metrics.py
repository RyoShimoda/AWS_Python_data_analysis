"""低評価予測のしきい値比較と評価指標。"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def threshold_metrics(y_true, positive_probability, threshold: float) -> dict:
    """指定した確率しきい値で低評価と判定し、分類指標を返す。"""
    predicted = (np.asarray(positive_probability) >= threshold).astype(int)
    return {
        "threshold": threshold,
        "accuracy": accuracy_score(y_true, predicted),
        "precision": precision_score(y_true, predicted, zero_division=0),
        "recall": recall_score(y_true, predicted, zero_division=0),
        "f1": f1_score(y_true, predicted, zero_division=0),
    }


def threshold_table(y_true, positive_probability, thresholds=None) -> pd.DataFrame:
    """Validationで候補しきい値を比較する。Testではこの表から選ばない。"""
    if thresholds is None:
        thresholds = np.arange(0.01, 1.00, 0.01)
    return pd.DataFrame(
        [threshold_metrics(y_true, positive_probability, value) for value in thresholds]
    )


def final_classification_metrics(
    y_true, positive_probability, threshold: float
) -> dict:
    """固定済みしきい値で混同行列と各指標を計算する。"""
    predicted = (np.asarray(positive_probability) >= threshold).astype(int)
    result = threshold_metrics(y_true, positive_probability, threshold)
    result["confusion_matrix"] = confusion_matrix(y_true, predicted)
    result["roc_auc"] = roc_auc_score(y_true, positive_probability)
    return result


def ranking_metrics_at_k(y_true, probabilities, k):
    """
    予測確率の高い上位K件について、
    Precision@K、Recall@K、Lift@Kを計算する。
    """
    y_true = np.asarray(y_true)
    probabilities = np.asarray(probabilities)

    if len(y_true) != len(probabilities):
        raise ValueError("正解ラベルと予測確率の件数が一致しません。")

    if len(y_true) == 0:
        raise ValueError("評価データが空です。")

    if not np.isin(y_true, [0, 1]).all():
        raise ValueError("正解ラベルは0または1で指定してください。")

    if not np.isfinite(probabilities).all():
        raise ValueError("予測確率に欠損値または無限大が含まれています。")

    if not 1 <= k <= len(y_true):
        raise ValueError("Kは1以上、評価注文数以下にしてください。")

    # 低評価の予測確率が高い順に並べる
    top_indices = np.argsort(-probabilities, kind="stable")[:k]

    # 上位K件で発見した低評価注文数
    true_positives = int(y_true[top_indices].sum())

    # 評価対象全体の低評価注文数
    total_positives = int(y_true.sum())

    # 評価対象全体の低評価率
    base_rate = total_positives / len(y_true)

    precision = true_positives / k

    recall = true_positives / total_positives if total_positives > 0 else np.nan

    lift = precision / base_rate if base_rate > 0 else np.nan

    return {
        "k": k,
        "n_orders": len(y_true),
        "total_positives": total_positives,
        "captured_positives": true_positives,
        "base_rate": base_rate,
        "precision_at_k": precision,
        "recall_at_k": recall,
        "lift_at_k": lift,
    }
