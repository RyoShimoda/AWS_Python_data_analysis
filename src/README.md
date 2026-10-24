# 共通分析コード

Notebookには「何を確かめるか」「関数へ渡すデータ」「結果の読み方」を残し、繰り返す集計・描画・評価はここへまとめました。

| ファイル | 主な役割 |
|---|---|
| `project_paths.py` | プロジェクト内の`data/`と`images/`の場所を定義 |
| `sales_metrics.py` | 州・月・カテゴリ・季節の集計と平均注文額への構成額 |
| `review_stats.py` | Kruskal–Wallis検定、効果量、Dunn検定後の州ペア整理 |
| `model_metrics.py` | 低評価予測のしきい値別指標と最終評価 |
| `analysis_plots.py` | 複数Notebookで使う箱ひげ図・カテゴリ図・推移図 |
| `order_value_state_plots.py` | 注文単位の州別箱ひげ図を単独で保存する入口 |

## 分類モデルの共通学習関数

- `build_logistic_pipeline()`：数値変数の欠損補完・標準化とカテゴリ変数のOne-Hot Encodingを含むPipelineを構築
- `train_logistic_model()`：ロジスティック回帰を学習し、検証データの予測確率を取得
- `train_random_forest_model()`：共通前処理を利用したRandom Forestの学習
- `train_classifier_model()`：分類器を引数で指定し、XGBoost・LightGBM・CatBoostなどを共通のインターフェースで学習

モデル比較時は、Notebook内に同じ前処理を重複実装せず、これらの関数を利用する。

## 指標の定義

- 州の平均注文額：州GMV合計 ÷ 州のユニークな注文数。月平均AOVの単純平均は使いません。
- カテゴリ注文率：そのカテゴリを含む注文数 ÷ 州のユニークな注文数。複数カテゴリを含む注文はカテゴリごとに数えます。
- 州AOVへのカテゴリ構成額：カテゴリGMV ÷ 州のユニークな注文数。全カテゴリの構成額を足すと州AOVになります。
- カテゴリ注文のAOV：そのカテゴリを含む注文の**注文全体GMV合計** ÷ そのカテゴリを含む注文数。カテゴリGMVだけを分子にした値とは異なります。
- 季節AOV：3か月分のGMV合計 ÷ 同期間の注文数合計。月AOVの単純平均は使いません。

公開用Notebookを上から実行すると`src`の関数を読み込みます。入力CSVは`data/`に置きますが、公開リポジトリへは含めません。関数名を検索すると、各Notebookからの呼び出し箇所を追えます。
