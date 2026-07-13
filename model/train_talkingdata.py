"""
TalkingData 数据集训练脚本

数据集字段：
  ip, app, device, os, channel, click_time, attributed_time, is_attributed

is_attributed=0 表示点击后没有安装 → 视为无效点击（欺诈/Bot）
is_attributed=1 表示点击后真实安装了 App → 视为有效点击

特征工程：离线计算聚合统计，模拟线上滑动窗口逻辑

用法：
    python model/train_talkingdata.py
输出：
    model/fraud_model_talkingdata.pkl
"""

import joblib
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

DATA_PATH  = Path("/Users/angelren/.cache/kagglehub/competitions/talkingdata-adtracking-fraud-detection/train_sample.csv")
MODEL_PATH = Path(__file__).parent / "fraud_model_talkingdata.pkl"


# 各计数特征依赖的分组键（组合键在 add_composite_keys 里构造）
COUNT_KEYS = {
    "ip_count":         "ip",
    "ip_app_count":     "ip_app",
    "ip_device_count":  "ip_device",
    "ip_os_count":      "ip_os",
    "ip_channel_count": "ip_channel",
    "ip_app_os_count":  "ip_app_os",
    "app_count":        "app",
    "channel_count":    "channel",
}


def load_raw(path: Path) -> pd.DataFrame:
    """只做行内(row-local)特征：不涉及任何跨行统计，因此不会泄漏。"""
    print("加载数据...")
    df = pd.read_csv(path, parse_dates=["click_time"])
    print(f"  样本数: {len(df):,}  欺诈率: {(1 - df['is_attributed'].mean())*100:.1f}%")

    # 时间特征（每行独立，无泄漏）
    df["hour"] = df["click_time"].dt.hour
    df["day"]  = df["click_time"].dt.day
    df["wday"] = df["click_time"].dt.dayofweek

    # 组合键（用于后续 groupby 计数）
    df["ip_app"]     = df["ip"].astype(str) + "_" + df["app"].astype(str)
    df["ip_device"]  = df["ip"].astype(str) + "_" + df["device"].astype(str)
    df["ip_os"]      = df["ip"].astype(str) + "_" + df["os"].astype(str)
    df["ip_channel"] = df["ip"].astype(str) + "_" + df["channel"].astype(str)
    df["ip_app_os"]  = df["ip"].astype(str) + "_" + df["app"].astype(str) + "_" + df["os"].astype(str)

    # 标签：is_attributed=0 → 欺诈(1)，is_attributed=1 → 正常(0)
    df["is_fraud"] = (df["is_attributed"] == 0).astype(int)
    return df


def fit_count_maps(train_df: pd.DataFrame) -> dict:
    """频率特征只在训练集上拟合，避免测试集信息泄漏进特征。"""
    return {
        feat: train_df.groupby(key).size()
        for feat, key in COUNT_KEYS.items()
    }


def apply_features(df: pd.DataFrame, count_maps: dict) -> pd.DataFrame:
    """把训练集拟合的计数映射套用到该 split；未见过的键 → 0。
    click_interval 在各 split 内部独立计算（不跨 split，故无泄漏）。"""
    df = df.sort_values("click_time").reset_index(drop=True)

    # 点击间隔（同一 IP 相邻两次点击的秒数差）——仅用本 split 内的相邻点击
    df["prev_click_time"] = df.groupby("ip")["click_time"].shift(1)
    df["click_interval_sec"] = (df["click_time"] - df["prev_click_time"]).dt.total_seconds()
    df["click_interval_sec"] = df["click_interval_sec"].fillna(-1)

    # 计数特征：用训练集频率映射
    for feat, key in COUNT_KEYS.items():
        df[feat] = df[key].map(count_maps[feat]).fillna(0).astype(int)

    return df


FEATURES = [
    "ip",
    "app",
    "device",
    "os",
    "channel",
    "hour",
    "day",
    "wday",
    "click_interval_sec",
    "ip_count",
    "ip_app_count",
    "ip_device_count",
    "ip_os_count",
    "ip_channel_count",
    "ip_app_os_count",
    "app_count",
    "channel_count",
]


def main():
    df = load_raw(DATA_PATH)

    # 先切分，再做特征工程 —— 计数特征只在训练集上拟合，杜绝泄漏
    print("特征工程（切分后，仅用训练集拟合计数特征）...")
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["is_fraud"]
    )
    count_maps = fit_count_maps(train_df)
    train_df = apply_features(train_df, count_maps)
    test_df  = apply_features(test_df,  count_maps)

    X_train, y_train = train_df[FEATURES], train_df["is_fraud"]
    X_test,  y_test  = test_df[FEATURES],  test_df["is_fraud"]
    print(f"\n  训练集: {len(X_train):,}  测试集: {len(X_test):,}")

    fraud_ratio = df["is_fraud"].sum() / len(df)
    scale = (1 - fraud_ratio) / fraud_ratio

    print("\n训练 XGBoost...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale,
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    print("\n评估结果:")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    print(f"  AUC-ROC: {auc:.4f}")
    print()
    print(classification_report(y_test, y_pred, target_names=["正常", "欺诈"]))

    print("特征重要性:")
    importances = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])
    for feat, imp in importances:
        if imp > 0.001:
            bar = "█" * int(imp * 50)
            print(f"  {feat:<25} {bar} {imp:.4f}")

    joblib.dump(model, MODEL_PATH)
    print(f"\n模型保存到 {MODEL_PATH}")


if __name__ == "__main__":
    main()
