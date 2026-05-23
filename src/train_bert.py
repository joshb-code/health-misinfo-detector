import pandas as pd
import mlflow
import mlflow.pytorch
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification
from torch.optim import AdamW
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv('data/training_data.csv', names=['post_id', 'title', 'body', 'label', 'confidence'])
df = df[df['label'] != 'label']
df = df[df['label'] != 'unsure']
df = df.dropna(subset=['label'])
df['text'] = df['title'].fillna('') + ' ' + df['body'].fillna('')
df['text'] = df['text'].str[:512]

# Encode labels
le = LabelEncoder()
df['label_encoded'] = le.fit_transform(df['label'])

# Split
X_train, X_temp, y_train, y_temp = train_test_split(
    df['text'].tolist(), df['label_encoded'].tolist(),
    test_size=0.3, random_state=42, stratify=df['label_encoded']
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
)

print(f"Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

# Tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

class MisinfoDataset(Dataset):
    def __init__(self, texts, labels):
        self.encodings = tokenizer(texts, truncation=True, padding=True, max_length=128)
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

train_dataset = MisinfoDataset(X_train, y_train)
val_dataset = MisinfoDataset(X_val, y_val)

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=16)

# Model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3)
model.to(device)

optimizer = AdamW(model.parameters(), lr=2e-5)

# Training
mlflow.set_experiment('health-misinfo-bert')

with mlflow.start_run(run_name='bert-base-uncased'):
    mlflow.log_param('model', 'bert-base-uncased')
    mlflow.log_param('epochs', 3)
    mlflow.log_param('batch_size', 16)
    mlflow.log_param('lr', 2e-5)

    for epoch in range(3):
        model.train()
        total_loss = 0
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch+1} | Loss: {avg_loss:.4f}")
        mlflow.log_metric('train_loss', avg_loss, step=epoch)

    # Validation
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            outputs = model(input_ids, attention_mask=attention_mask)
            preds = torch.argmax(outputs.logits, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    f1 = f1_score(all_labels, all_preds, average='weighted')
    mlflow.log_metric('val_f1_weighted', f1)

    print(f"\nVal F1 (weighted): {f1:.3f}")
    print(classification_report(all_labels, all_preds, target_names=le.classes_))

    # Save model
    model.save_pretrained('models/bert-misinfo')
    tokenizer.save_pretrained('models/bert-misinfo')
    print("Model saved to models/bert-misinfo")