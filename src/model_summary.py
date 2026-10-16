"""ロジスティック回帰のodds比と信頼区間を抽出する関数"""

import numpy as np


def extract_low_review_or(model, model_name):
    coef = model.params["low_review"]
    ci = model.conf_int().loc["low_review"]

    return {
        "model": model_name,
        "odds_ratio": np.exp(coef),
        "ci_lower": np.exp(ci[0]),
        "ci_upper": np.exp(ci[1]),
        "p_value": model.pvalues["low_review"],
    }
