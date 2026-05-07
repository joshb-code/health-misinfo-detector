import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder

# Load data
df = pd.read_csv('data/training_data.csv', names=['post_id', 'title', 'body', 'label', 'confidence'])
df = df[df['label'] != 'label']  # remove header row that snuck in
df = df[df['label'] != 'unsure']  # too few samples to stratify
df = df.dropna(subset=['label'])
df['text'] = df['title'].fillna('') + ' ' + df['body'].fillna('')

print(f"Dataset size: {len(df)}")
print(df['label'].value_counts())

# Encode labels
le = LabelEncoder()
df['label_encoded'] = le.fit_transform(df['label'])

# Train/val/test split (70/15/15)
X_train, X_temp, y_train, y_temp = train_test_split(
    df['text'], df['label_encoded'], test_size=0.3, random_state=42, stratify=df['label_encoded']
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
)

print(f"\nTrain: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

# TF-IDF vectorizer
tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
X_train_tfidf = tfidf.fit_transform(X_train)
X_val_tfidf = tfidf.transform(X_val)
X_test_tfidf = tfidf.transform(X_test)

# Models to try
models = {
    'logistic_regression': LogisticRegression(max_iter=1000, class_weight='balanced'),
    'random_forest': RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42),
    'xgboost': XGBClassifier(n_estimators=100, random_state=42, verbosity=0)
}

mlflow.set_experiment('health-misinfo-baseline')

for name, model in models.items():
    with mlflow.start_run(run_name=name):
        model.fit(X_train_tfidf, y_train)
        
        val_preds = model.predict(X_val_tfidf)
        f1 = f1_score(y_val, val_preds, average='weighted')
        
        mlflow.log_param('model', name)
        mlflow.log_param('tfidf_features', 10000)
        mlflow.log_metric('val_f1_weighted', f1)
        mlflow.sklearn.log_model(model, name)
        
        print(f"\n--- {name} ---")
        print(f"Val F1 (weighted): {f1:.3f}")
        print(classification_report(y_val, val_preds, target_names=le.classes_))

print("\nDone. Run 'mlflow ui' to view results.")