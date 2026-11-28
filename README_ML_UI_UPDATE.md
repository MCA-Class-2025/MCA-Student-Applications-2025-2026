# AI Interior Designer — ML + UI update

## Preserved features
The existing Design Studio, fused-dataset explorer, RAG/FAISS retrieval, Groq, Mistral, Hugging Face image generation, Unsplash, Pixabay, Geoapify, room sizing/layout, PDF and upload workflows have been retained. The update adds a separate **ML Model Lab** tab and a visual refresh; existing workflow controls were not intentionally removed or renamed.

## Eight ML algorithms
1. Naive Bayes — predicts `style_tags`
2. Support Vector Machine — predicts `style_tags`
3. Decision Tree — predicts `style_tags`
4. Random Forest — predicts `style_tags`
5. Logistic Regression — predicts `style_tags`
6. Linear Regression — estimates `match_score` from one numeric feature
7. Multiple Linear Regression — estimates `match_score` from multiple fused features
8. Polynomial Regression — degree-2 regression for `match_score`

The ML tab trains on `fused_dataset/AI_interior_designer.csv`, uses a reproducible 80/20 train/test split, and reports accuracy/precision/recall/F1 for classification and MAE/RMSE/R² for regression. It can export the evaluation table as CSV.

## Run
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
# Add your newly generated provider keys to .env
streamlit run app.py
```

## API credentials
`.env` is deliberately not included in this updated package. Copy `.env.example` to `.env` and supply your own credentials for Groq, Hugging Face, Mistral, Unsplash, Pixabay and Geoapify.

**Security:** The source archive supplied for this update contained populated API credentials in `.env`. Treat those credentials as exposed and revoke/rotate them with each provider before using the app. Do not commit `.env` or share it publicly.
