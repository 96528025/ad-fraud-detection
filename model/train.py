"""
XGBoost 模型训练

用法：
    python model/train.py
输出：
    model/fraud_model.pkl
"""

import joblib
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

DATA_PATH  = Path(__file__).parent.parent / "data" / "training_data.csv"
MODEL_PATH = Path(__file__).parent / "fraud_model.pkl"

FEATURES = [
    "ip_click_count_1min",
    "ip_click_count_1hour",
    "device_ip_count",
    "click_interval_ms",
    "hour_of_day",
    "app_id",
    "channel_id",
    "os",
    "is_blacklisted",
]


def main():
    # 1. 加载数据
    print("加载数据...")
    df = pd.read_csv(DATA_PATH)
    print(f"  总样本: {len(df):,}  欺诈率: {df['is_fraud'].mean()*100:.1f}%")

    X = df[FEATURES]
    y = df["is_fraud"]

    # 2. 划分训练集 / 测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  训练集: {len(X_train):,}  测试集: {len(X_test):,}")

    # 3. 训练 XGBoost
    print("\n训练 XGBoost...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=9,   # 处理类别不平衡（正常:欺诈 ≈ 9:1）
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # 4. 评估
    print("\n评估结果:")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    print(f"  AUC-ROC: {auc:.4f}")
    print()
    print(classification_report(y_test, y_pred, target_names=["正常", "欺诈"]))

    # 5. 特征重要性
    print("特征重要性:")
    importances = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])
    for feat, imp in importances:
        bar = "█" * int(imp * 50)
        print(f"  {feat:<25} {bar} {imp:.4f}")

    # 6. 保存模型
    joblib.dump(model, MODEL_PATH)
    print(f"\n模型保存到 {MODEL_PATH}")


if __name__ == "__main__":
    main()
