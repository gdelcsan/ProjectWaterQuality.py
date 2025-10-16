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
<<<<<<< Updated upstream
        "routes":{
            "/cleandataset": "First 10 rows of water quality",
            "/cleandataset/load": "List of all water quality data",
            "/filters": "filters",
            "/statistics": "mean, median, Q1, Q3, std",
=======
        "routes": {
            "/api/status": "returns API status",
            "/api/clean": "First 10 rows of water quality",
            "/api/cleandataset": "Clean raw water quality data and returns it as a json",
            "/api/observations": 
            {
                "return documents with optional query parameters:":
                [
                    "start/end (ISO timestamps)",
                    "min_temp, max_temp",
                    "min_sal, max_sal",
                    "min_odo, max_odo",
                    "limit, (default 100, max 1000)"
                    "skip (for pagination)"
                ]
            },
            "/api/stats": "count, mean, min, max, and percentiles (25%, 50%, 75%)",
            "/outliers" : "return a list of flagged records", 
>>>>>>> Stashed changes
        }
    })

@app.route('/api/status')
def status():
    return { "status": "ok" }

@app.route('/api/clean')
def clean():
    return jsonify(df.head(10).to_dict(orient="records"))

@app.route('/api/cleandataset',methods=['GET'])
def cleaning_dataset():
    # ZScore Formula
    # zscore = ((X - mean) / standard deviation))

    # Columns for Outliers
    outlier_columns = ['Temperature (C)', 'pH', 'ODO (mg/L)']

    # Using Formula
    df_zscore = (df[outlier_columns] - df[outlier_columns].mean()) / df[outlier_columns].std(ddof=0)

    # Outliers that have |z| > 3
    outliers = (df_zscore.abs() > 3).any(axis=1)

    totalrows = len(df)  # number of rows in data
    removedrows = outliers.sum()  # number of rows removed
    remainingrows = totalrows - removedrows  # remaininggrows

    # Removing outliers
    cleaned_dataset = df[~outliers]
    clean_dict = cleaned_dataset.to_dict(orient='records')

    # Responsible for creatign database/report.txt:
    #report = f"Removed {totalrows - removedrows} outliers (from total of {totalrows} rows to remaining rows of {remainingrows})"
    #fp = open("database/report.txt", "w")
    #fp.write(report)
    #fp.close()
    
    upload(clean_dict)

    #Returning as JSON
    return jsonify(cleaned_dataset.to_dict(orient='records'))

<<<<<<< Updated upstream
=======
@app.route('/api/outliers')
def pullOutliers():

    # Dataset gets read
    df = pd.read_csv("./database/biscayne_bay_dataset_oct_2022.csv")

    # Use columns to check for outliers
    outlier_columns = ['Temperature (C)', 'pH', 'ODO (mg/L)']

    #Z-score is computed for each value
    df_zscore = (df[outlier_columns] - df[outlier_columns].mean()) / df[outlier_columns].std(ddof=0)

    # Identify outliers
    outliers = (df_zscore.abs() > 3).any(axis=1)

    # Filter out olier rows
    outlier_rows = df[outliers]

    #JSON output
    outlier_dict = outlier_rows.to_dict(orient='records')

    return jsonify({
        "total_outliers": len(outlier_rows),
        "outlier_rows": outlier_dict
    })
>>>>>>> Stashed changes

if __name__ == '__main__':
    app.run(debug=True, port=5050)
