import os
from fastapi import FastAPI
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "bert-misinfo")

app = FastAPI(title = "Health Misinformation Detector")

LABEL_MAP = {0: "accurate", 1: "misinfo", 2: "opinion"}

tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}

class PredictRequest(BaseModel):
    text: str

@app.post("/predict")
def predict(request: PredictRequest):

    #tokenize
    inputs = tokenizer(
        request.text,
        return_tensors = "pt",
        truncation = True,
        padding = True,
        max_length = 128
    )

    #inference
    with torch.no_grad():
        outputs = model(**inputs)

    #convert logits to probabilities
    probs = torch.softmax(outputs.logits, dim=1).squeeze()

    #get prediction
    pred_idx = torch.argmax(probs).item()

    return {
        "prediction": LABEL_MAP[pred_idx],
        "confidence": round(probs[pred_idx].item(), 4),
        "probabilities": {
            "accurate": round(probs[0].item(), 4),
            "misinfo": round(probs[1].item(), 4),
            "opinion": round(probs[2].item(), 4)
        }
    }