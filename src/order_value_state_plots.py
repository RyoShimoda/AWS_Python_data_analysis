"""注文単位の州別GMV分布図をNotebookと同じ関数で保存する。"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis_plots import plot_order_value_by_state
from src.project_paths import DATA_DIR, IMAGE_DIR


def main() -> None:
    orders = pd.read_csv(DATA_DIR / "order_level_sales_by_state.csv")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for statistic, filename in [
        ("mean", "Order_Value_Distribution_by_State_Sorted_by_Mean.png"),
        ("median", "Order_Value_Distribution_by_State_Sorted_by_Median.png"),
    ]:
        fig = plot_order_value_by_state(
            orders, statistic, IMAGE_DIR / filename, show=False
        )
        plt.close(fig)


if __name__ == "__main__":
    main()
