# Tanu Gupta - Weather Project

This project combines a Spring Boot weather application, historical Indian
weather datasets, exploratory analysis, machine-learning models, and a
Gemini/FAISS weather assistant.

## Project structure

- [`api_implementation/`](./api_implementation/): Spring Boot API, web UI,
  static assets, Maven wrapper, and build configuration.
- [`dashboard/`](./dashboard/): Streamlit dashboard code, bundled assets, and
  UI screenshots.
- [`dataset/`](./dataset/): raw, processed, and generated weather data.
- [`eda_implementaion/`](./eda_implementaion/): preprocessing, EDA scripts,
  analysis results, and visualizations.
- [`llm_implementation/`](./llm_implementation/): FastAPI weather assistant,
  Gemini/RAG integration, vector-store builder, and tests.
- [`ml_algorithm/`](./ml_algorithm/): model training, serialized models, and
  evaluation results.
- [`document/`](./document/): project report and detailed guides.

For setup instructions, see the [documentation index](./document/README.md).

## Quick start

Run the Spring Boot application from PowerShell:

```powershell
cd api_implementation
.\mvnw.cmd spring-boot:run
```

Run the dashboard from the project folder in PowerShell:

```powershell
python -m pip install -r .\dashboard\code\requirements.txt
streamlit run .\dashboard\code\app.py
```

Run preprocessing, EDA, and model training from the project folder:

```powershell
python .\eda_implementaion\preprocess.py
python .\eda_implementaion\eda_analysis.py
python .\eda_implementaion\fused_eda.py
python .\ml_algorithm\ml_algorithms.py
```

The Python scripts resolve dataset and output locations from the project
structure. See [`document/`](./document/) for service instructions and the
Phase 1/2 report.
