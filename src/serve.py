from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import joblib
import os

app = FastAPI()

# AWS Configuration
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET", "your-bucket-name")
S3_MODEL_KEY = "models/latest/model.pkl"
MODEL_PATH = os.path.expanduser("~/models/model.pkl")

def download_model():
    """
    Tai file model.pkl tu S3 ve may khi server khoi dong.
    """
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    if "S3_BUCKET" not in os.environ:
        print("S3_BUCKET environment variable not set. Skipping model download.")
        if not os.path.exists(MODEL_PATH):
            if os.path.exists("models/model.pkl"):
                import shutil
                shutil.copy("models/model.pkl", MODEL_PATH)
                print(f"Copied local model to {MODEL_PATH}")
            else:
                print(f"Warning: Model not found at {MODEL_PATH}")
        return

    # Initialize S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    try:
        s3.download_file(S3_BUCKET, S3_MODEL_KEY, MODEL_PATH)
        print(f"Model da duoc tai xuong tu S3 bucket {S3_BUCKET}.")
    except Exception as e:
        print(f"Error downloading model from S3: {e}")

# Load model at startup
try:
    download_model()
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    else:
        model = None
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

class PredictRequest(BaseModel):
    features: list[float]

@app.get("/health")
def health():
    if model is None:
        return {"status": "warning", "message": "Model not loaded"}
    return {"status": "ok"}

@app.post("/predict")
def predict(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if len(req.features) != 12:
        raise HTTPException(status_code=400, detail="Input must contain exactly 12 features.")

    pred = model.predict([req.features])[0]

    labels = {0: "thap", 1: "trung_binh", 2: "cao"}
    return {
        "prediction": int(pred),
        "label": labels.get(int(pred), "unknown")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
