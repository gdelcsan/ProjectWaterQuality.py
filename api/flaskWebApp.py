from flask import Flask, jsonify, request, abort
from mongoDB import upload, query
import pandas as pd

app = Flask(__name__)

# print(df.head())
# print(df.columns)

@app.route('/')
def index():
    return jsonify({
        "routes": {
            "/api/health": "returns API status",
            "/api/cleandataset": "cleans raw water quality data",
            "/api/observations": 
            {
                "return documents with optional query parameters":
                [
                    "start/end (ISO timestamps)",
                    "min_temp, max_temp",
                    "min_sal, max_sal",
                    "min_odo, max_odo",
                    "limit, (default 100, max 1000)",
                    "skip (for pagination)"
                ]
            },
            "/api/stats": "count, mean, min, max, and percentiles (25%, 50%, 75%)",
            "/api/outliers" : "return a list of flagged records", 
        }
    })

@app.route('/api/health')
def status():
    return { "status": "ok" }

@app.route('/api/cleandataset',methods=['GET'])
def cleaning_dataset():
    # ZScore Formula
    # zscore = ((X - mean) / standard deviation))
    df = pd.read_csv("database/biscayne_bay_dataset_oct_2022.csv")
    
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

    # Responsible for creating database/report.txt:
    #report = f"Removed {totalrows - removedrows} outliers (from total of {totalrows} rows to remaining rows of {remainingrows})"
    #fp = open("database/report.txt", "w")
    #fp.write(report)
    #fp.close()
    
    upload(clean_dict)

    #Returning as JSON
    return {"status": "cleaned"}

@app.route('/api/observations')
def observations():
    name_args = ["min_temp", "max_temp", "min_sal", "max_sal", "min_odo", "max_odo", "limit", "skip"]
    args = {}
    for i in range(len(name_args)):
        flask_request = request.args.get(name_args[i])
        if flask_request: args[name_args[i]] = flask_request
    
    if len(args) == 0 and len(request.args.keys()) > 0: 
        abort(400, "Arguments provided are not supported.")
        
    if not "limit" in args: 
        args["limit"] = 100
    else:
        args["limit"] = int(args["limit"])
        if args["limit"] > 1000: 
            args["limit"] = 1000
    if not "skip" in args: 
        args["skip"] = 0
    else: 
        args["skip"] = int(args["skip"])
    
    from bson import json_util
    import json
    return json.loads(json_util.dumps(query(args)))
    #return query(args)

@flask_app.get("/api/stats")
def api_stats():
    """
    Stats for the CURRENT selected_df:
    count, mean, std, min, 25%, 50%, 75%, max for numeric columns only.
    """
    try:
        with SELECTED_DF_LOCK:
            local_df = SELECTED_DF.copy() if SELECTED_DF is not None else None

        if local_df is None or not hasattr(local_df, "select_dtypes"):
            return jsonify({"error": "No dataset selected"}), 400

        num_df = local_df.select_dtypes(include="number")
        if num_df.empty:
            return jsonify({"error": "No numeric columns to summarize for this dataset"}), 400

        # Use describe() to include percentiles 25/50/75
        desc = num_df.describe()  # rows: ['count','mean','std','min','25%','50%','75%','max']

        # Round + sanitize for JSON (jsonify cannot handle NaN/Inf)
        desc = desc.round(3).replace([np.inf, -np.inf], np.nan).where(pd.notnull(desc), None)

        # Return a tidy records-like structure (one row per metric)
        summary = (
            desc.transpose()
                .reset_index()
                .rename(columns={"index": "metric"})
        )

        # Ensure 'metric' is a string (just in case)
        summary["metric"] = summary["metric"].astype(str)

        return jsonify(summary.to_dict(orient="records")), 200

    except Exception as e:
        return jsonify({"error": "internal_error", "detail": str(e)}), 500
        
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

if __name__ == '__main__':
    app.run(debug=True, port=5050)
