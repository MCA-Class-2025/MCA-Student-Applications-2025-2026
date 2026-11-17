# SnapKnow Interactive Analytics Dashboard

A professional, Power BI-inspired interactive dashboard built entirely with Python using Streamlit, Pandas and Plotly. Designed to run in VS Code.

## Included files
- `app.py` — interactive dashboard with 14 visualisations, global filters, record search, image preview and CSV export.
- `snapknow_ml_dataset.csv` — dataset included in the submitted project ZIP.
- `snapknow_images/` — available image previews.
- `requirements.txt` — Python dependencies.

## Important dataset note
The project ZIP includes `snapknow_ml_dataset.csv` (19 records, 42 columns). It contains the model output, image features, `true_label`, and `ai_correct`. The project report describes a separate API-fused file called `snapknow.csv` (18 records, 38 columns), but that exact file is not present in the uploaded ZIP. This dashboard therefore uses the actual CSV that was supplied. If you obtain the report's `snapknow.csv`, upload it using the sidebar's **Upload fused / ML dataset (CSV)** control. The dashboard will use it where matching fields exist; fields absent from that file will be skipped automatically.

## Run in VS Code (Windows)
1. Extract this folder.
2. Open the folder in VS Code.
3. Open Terminal → New Terminal.
4. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

5. Install packages:

```bash
pip install -r requirements.txt
```

6. Start the dashboard:

```bash
streamlit run app.py
```

7. Open the local URL printed in the terminal (usually `http://localhost:8501`).

## Dashboard contents (14 charts)
1. Image category distribution
2. Confidence score distribution
3. Highest-confidence identifications
4. Average generated text length
5. Predicted category vs true label
6. Label agreement by category
7. Confidence by prediction correctness
8. Confidence vs correctness
9. Image resolution map
10. Brightness vs contrast
11. Saturation vs colourfulness
12. Average RGB colour intensity by category
13. Average hue composition
14. Numeric feature correlation heatmap

## Interactive features
- Global sidebar filters for predicted category, confidence range and source image.
- Four dashboard tabs for overview, model performance, image analytics and record exploration.
- Search for a record by name, ID, caption or category.
- Image preview when a corresponding image file is included.
- Hover tooltips, zoom, pan, legends and chart interactions through Plotly.
- Download the filtered records as CSV.
- Upload a different fused dataset without editing the code.

## Academic interpretation / limitation
The included dataset is small (19 records). Present percentages and correlations as descriptive results for this sample, not as proof of general model performance. The supplied sample has 18 correct and 1 incorrect label according to `ai_correct` (94.7% agreement). The single mismatch is Bellagio Las Vegas, predicted as Place while the folder-derived true label is Animal; inspect the original source image/label before interpreting this as a model error.
