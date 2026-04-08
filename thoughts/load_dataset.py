from datasets import load_dataset
import pandas as pd
import json

dataset = load_dataset("allenai/WildChat-1M", split="train", streaming=True)
sample = pd.DataFrame([row for _, row in zip(range(2_000), dataset)])

# Sonderzeichen bereinigen
def clean_text(obj):
    if isinstance(obj, str):
        return obj.replace('\u2028', ' ').replace('\u2029', ' ')
    elif isinstance(obj, list):
        return [clean_text(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: clean_text(v) for k, v in obj.items()}
    return obj

cleaned = sample.apply(lambda col: col.map(clean_text))

# Speichern
cleaned.to_json("wildchat_sample.json", orient="records", indent=2, force_ascii=False)

print("✅ Fertig! Sonderzeichen bereinigt.")