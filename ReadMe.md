# Health Misinformation Detector

BERT-based classifier that detects health misinformation in Reddit posts, targeting nutrition and supplement claims. Built as an end-to-end ML portfolio project covering data collection, labeling, training, and deployment.

## Live Demo

[huggingface.co/spaces/Jbcode/health-misinfo-detector](https://huggingface.co/spaces/Jbcode/health-misinfo-detector)

## What It Does

Takes a health-related claim as input and classifies it as one of:
- **misinfo** — false or misleading health claim
- **accurate** — factually correct health information
- **opinion** — personal view or anecdote, not a factual claim

## Model Performance

| Model | Val F1 (weighted) | Misinfo Recall | Accurate Recall |
|---|---|---|---|
| Logistic Regression (TF-IDF) | 0.792 | 0.59 | 0.53 |
| Random Forest (TF-IDF) | 0.810 | 0.46 | 0.06 |
| XGBoost (TF-IDF) | 0.814 | 0.49 | 0.12 |
| **BERT (fine-tuned)** | **0.816** | **0.53** | **0.24** |

BERT achieves the highest overall F1. Notably, Logistic Regression outperforms BERT on minority class recall — a consequence of class imbalance in the training data (76% opinion, 18% misinfo, 5% accurate).

## Pipeline

```
Reddit JSON endpoints → PostgreSQL → LLM labeling (Mistral/Ollama) → BERT fine-tune → FastAPI → Gradio
```

- **Data**: 2,253 posts collected across 6 subreddits via automated daily collection
- **Labeling**: LLM-assisted labeling with manual inter-labeler agreement validation (Cohen's Kappa)
- **Experiment tracking**: MLflow (3 baseline models + BERT)
- **API**: FastAPI with `/predict` and `/health` endpoints
- **Demo**: Gradio on Hugging Face Spaces

## Project Structure

```
health-misinfo-detector/
├── src/
│   ├── collector.py          # Reddit data collection
│   ├── feature_engineering.py
│   ├── label_posts.py        # Mistral LLM labeling
│   ├── train_baseline.py     # TF-IDF + sklearn models
│   ├── train_bert.py         # BERT fine-tuning
│   └── api.py                # FastAPI prediction endpoint
├── models/
│   └── bert-misinfo/         # Saved model (weights hosted on HF Space, see below)
├── sql/
│   └── init.sql
├── app.py                    # Gradio demo
├── docker-compose.yml
└── requirements.txt
```

## Run Locally

Model weights aren't tracked in this repo. The trained weights live in the [Hugging Face Space](https://huggingface.co/spaces/Jbcode/health-misinfo-detector) (`hf-space/models/bert-misinfo`) — copy them into `models/bert-misinfo/` locally, or run `train_bert.py` to regenerate them, before starting the API or demo.

```bash
# Start database
docker-compose up -d

# Install dependencies
pip install torch transformers fastapi uvicorn gradio
# or: pip install -r requirements.txt

# Run API
uvicorn src.api:app --reload

# Run demo UI
python app.py
```

API docs available at `http://127.0.0.1:8000/docs`

## Limitations

- Model is biased toward the opinion class due to training data imbalance
- Accurate class recall is low (0.24) — addressable with more labeled examples
- Trained on Reddit posts only; may not generalize to other platforms
- No fine-tuning on domain-specific health vocabulary beyond base BERT