from fastapi import FastAPI
import sys

sys.path.append('../Config Files')
import config
sys.path.append('../Database')
import database

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/add_asset")
def process(data: dict):
    config.add_asset(data['asset'], data['asset_type'], data['gate_bypass'])
    return True

@app.post("/remove_asset")
def process(data: dict):
    config.remove_asset(data['asset'])
    return True

@app.post("/get_asset")
def process(data: dict):
    return config.get_assets(data['asset'])

@app.get("/get_signals")
def process():
    return database.select_all('signals')

if __name__ == "__main__":
    port = 3000
    app.run(port=port)