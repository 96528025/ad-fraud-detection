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


def load_and_engineer(path: Path) -> pd.DataFrame:
    print("加载数据...")
    df = pd.read_csv(path, parse_dates=["click_time"])
    print(f"  样本数: {len(df):,}  欺诈率: {(1 - df['is_attributed'].mean())*100:.1f}%")

    print("特征工程...")

    # 时间特征
    df["hour"]    = df["click_time"].dt.hour
    df["day"]     = df["click_time"].dt.day
    df["wday"]    = df["click_time"].dt.dayofweek

    # 排序（用于计算点击间隔）
    df = df.sort_values("click_time").reset_index(drop=True)

    # 点击间隔（同一 IP 相邻两次点击的秒数差）
    df["prev_click_time"] = df.groupby("ip")["click_time"].shift(1)
    df["click_interval_sec"] = (df["click_time"] - df["prev_click_time"]).dt.total_seconds()
    df["click_interval_sec"] = df["click_interval_sec"].fillna(-1)

    # 聚合特征：各维度点击数量
    df["ip_app"]    = df["ip"].astype(str) + "_" + df["app"].astype(str)
    df["ip_device"] = df["ip"].astype(str) + "_" + df["device"].astype(str)
    df["ip_os"]     = df["ip"].astype(str) + "_" + df["os"].astype(str)
    df["ip_channel"]= df["ip"].astype(str) + "_" + df["channel"].astype(str)
    df["ip_app_os"] = df["ip"].astype(str) + "_" + df["app"].astype(str) + "_" + df["os"].astype(str)

    df["ip_count"]         = df.groupby("ip")["ip"].transform("count")
    df["ip_app_count"]     = df.groupby("ip_app")["ip"].transform("count")
    df["ip_device_count"]  = df.groupby("ip_device")["ip"].transform("count")
    df["ip_os_count"]      = df.groupby("ip_os")["ip"].transform("count")
    df["ip_channel_count"] = df.groupby("ip_channel")["ip"].transform("count")
    df["ip_app_os_count"]  = df.groupby("ip_app_os")["ip"].transform("count")
    df["app_count"]        = df.groupby("app")["app"].transform("count")
    df["channel_count"]    = df.groupby("channel")["channel"].transform("count")

    # 标签：is_attributed=0 → 欺诈(1)，is_attributed=1 → 正常(0)
    df["is_fraud"] = (df["is_attributed"] == 0).astype(int)

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
    df = load_and_engineer(DATA_PATH)

    X = df[FEATURES]
    y = df["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n  训练集: {len(X_train):,}  测试集: {len(X_test):,}")

    fraud_ratio = y.sum() / len(y)
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
