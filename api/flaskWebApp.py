import os
from flask import Flask, request, jsonify
from datetime import datetime
from pymongo import DESCENDING
import numpy as np
import pandas as pd
from .db import get_collection

PORT = int(os.environ.get("PORT", ""))
app = Flask(__name__)

def parse_dt(s):
    if not s:
        return None
    try:
        return pd.to_datetime(s, utc=True)
    except Exception:
        return None

@app.get("/health")
def health():
    return jsonify({"ok": True})

def build_filters(args):
    col = get_collection()
    q = {}
    start = parse_dt(args.get("start"))
    end = parse_dt(args.get("end"))
    station = args.get("station")
    parameter = args.get("parameter")

    dt_col = args.get("dt_col", None)
    if not dt_col:
        sample = col.find_one()
        if sample:
            for c in sample.keys():
                cl = str(c).lower()
                if "time" in cl or "date" in cl or "timestamp" in cl:
                    dt_col = c
                    break
    if not dt_col:
        dt_col = "sample_datetime"

    if start or end:
        rng = {}
        if start is not None:
            rng["$gte"] = start.to_pydatetime()
        if end is not None:
            rng["$lt"] = end.to_pydatetime()
        q[dt_col] = rng

    if station:
        for field in ["station", "site", "location", "station_id", "site_id"]:
            q[field] = station
            break

    if parameter:
        q[parameter] = {"$ne": None}

    return q, dt_col

@app.get("/observations")
def observations():
    col = get_collection()
    q, dt_col = build_filters(request.args)
    limit = int(request.args.get("limit", "200"))
    skip = int(request.args.get("skip", "0"))
    projection = None
    cursor = col.find(q, projection).skip(skip).limit(limit).sort([(dt_col, DESCENDING)])
    docs = list(cursor)
    for d in docs:
        d["_id"] = str(d.get("_id", ""))
        for k, v in list(d.items()):
            if isinstance(v, (datetime, pd.Timestamp)):
                d[k] = pd.to_datetime(v).isoformat()
    return jsonify({"count": len(docs), "items": docs})

@app.get("/stats")
def stats():
    col = get_collection()
    q, _ = build_filters(request.args)
    group_by = request.args.get("group_by", "parameter")
    parameter = request.args.get("parameter", None)

    docs = list(col.find(q))
    if not docs:
        return jsonify({"items": []})
    df = pd.DataFrame(docs)

    if parameter and parameter in df.columns:
        num_cols = [parameter]
    else:
        num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        return jsonify({"items": []})

    if group_by == "station":
        key = None
        for candidate in ["station", "site", "location", "station_id", "site_id"]:
            if candidate in df.columns:
                key = candidate
                break
        if key is None:
            key = None
    else:
        key = None

    def summarize(g):
        out = []
        for colname in num_cols:
            series = pd.to_numeric(g[colname], errors="coerce")
            out.append({
                "parameter": colname,
                "count": int(series.count()),
                "mean": None if series.count()==0 else float(series.mean()),
                "median": None if series.count()==0 else float(series.median()),
                "std": None if series.count()==0 else float(series.std()),
                "min": None if series.count()==0 else float(series.min()),
                "max": None if series.count()==0 else float(series.max()),
            })
        return out

    if key:
        items = []
        for grp, gdf in df.groupby(key):
            items.append({"group": {key: None if pd.isna(grp) else grp}, "stats": summarize(gdf)})
    else:
        items = summarize(df)

    return jsonify({"items": items})

@app.get("/outliers")
def outliers():
    col = get_collection()
    q, _ = build_filters(request.args)
    parameter = request.args.get("parameter")
    if not parameter:
        return jsonify({"error": "parameter is required"}, 400)

    z_thresh = float(request.args.get("z", "3"))
    limit = int(request.args.get("limit", "200"))
    skip = int(request.args.get("skip", "0"))

    docs = list(col.find(q))
    if not docs:
        return jsonify({"items": []})

    df = pd.DataFrame(docs)
    if parameter not in df.columns:
        return jsonify({"items": []})

    series = pd.to_numeric(df[parameter], errors="coerce")
    mu = series.mean(skipna=True)
    sigma = series.std(skipna=True)
    if not sigma or np.isnan(sigma) or sigma == 0:
        return jsonify({"items": []})

    z = (series - mu) / sigma
    mask = z.abs() > z_thresh
    out_df = df[mask].copy()
    out_df["_zscore"] = z[mask]
    out_df = out_df.iloc[skip: skip + limit]

    items = out_df.to_dict(orient="records")
    for d in items:
        if "_id" in d:
            d["_id"] = str(d["_id"])
        for k, v in list(d.items()):
            if isinstance(v, (datetime, pd.Timestamp)):
                d[k] = pd.to_datetime(v).isoformat()
        if "_zscore" in d and pd.notna(d["_zscore"]):
            d["_zscore"] = float(d["_zscore"])

    return jsonify({"count": len(items), "items": items})

if __name__ == "__main__":
    col = get_collection()
    if col.estimated_document_count() == 0:
        cleaned_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "cleaned_biscayne_bay_oct_2022.csv")
        if os.path.exists(cleaned_path):
            df = pd.read_csv(cleaned_path)
            col.insert_many(df.to_dict(orient="records"))
    app.run(host="0.0.0.0", port=PORT, debug=True)
