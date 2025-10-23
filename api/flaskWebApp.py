from flask import Flask, jsonify
from mongoDB import upload
import pandas as pd

app = Flask(__name__)

df = pd.read_csv("database/biscayne_bay_dataset_oct_2022.csv")
# print(df.head())
# print(df.columns)

@app.route('/')
def index():
    return jsonify({
        "routes":{
            "/cleandataset": "First 10 rows of water quality",
            "/cleandataset/load": "List of all water quality data",
            "/stats": "mean, median, Q1, Q3, std",
        }
    })

@app.route('/clean')
def clean():
    return jsonify(df.head(10).to_dict(orient="records"))

@app.route('/cleandataset/load',methods=['GET'])
def cleaning_dataset():
    # ZScore Formula
    # zscore = ((X - mean) / standard deviation))

    df = pd.read_csv("./database/biscayne_bay_dataset_oct_2022.csv")

    # Columns for Outliers
    outlier_columns = ['Temperature (C)', 'pH', 'ODO (mg/L)', 'Date m,d,y  ']

    # Using Formula
    df_zscore = (df[outlier_columns] - df[outlier_columns].mean()) / df[outlier_columns].std(ddof=0)

    # Outliers that have |z| > 3
    outliers = (df_zscore.abs() > 3).any(axis=1)

    totalrows = len(df)  # number of rows in data
    removedrows = outliers.sum()  # number of rows removed
    remainingrows = totalrows - removedrows  # remaininggrows

    # Removing outliers
    cleaned_dataset = df[~outliers]
    #print(f"Removed {totalrows - removedrows} outliers (from {totalrows} to {remainingrows})")
    clean_dict = cleaned_dataset.to_dict(orient='records')
    upload(clean_dict)

    #Returning as JSON
    return jsonify(cleaned_dataset.to_dict(orient='records'))



if __name__ == '__main__':
    app.run(debug=True, port=5050)
