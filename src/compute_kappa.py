import pandas as pd
from sklearn.metrics import cohen_kappa_score

# Load your manually labeled CSV
df = pd.read_csv('data/manual_labeling_done.csv')

# Drop any rows where a label is missing
df = df.dropna(subset=['manual_label', 'llm_label'])

print(f"N posts compared: {len(df)}")

# Compute Cohen's Kappa
kappa = cohen_kappa_score(df['manual_label'], df['llm_label'])
print(f"Cohen's Kappa: {kappa:.3f}")

# Label distributions
print("\n--- Your Labels ---")
print(df['manual_label'].value_counts())

print("\n--- Mistral's Labels ---")
print(df['llm_label'].value_counts())

# Where did you disagree?
disagreements = df[df['manual_label'] != df['llm_label']]
print(f"\n--- Disagreements: {len(disagreements)} posts ---")
print(disagreements[['title', 'manual_label', 'llm_label']].to_string())