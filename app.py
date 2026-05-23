import os
import torch
import gradio as gr
from transformers import BertTokenizer, BertForSequenceClassification

# Load model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "bert-misinfo")
LABEL_MAP = {0: "accurate", 1: "misinfo", 2: "opinion"}

tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()

def predict(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    )

    with torch.no_grad():
        outputs = model(**inputs)
    
        probs = torch.softmax(outputs.logits, dim=1).squeeze()
    pred_idx = torch.argmax(probs).item()
    label = LABEL_MAP[pred_idx]
    confidence = round(probs[pred_idx].item() * 100, 1)

    result = f"Prediction: {label.upper()}\nConfidence: {confidence}%\n\n"
    result += f"accurate:  {round(probs[0].item() * 100, 1)}%\n"
    result += f"misinfo:   {round(probs[1].item() * 100, 1)}%\n"
    result += f"opinion:   {round(probs[2].item() * 100, 1)}%"

    return result

demo = gr.Interface(
    fn=predict,
    inputs=gr.Textbox(lines=4, label="Enter a health claim or Reddit post"),
    outputs=gr.Textbox(lines=8, label="Analysis"),
    title="Health Misinformation Detector",
    description="Analyzes health-related claims from Reddit and classifies them as misinformation, accurate information, or opinion.",
    examples=[
        ["Vitamin C cures cancer if you take 10,000mg daily"],
        ["The recommended daily intake of Vitamin C for adults is 65 to 90 milligrams per day"],
        ["I personally think everyone should take magnesium supplements"]
    ]
)


demo.launch()