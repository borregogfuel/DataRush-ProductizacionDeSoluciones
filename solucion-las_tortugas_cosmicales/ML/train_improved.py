import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import argparse
import os


def load_data(path):
    df = pd.read_csv(path)
    # Expect columns: PRECINCT, HOUR, INCIDENT_COUNT, AVG_SEVERITY, SAFETY_INDEX
    return df


def build_pipeline():
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestRegressor(random_state=42))
    ])
    return pipeline


def get_param_dist():
    return {
        'rf__n_estimators': [50, 100, 200, 300],
        'rf__max_depth': [None, 10, 20, 30],
        'rf__min_samples_split': [2, 5, 10],
        'rf__min_samples_leaf': [1, 2, 4],
        'rf__max_features': ['auto', 'sqrt', 'log2']
    }


def train_and_save(df, out_path, n_iter=20, cv=3, random_state=42):
    X = df[['PRECINCT', 'HOUR']]
    y = df['SAFETY_INDEX']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=random_state)

    pipeline = build_pipeline()
    param_dist = get_param_dist()

    search = RandomizedSearchCV(pipeline, param_distributions=param_dist, n_iter=n_iter, cv=cv, scoring='neg_mean_absolute_error', random_state=random_state, n_jobs=-1)
    search.fit(X_train, y_train)

    best = search.best_estimator_

    preds = best.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)

    print("Training complete")
    print(f"Best params: {search.best_params_}")
    print(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump(best, out_path)
    print(f"Saved best model to {out_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to safety_data CSV (PRECINCT,HOUR,INCIDENT_COUNT,AVG_SEVERITY,SAFETY_INDEX)')
    parser.add_argument('--output', default='ML/safety_model_improved.joblib', help='Output model path')
    parser.add_argument('--n_iter', type=int, default=20, help='RandomizedSearchCV iterations')
    parser.add_argument('--cv', type=int, default=3, help='CV folds')
    args = parser.parse_args()

    df = load_data(args.input)
    train_and_save(df, args.output, n_iter=args.n_iter, cv=args.cv)
