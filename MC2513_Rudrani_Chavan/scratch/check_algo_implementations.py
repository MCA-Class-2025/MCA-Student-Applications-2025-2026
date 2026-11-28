# -*- coding: utf-8 -*-
import os
import glob
import re

root_dir = r"c:\nutrimate"

algos = [
    "Naive Bayes", "GaussianNB", "MultinomialNB", "BernoulliNB",
    "SVM", "SVC", "SVR", "Support Vector",
    "Decision Tree", "DecisionTreeClassifier", "DecisionTreeRegressor",
    "Random Forest", "RandomForestClassifier", "RandomForestRegressor",
    "Logistic Regression", "LogisticRegression",
    "Regression Analysis", "LinearRegression", "statsmodels",
    "Multiple Linear Regression",
    "Polynomial Regression", "PolynomialFeatures"
]

print("=== CHECKING ALL NON-VENV FILES FOR THE 8 ALGORITHMS ===")

files_to_check = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    if "venv" in dirpath or ".git" in dirpath or "__pycache__" in dirpath:
        continue
    for f in filenames:
        if f.endswith((".py", ".ipynb", ".md", ".txt", ".json", ".csv", ".db", ".sqlite3")):
            files_to_check.append(os.path.join(dirpath, f))

found = {}
for path in files_to_check:
    if path.endswith((".db", ".sqlite3", ".csv", ".bin", ".jpg", ".png", ".jpeg")):
        continue
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
            for algo in algos:
                matches = re.findall(rf"\b{re.escape(algo)}\b", content, re.IGNORECASE)
                if matches:
                    if algo not in found:
                        found[algo] = []
                    found[algo].append((path, len(matches)))
    except Exception as e:
        print(f"Error reading {path}: {e}")

for algo in algos:
    if algo in found:
        print(f"\n[FOUND] {algo}:")
        for p, count in found[algo]:
            print(f"  - {p} (count: {count})")
    else:
        print(f"[NOT FOUND] {algo}")

