from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from model import detect_anomalies

app = FastAPI()

# Allow GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze-csv")
async def analyze_csv(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    result = detect_anomalies(df)
    return result.to_dict(orient="records")
