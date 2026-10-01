"""低評価予測のしきい値比較と評価指標。"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
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
    return pd.DataFrame([
        threshold_metrics(y_true, positive_probability, value) for value in thresholds
    ])


def final_classification_metrics(y_true, positive_probability, threshold: float) -> dict:
    """固定済みしきい値で混同行列と各指標を計算する。"""
    predicted = (np.asarray(positive_probability) >= threshold).astype(int)
    result = threshold_metrics(y_true, positive_probability, threshold)
    result["confusion_matrix"] = confusion_matrix(y_true, predicted)
    result["roc_auc"] = roc_auc_score(y_true, positive_probability)
    return result
