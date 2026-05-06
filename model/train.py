"""
Model Training — XGBoost on TalkingData Dataset

Dataset: https://www.kaggle.com/c/talkingdata-adtracking-fraud-detection
Place train.csv in data/ before running.

Training pipeline:
  1. Load data (sample 10M rows for speed)
  2. Feature engineering (click counts, time deltas, aggregations)
  3. Train XGBoost with AUC objective
  4. Evaluate on held-out 20% split
  5. Save model to model/fraud_model.pkl

Target metrics:
  AUC-ROC  > 0.97
  Precision > 0.90 at threshold 0.5
  Recall   > 0.85 at threshold 0.5

Usage:
  python model/train.py
"""

# TODO Phase 3:
# 1. pd.read_csv('data/train.csv', nrows=10_000_000)
# 2. Feature engineering:
#    - ip_click_count: groupby ip, count per hour
#    - ip_app_count: groupby (ip, app), count
#    - ip_device_count: groupby (ip, device), nunique
#    - hour: extract from click_time
#    - next_click_delta, prev_click_delta: time to next/prev click by ip
# 3. train_test_split(stratify=y, test_size=0.2)
# 4. XGBClassifier(n_estimators=300, max_depth=6, eval_metric='auc')
# 5. Print classification_report + roc_auc_score
# 6. joblib.dump(model, 'model/fraud_model.pkl')
