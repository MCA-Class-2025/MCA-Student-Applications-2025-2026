# FishFusion Analytics — Exploratory Data Analysis Dashboard
https://fishfusionappdeployment-jw5ylf3gvecbmfxkltrbeg.streamlit.app/

# 1. Project overview
FishFusion Analytics is an exploratory dashboard built around a fish image dataset enriched with information from three additional sources:
1. Image dataset information — fish species labels and whether each image belongs to the training or testing split.
2. GBIF biodiversity information — taxonomic identification and occurrence information, such as the number of recorded occurrences, country coverage and mean occurrence coordinates.
3. USDA nutrition information — calories, protein, fat and carbohydrates associated with each species.
4. Weather enrichment — temperature, humidity, pressure, wind speed, cloud cover and a weather description associated with each species.
The purpose of the dashboard is to bring these different kinds of information together so that a user can explore the dataset from several perspectives: image distribution, biodiversity coverage, nutrition, environment and data quality.

What this dashboard is for: understanding what information is available in the FishFusion dataset, comparing species, spotting patterns and identifying missing or limited enrichment data.


<img width="713" height="488" alt="image" src="https://github.com/user-attachments/assets/99669aba-98b6-4825-bca6-315aca1c7e62" />

<img width="704" height="503" alt="image" src="https://github.com/user-attachments/assets/bdddcaf0-8512-4b13-be66-3d31a680fbeb" />

<img width="721" height="464" alt="image" src="https://github.com/user-attachments/assets/4b29fd4e-b815-438e-bca3-02bd97f39d18" />

<img width="742" height="329" alt="image" src="https://github.com/user-attachments/assets/08db4813-d22b-492f-a5f6-5e9439ca7dd9" />

<img width="737" height="361" alt="image" src="https://github.com/user-attachments/assets/f5ec28d9-42cc-4c69-a7f8-f207901687bc" />


# Dashboard walkthrough — what each chart tells you
A. Overview
The Overview section provides a quick picture of the image dataset and its species composition.

# Images by species — horizontal bar chart
- Shows the number of image records available for each fish species.
- A longer bar means that more image records are available for that species.
- Use it to identify which classes have more images and which classes have fewer images.
- Why it matters: uneven class counts can affect how a machine-learning image classifier learns. This chart describes the dataset distribution; it does not by itself measure model accuracy.
# Train / test composition — donut chart
- Shows how image records are divided between the training and testing splits.
- The slices represent the share of records assigned to each split.
- Use it to check the overall split composition.
- Why it matters: training data is used to fit a model, while testing data is held out to evaluate it. A split chart does not prove that the split is free from data leakage.
# Image share — treemap
- Shows each species' contribution to the total image collection as differently sized rectangles.
- Larger rectangles represent a larger share of image records.
- Use it to compare class representation at a glance.
# GBIF occurrences vs country coverage — bubble chart
- Compares the number of GBIF occurrence records with the number of countries represented for each species.
- Each bubble represents a species; bubble size provides an additional visual cue for occurrence volume.
- Use it to see whether a species with many occurrence records also has broad country coverage.
- This is a comparison of the GBIF enrichment sample, not a direct estimate of wild population size.
# Automatic EDA observations
- Presents short observations calculated from the supplied data.
- Treat these as descriptive findings that help direct further investigation, rather than as causal explanations or scientific conclusions.
