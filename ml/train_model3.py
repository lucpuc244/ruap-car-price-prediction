import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# ======================
# 1) Load dataset
# ======================
df = pd.read_csv("njuskalo_osijek_regija_auti_5000_2_fixed.csv")

TARGET = "Price_market"
X = df.drop(columns=[TARGET])
y = df[TARGET].astype(float)

# ======================
# 2) Train / Val / Test split
# ======================
X_trainval, X_test, y_trainval, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

X_train, X_val, y_train, y_val = train_test_split(
    X_trainval, y_trainval, test_size=0.2, random_state=42
)

# ======================
# 3) Preprocessing
# ======================
cat_cols = X.select_dtypes(include="object").columns
num_cols = X.select_dtypes(exclude="object").columns

numeric_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("num", numeric_pipe, num_cols),
    ("cat", categorical_pipe, cat_cols)
])

# ======================
# 4) Model (ExtraTrees)
# ======================
model = ExtraTreesRegressor(
    n_estimators=500,
    random_state=42,
    n_jobs=-1
)

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])

# ======================
# 5) Train
# ======================
pipeline.fit(X_train, y_train)

# ======================
# 6) Predict
# ======================
y_train_pred = pipeline.predict(X_train)
y_val_pred   = pipeline.predict(X_val)
y_test_pred  = pipeline.predict(X_test)

# ======================
# 7) Metrics (MAE, MAPE, MSE, RMSE, R², ACC ±1000/±2000)
# ======================
def mape(y_true, y_pred, eps=1e-9):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    # zaštita od dijeljenja s nulom
    return np.mean(np.abs((y_true - y_pred) / (np.maximum(np.abs(y_true), eps)))) * 100

def accuracy_within_range(y_true, y_pred, tolerance=1000):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return np.mean(np.abs(y_true - y_pred) <= tolerance) * 100

def eval_split(name, y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    mape_val = mape(y_true, y_pred)

    acc_1000 = accuracy_within_range(y_true, y_pred, tolerance=1000)
    acc_2000 = accuracy_within_range(y_true, y_pred, tolerance=2000)

    print(f"\n✅ {name}")
    print(f"MAE  = {mae:,.2f} €")
    print(f"MAPE = {mape_val:,.2f} %")
    print(f"MSE  = {mse:,.2f} €²")
    print(f"RMSE = {rmse:,.2f} €")
    print(f"R²   = {r2:.4f}")
    print(f"ACC ±1000 € = {acc_1000:.2f} %")
    print(f"ACC ±2000 € = {acc_2000:.2f} %")

print("=== ExtraTrees Regressor (metrics + plots) ===")
print(f"Train: {len(y_train)} | Val: {len(y_val)} | Test: {len(y_test)}")

eval_split("TRAIN", y_train, y_train_pred)
eval_split("VALIDATION", y_val, y_val_pred)
eval_split("TEST", y_test, y_test_pred)

# =========================================================
# ======================= GRAFOVI =========================
# =========================================================

# -------- 1) Stvarna vs predviđena cijena (TEST) + y=x linija --------
plt.figure()
plt.scatter(y_test, y_test_pred)

# idealna linija: y = x
min_val = min(y_test.min(), y_test_pred.min())
max_val = max(y_test.max(), y_test_pred.max())
plt.plot([min_val, max_val], [min_val, max_val])  # y=x

plt.xlabel("Stvarna cijena (€)")
plt.ylabel("Predviđena cijena (€)")
plt.title("Stvarna vs predviđena cijena (TEST) + idealna linija y=x")
plt.grid(True)
plt.show()

# -------- 2) Reziduali (TEST) --------
residuals = y_test - y_test_pred

plt.figure()
plt.hist(residuals, bins=40)
plt.xlabel("Pogreška predikcije (€)")
plt.ylabel("Broj uzoraka")
plt.title("Distribucija reziduala (TEST)")
plt.grid(True)
plt.show()



MODEL_PATH = "car_price_pipeline.pkl"
joblib.dump(pipeline, MODEL_PATH)

print(f"\n✅ Saved trained pipeline to: {MODEL_PATH}")
print("   (This file is what you upload to Azure ML as the model.)")

