from flask import Flask, jsonify, request, abort
from mongoDB import upload_MONGO, query, mongo_OK
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "routes": {
            "/api/health": "returns API status",
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

@app.route('/api/health',methods=['GET'])
def status():
    status = {"status": "OK", "mongoDB": "ONLINE" if mongo_OK else "OFFLINE"}
    return jsonify(status), 200

# Will return error if accessed through a GET request, only allowed from streamlit
@app.route('/api/upload', methods=['POST'])
def upload():
    if request.is_json:
        results = upload_MONGO(request.get_json())
        return jsonify(results), 200
    else:
        return jsonify('Error. Request must be JSON'), 400

@app.route('/api/observations',methods=['GET'])
def observations():
    name_args = ["min_time", "max_time", "min_temp", "max_temp", "min_sal", "max_sal", "min_odo", "max_odo", "limit", "skip"]
    params = {}
    for i in range(len(name_args)):
        flask_request = request.args.get(name_args[i])
        if flask_request: params.update({name_args[i] : flask_request})
    
    #import json
    #with open("test.json", 'w') as f:
        #json.dump(args, f)
    
    if len(params) == 0 and len(request.args.keys()) > 0: 
        abort(400, "Arguments provided are not supported.")
        
    if not "limit" in params: 
        params["limit"] = 100
    else:
        params["limit"] = int(params["limit"])
        if params["limit"] > 1000: 
            params["limit"] = 1000
    if not "skip" in params: 
        params["skip"] = 0
    else: 
        params["skip"] = int(params["skip"])

    data = query(params)
    count = data["count"]
    if count != 0:
        documents = data["items"]
        for item in documents:
            del item['_id']

        return {"count": count, "items": documents}
    else:
        return {}

@app.route('/api/stats',methods=['GET'])
def stats():
    documents = (observations()).get("items")
    df = pd.DataFrame(documents)
    return jsonify((df.describe()).to_dict(orient='dict'))

"""
@app.route('/api/outliers',methods=['GET'])
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
"""

if __name__ == '__main__':
    app.run(debug=True, port=5050)
    #app.run(host='0.0.0.0', debug=True)
