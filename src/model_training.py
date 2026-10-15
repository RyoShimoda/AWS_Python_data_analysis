"""特徴量セットを指定したロジスティック回帰の学習。"""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_logistic_pipeline(
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
    *,
    max_iter: int = 1000,
) -> Pipeline:
    """数値の中央値補完・標準化とカテゴリの欠損補完・One-hot化を定義する。

    戻り値は未学習。fit時に渡したデータだけで補完値や尺度を学習する。
    数値のみ、またはカテゴリのみの場合は、もう一方に空リストを指定する。
    """
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, list(numeric_features)),
            ("cat", categorical_transformer, list(categorical_features)),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=max_iter)),
        ]
    )


def train_logistic_model(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
    *,
    target: str = "low_review",
    max_iter: int = 1000,
) -> tuple[Pipeline, pd.Series, np.ndarray]:
    """学習済みモデル、検証の正解ラベル、クラス1の予測確率を返す。

    目的変数は0/1で指定する。データ分割は呼び出し側で行い、
    前処理とモデルはtrainだけで学習する。validationは予測のみに使う。
    戻り値の正解ラベルと予測確率はmodel_metrics.threshold_tableに渡せる。
    """
    if not train[target].isin([0, 1]).all() or train[target].nunique() != 2:
        raise ValueError("学習データの目的変数には0と1の両方が必要です。")
    features = list(numeric_features) + list(categorical_features)
    if not features:
        raise ValueError("特徴量を1つ以上指定してください。")
    if target in features:
        raise ValueError("目的変数を特徴量に含めることはできません。")
    if len(features) != len(set(features)):
        raise ValueError("特徴量名が重複しています。")

    model = build_logistic_pipeline(
        numeric_features, categorical_features, max_iter=max_iter
    )
    model.fit(train[features], train[target])
    positive_probability = model.predict_proba(validation[features])[:, 1]
    return model, validation[target], positive_probability
