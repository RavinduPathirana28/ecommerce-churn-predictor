import pandas as pd
import numpy as np
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score, f1_score, recall_score, precision_score, accuracy_score
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

def train_and_export():
    print("Loading raw dataset...")
    df = pd.read_csv("E-Commerce Churn Data.csv")
    print(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns.")

    # 1. Store raw categorical options and numeric statistics for inference
    categorical_options = {
        'Gender': ['Female', 'Male'],
        'MaritalStatus': ['Single', 'Divorced', 'Married'],
        'PreferredLoginDevice': ['Mobile Phone', 'Computer'],
        'PreferredPaymentMode': ['Debit Card', 'Credit Card', 'E-wallet', 'Cash on Delivery', 'UPI'],
        'PreferedOrderCat': ['Laptop & Accessory', 'Mobile Phone', 'Fashion', 'Grocery', 'Others']
    }

    numeric_cols = [
        'Tenure', 'CityTier', 'WarehouseToHome', 'HourSpendOnApp', 
        'NumberOfDeviceRegistered', 'SatisfactionScore', 'NumberOfAddress', 
        'Complain', 'OrderAmountHikeFromlastYear', 'CouponUsed', 
        'OrderCount', 'DaySinceLastOrder', 'CashbackAmount'
    ]

    # Calculate medians on raw data before imputation
    raw_medians = {}
    missing_cols = ['Tenure', 'WarehouseToHome', 'HourSpendOnApp',
                    'OrderAmountHikeFromlastYear', 'CouponUsed',
                    'OrderCount', 'DaySinceLastOrder']
    for col in missing_cols:
        raw_medians[col] = float(df[col].median())

    # Preprocessing identical to notebook:
    # A. Missing indicator features
    for col in ['Tenure', 'WarehouseToHome', 'HourSpendOnApp',
                'OrderAmountHikeFromlastYear', 'OrderCount', 'CouponUsed']:
        df[f'{col}_was_missing'] = df[col].isnull().astype(int)

    # B. Category consolidation
    df['PreferredLoginDevice'] = df['PreferredLoginDevice'].replace({'Phone': 'Mobile Phone'})
    df['PreferredPaymentMode'] = df['PreferredPaymentMode'].replace({
        'COD': 'Cash on Delivery',
        'CC': 'Credit Card'
    })
    df['PreferedOrderCat'] = df['PreferedOrderCat'].replace({'Mobile': 'Mobile Phone'})

    # C. Drop identifier
    df = df.drop(columns=['CustomerID'])

    # D. Median imputation
    for col in missing_cols:
        df[col] = df[col].fillna(raw_medians[col])

    # E. Categorical encoding
    categorical_cols = ['Gender', 'MaritalStatus', 'PreferredLoginDevice',
                        'PreferredPaymentMode', 'PreferedOrderCat']
    df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

    # F. Boolean to int
    bool_cols = df.select_dtypes(include='bool').columns
    df[bool_cols] = df[bool_cols].astype(int)

    # G. Clean column names
    df.columns = df.columns.str.replace(' ', '_').str.replace('&', 'and')

    # Train / Test split
    X = df.drop(columns=['Churn'])
    y = df['Churn']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_test = X_train.copy(), X_test.copy()

    # H. Engineered Tenure Features (Cell 102)
    for data in (X_train, X_test):
        data['Tenure_New_0_3mo'] = (data['Tenure'] <= 3).astype(int)
        data['Tenure_Loyal_12mo_plus'] = (data['Tenure'] > 12).astype(int)

    print(f"X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")
    feature_columns = list(X_train.columns)
    print(f"Total features: {len(feature_columns)}")

    # Best parameters identified from RandomizedSearchCV in Cell 123:
    # {'model__subsample': 1.0, 'model__n_estimators': 200, 'model__min_samples_split': 10, 'model__max_depth': 7, 'model__learning_rate': 0.2}
    best_gb = ImbPipeline([
        ('smote', SMOTE(random_state=42)),
        ('model', GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.2,
            max_depth=7,
            min_samples_split=10,
            subsample=1.0,
            random_state=42
        ))
    ])

    print("Fitting best Gradient Boosting model on full X_train...")
    best_gb.fit(X_train, y_train)

    # Evaluate on test set
    y_pred = best_gb.predict(X_test)
    y_pred_proba = best_gb.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred))
    rec = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    auc = float(roc_auc_score(y_test, y_pred_proba))

    print(f"Test Set Evaluation:")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {auc:.4f}")

    # Feature importances
    gb_model = best_gb.named_steps['model']
    importances = dict(zip(feature_columns, [float(v) for v in gb_model.feature_importances_]))
    sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)

    # Save artifacts
    joblib.dump(best_gb, 'churn_model.joblib')
    print("Saved churn_model.joblib successfully!")

    # Compute typical values (medians/modes) across the full dataset for realistic form defaults
    defaults = {}
    for col in numeric_cols:
        defaults[col] = float(df[col].median())
    for col, opts in categorical_options.items():
        defaults[col] = opts[0]

    metadata = {
        'model_name': 'Tuned Gradient Boosting Classifier',
        'metrics_test': {
            'accuracy': round(acc, 4),
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1': round(f1, 4),
            'roc_auc': round(auc, 4)
        },
        'metrics_cv': {
            'accuracy': 0.9551,
            'precision': 0.9056,
            'recall': 0.8193,
            'f1': 0.8597,
            'roc_auc': 0.9729
        },
        'feature_columns': feature_columns,
        'raw_medians': raw_medians,
        'categorical_options': categorical_options,
        'defaults': defaults,
        'feature_importances': sorted_importances[:10]
    }

    with open('model_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print("Saved model_metadata.json successfully!")

if __name__ == '__main__':
    train_and_export()
