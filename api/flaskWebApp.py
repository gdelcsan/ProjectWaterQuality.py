from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

df = pd.read_csv("Datasets/biscayne_bay_dataset_oct_2022.csv")
# print(df.head())
# print(df.columns)

@app.route('/')
def index():
    return jsonify({
        "routes":{
            "/cars": "First 10 rows of all cars",
            "/cars/makes": "List of all unique car makes",
            "/cars/bodies": "List of all unique car bodies",
            "cars/prices": "First 10 rows showing car name and price",
        }
    })

@app.route('/cars')
def {cars, make():
return jsonify({})

if __name__ == '__main__':
    app.run(debug=True, port=5050)
