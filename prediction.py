import pandas as pd
import joblib

model = joblib.load("models/xgboost_model.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")
encoding_info = joblib.load("models/model_encoding.pkl")

model_mean_price = encoding_info["model_mean_price"]
global_mean_price = encoding_info["global_mean_price"]

new_car = {
    "Model": "CLS 450 4MATIC",        
    "Yeni": 0,
    "Yürüş": 62000,
    "Buraxılış ili": 2018,
    "L": 3.0,
    "a.g.": 367,
    "rənglənib": 0,

    # If it is Benzin make all of them 0
    "fuel_Dizel": 0,
    "fuel_Elektro": 0,
    "fuel_Hibrid": 0,
    "fuel_Plug-in hibrid": 0,
    "fuel_Qaz": 0,
    "fuel_Unknown": 0,

    "Hansı bazar üçün yığılıb_Avropa": 1,
    "Hansı bazar üçün yığılıb_Digər": 0,
    "Hansı bazar üçün yığılıb_Dubay": 0,
    "Hansı bazar üçün yığılıb_Koreya": 0,
    "Hansı bazar üçün yığılıb_Rusiya": 0,
    "Hansı bazar üçün yığılıb_Rəsmi diler": 0,
    "Hansı bazar üçün yığılıb_Unknown": 0,
    "Hansı bazar üçün yığılıb_Yaponiya": 0,
    "Hansı bazar üçün yığılıb_Çin": 0,
}

X_new = pd.DataFrame([new_car])

X_new["Model_enc"] = X_new["Model"].map(model_mean_price)
X_new["Model_enc"] = X_new["Model_enc"].fillna(global_mean_price)

X_new = X_new.drop(columns=["Model"])

X_new = X_new.reindex(columns=feature_columns, fill_value=0)

pred_price = model.predict(X_new)[0]
print(f"Predicted Price: {pred_price:.2f} AZN")
