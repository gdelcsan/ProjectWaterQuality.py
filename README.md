# Biscayne Bay Water Quality Database Project

### Deployed:
[Streamlit App](https://waterdatasetbiscayne.streamlit.app/)

[REST API](https://biscaynebayproject.onrender.com/)

### API Documentation
#### List of endpoints:
```json
   {
  "routes": {
    "/api/health": "returns API status",
    "/api/observations": {
      "return documents with optional query parameters": [
        "start/end (ISO timestamps)",
        "min_temp, max_temp",
        "min_sal, max_sal",
        "min_odo, max_odo",
        "limit, (default 100, max 1000)",
        "skip (for pagination)"
      ]
    },
    "/api/outliers": "return a list of flagged records",
    "/api/stats": "count, mean, min, max, and percentiles (25%, 50%, 75%)"
  }
}
```

All of the mentioned endpoints only support GET requests.

## /api/health 
This endpoint is responsible for returning status information about the availability of MongoDB and the API.
Does not need any URL arguments.

## /api/observations 
If this endpoint doesn't receive any URL arguments, it returns documents from MongoDB with a default limit of 100.
If it does, the URL arguments are handled, and it returns documents from MongoDB based on the query arguments.

## /api/outliers
This endpoint will not function without any URL arguments. It will return a bad request if no URL arguments are provided.
Only acceptable fields are "field", "method", and "k."

## /api/stats
Returns statistics including count, mean, min, max, std, first quartile, median, and third quartile for all numeric columns.
Does not need any URL arguments.



### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run client/streamlit_app.py
   ```

3. Run Flask

   ```
   $python -u "c:\Users\jaile\biscaynebayproject\api\flaskWebApp.py"
   ```
