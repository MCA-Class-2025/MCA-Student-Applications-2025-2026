# Final Examination Presentation Guide — SnapKnow Analytics Dashboard

## 1. Project title
SnapKnow: Interactive Image Intelligence and Dataset Analytics Dashboard

## 2. Objective
The objective is to analyse the structured output produced by SnapKnow after image analysis. The dashboard helps inspect image categories, model confidence, prediction agreement, text output and measurable image properties.

## 3. Dataset used
The uploaded project contains `snapknow_ml_dataset.csv` with 19 records and 42 columns. It includes:
- Identification fields: image_id, image_filename, source, category, name and true_label.
- Model output: confidence, caption, description, details and fun_fact.
- Text features: word counts and number counts.
- Image features: width, height, aspect ratio, megapixels, file size, RGB means and standard deviations, brightness, contrast, saturation, colourfulness, sharpness, edge density and hue shares.
- Evaluation field: ai_correct.

Important: The report inside the ZIP refers to a separate API-fused `snapknow.csv` (18 records, 38 columns), but this exact file is not included. Do not claim that the supplied 19x42 CSV is that 18x38 fused file. Explain that the dashboard supports uploading the actual fused CSV if it is provided separately.

## 4. Tools and technologies
- Python: main programming language.
- Pandas: data loading, cleaning, filtering and aggregation.
- NumPy: numerical calculations.
- Streamlit: dashboard interface and interactive controls.
- Plotly Express / Graph Objects: interactive visualisations.
- VS Code: development environment.

## 5. Dashboard design
The dashboard is split into four tabs:
1. Overview — category distribution, confidence, highest-confidence names and text length.
2. Model Performance — predicted vs true labels, agreement by category, confidence against correctness.
3. Image Analytics — resolution, brightness, contrast, saturation, RGB channels, hue distribution and correlation.
4. Record Explorer — search individual records, inspect text fields and preview images.

## 6. Explain the 14 graphs
1. Category distribution: shows the number and percentage of records in each predicted class.
2. Confidence distribution: shows how model confidence scores are spread.
3. Highest-confidence identifications: ranks identified items by confidence.
4. Average generated text length: compares word counts for name, caption, description, details and fun fact.
5. Predicted category vs true label: compares model class with the folder-derived label.
6. Label agreement by category: calculates the share of records where ai_correct is 1 for each class.
7. Confidence by correctness: checks whether correct and incorrect predictions have different confidence distributions.
8. Confidence vs correctness: plots confidence against the binary correctness indicator.
9. Image resolution map: compares width and height; marker size can represent megapixels.
10. Brightness vs contrast: explores two image visual properties.
11. Saturation vs colourfulness: examines colour intensity and diversity.
12. Average RGB intensity by category: compares average red, green and blue channel values across classes.
13. Average hue composition: compares red, yellow, green, cyan, blue and magenta shares.
14. Numeric feature correlation heatmap: shows pairwise correlations between numeric columns.

## 7. Interactivity
- Category, confidence and source filters update the data used by every graph.
- Plotly charts support hover details, zooming, panning and legend selection.
- Record Explorer supports text search and individual record selection.
- Users can download the currently filtered data as CSV.
- A different fused CSV can be uploaded through the sidebar.

## 8. Key observations from the included sample
- There are 19 rows and 42 columns.
- Predicted categories are Animal (9), Flower (8), Place (1) and Food (1).
- The `ai_correct` column contains 18 correct and 1 incorrect value, giving 94.7% sample agreement.
- Confidence scores are high in this sample; a high confidence score should not automatically be treated as proof of correctness.
- One record is labelled `Animal` in `true_label` while the model category is `Place` (Bellagio Las Vegas). The source image path is `Animal\flamingo.jpg`, so inspect the source/ground-truth label before treating this as a model failure.

## 9. How to run in VS Code
1. Extract the ZIP and open the `SnapKnow_Dashboard` folder.
2. Create environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\activate`
4. Install: `pip install -r requirements.txt`
5. Run: `streamlit run app.py`
6. Open the localhost URL shown in the terminal.

## 10. Suggested 1-minute explanation
"My project is a Python-based interactive analytics dashboard for SnapKnow, an image intelligence application. SnapKnow analyses images and generates a category, name, confidence score, caption and descriptive information. The dataset also contains image-level numerical features such as resolution, brightness, contrast, colourfulness and RGB values. I used Pandas and NumPy for data handling, Streamlit to create the dashboard interface and Plotly for interactive charts. The dashboard has four sections: Overview, Model Performance, Image Analytics and Record Explorer. It contains fourteen visualisations, global filters, search, image preview and CSV download. This allows a user to explore the dataset instead of reading rows manually. Since the provided sample contains only nineteen records, the findings are descriptive and should not be generalised to all images."

## 11. Likely viva questions
Q: Why did you use Streamlit?
A: It lets me build an interactive web dashboard directly in Python without writing a separate frontend.

Q: Why Plotly instead of static Matplotlib charts?
A: Plotly supports hover information, zoom, pan, legends and interactive chart exploration.

Q: What is confidence?
A: It is the model's own confidence score for an image identification, represented as a percentage in this dataset.

Q: What does ai_correct mean?
A: It is a binary evaluation field: 1 means predicted category matches the true label, and 0 means it does not.

Q: What is a correlation heatmap?
A: It displays pairwise correlations between numeric variables. Correlation does not prove causation.

Q: What are the limitations?
A: The supplied dataset is small, API coverage may be uneven, labels can contain errors, and confidence alone does not guarantee a correct identification.

Q: Is this the Microsoft Power BI application?
A: No. It is a Power BI-inspired dashboard implemented entirely in Python, as requested. It provides similar interactive exploration, but it is not a `.pbix` report.
