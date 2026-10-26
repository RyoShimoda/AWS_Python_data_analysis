# 共通分析コード

Notebookには「何を確かめるか」「関数へ渡すデータ」「結果の読み方」を残し、繰り返す集計・描画・評価はここへまとめました。

| ファイル | 主な役割 |
|---|---|
| `analysis_plots.py` | 分析結果の可視化 |
| `bootstrap.py` | ブートストラップによる推定 |
| `model_metrics.py` | 分類モデルの評価指標・しきい値評価 |
| `model_search.py` | 複数のハイパーパラメータ候補を時系列CVで評価 |
| `model_summary.py` | モデル結果の集計・整理 |
| `model_training.py` | 前処理とモデル学習 |
| `order_value_state_plots.py` | 注文金額・地域別分析の可視化 |
| `project_paths.py` | ディレクトリパスの共通管理 |
| `review_stats.py` | レビュー評価に関する統計処理 |
| `sales_metrics.py` | 売上関連指標の集計 |


## 分類モデルの共通学習関数

- `build_logistic_pipeline()`：数値変数の欠損補完・標準化とカテゴリ変数のOne-Hot Encodingを含むPipelineを構築
- `train_logistic_model()`：ロジスティック回帰を学習し、検証データの予測確率を取得
- `train_random_forest_model()`：共通前処理を利用したRandom Forestの学習
- `train_classifier_model()`：分類器を引数で指定し、XGBoost・LightGBM・CatBoostなどを共通のインターフェースで学習
- `evaluate_parameter_candidates()`（`model_search.py`）：指定したハイパーパラメータ候補を時系列CVで評価し、Fold別結果と平均指標を返す

モデル比較時は、Notebook内に同じ前処理を重複実装せず、これらの関数を利用する。

## 指標の定義

- 州の平均注文額：州GMV合計 ÷ 州のユニークな注文数。月平均AOVの単純平均は使いません。
- カテゴリ注文率：そのカテゴリを含む注文数 ÷ 州のユニークな注文数。複数カテゴリを含む注文はカテゴリごとに数えます。
- 州AOVへのカテゴリ構成額：カテゴリGMV ÷ 州のユニークな注文数。全カテゴリの構成額を足すと州AOVになります。
- カテゴリ注文のAOV：そのカテゴリを含む注文の**注文全体GMV合計** ÷ そのカテゴリを含む注文数。カテゴリGMVだけを分子にした値とは異なります。
- 季節AOV：3か月分のGMV合計 ÷ 同期間の注文数合計。月AOVの単純平均は使いません。

公開用Notebookを上から実行すると`src`の関数を読み込みます。入力CSVは`data/`に置きますが、公開リポジトリへは含めません。関数名を検索すると、各Notebookからの呼び出し箇所を追えます。
