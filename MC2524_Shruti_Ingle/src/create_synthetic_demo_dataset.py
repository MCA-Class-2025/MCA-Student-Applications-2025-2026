import csv
import json
from pathlib import Path
from datetime import datetime, timezone

OUTPUT = Path("datasets/synthetic_demo_dataset.csv")

if OUTPUT.exists():
    raise SystemExit(
        f"STOP: {OUTPUT} already exists. "
        "It was not overwritten."
    )

topics = [
    ("Python", "a programming language used for automation, scripting, data analysis, and AI"),
    ("Java", "an object-oriented programming language used in many applications"),
    ("C Sharp", "a programming language commonly used with the .NET platform"),
    ("C Plus Plus", "a compiled programming language used for systems and performance-focused software"),
    ("JavaScript", "a programming language used to create interactive web experiences"),
    ("HTML", "the markup language used to structure web pages"),
    ("CSS", "the language used to style web pages"),
    ("React", "a JavaScript library for building user interfaces"),
    ("ASP.NET Core", "a framework for building web applications and APIs with .NET"),
    ("REST API", "a web interface that lets software systems exchange data through HTTP"),
    ("SQL", "a language used to query and manage relational databases"),
    ("SQL Server", "a relational database management system from Microsoft"),
    ("MySQL", "an open-source relational database management system"),
    ("Database Normalization", "a database design technique that reduces unwanted duplication"),
    ("Primary Key", "a column or set of columns that uniquely identifies a database row"),
    ("Foreign Key", "a database constraint that links related tables"),
    ("Object-Oriented Programming", "a programming approach organized around objects and classes"),
    ("Inheritance", "an object-oriented feature that lets a class reuse another class's behavior"),
    ("Polymorphism", "a programming concept that allows one interface to have different implementations"),
    ("Encapsulation", "a programming principle that groups data and behavior and controls access"),
    ("Data Structures", "ways of organizing data for efficient access and modification"),
    ("Arrays", "indexed collections of elements"),
    ("Linked Lists", "data structures made of nodes connected by links"),
    ("Stacks", "collections that typically follow last-in, first-out order"),
    ("Queues", "collections that typically follow first-in, first-out order"),
    ("Binary Search", "a search algorithm for sorted data that repeatedly halves the search range"),
    ("Sorting Algorithms", "algorithms that arrange data in a chosen order"),
    ("Time Complexity", "a way to describe how an algorithm's running time scales with input size"),
    ("Machine Learning", "a field that develops systems that learn patterns from data"),
    ("Supervised Learning", "machine learning using examples with known target labels or values"),
    ("Unsupervised Learning", "machine learning that looks for patterns in data without target labels"),
    ("Train Test Split", "a method for separating data used to fit and evaluate a model"),
    ("Cross Validation", "a technique that evaluates a model across multiple data splits"),
    ("Logistic Regression", "a statistical model often used for classification"),
    ("Random Forest", "an ensemble model that combines multiple decision trees"),
    ("Support Vector Machine", "a model that can separate classes using decision boundaries"),
    ("K Nearest Neighbors", "a method that predicts using nearby examples in feature space"),
    ("Model Accuracy", "the fraction of predictions that match the correct labels"),
    ("Precision and Recall", "classification metrics that measure prediction correctness and coverage"),
    ("Overfitting", "when a model fits training data too closely and generalizes poorly"),
    ("Data Preprocessing", "steps used to clean and prepare data before analysis or modeling"),
    ("Exploratory Data Analysis", "the process of summarizing and examining a dataset"),
    ("Pandas", "a Python library for working with tabular data"),
    ("NumPy", "a Python library for numerical arrays and computation"),
    ("Streamlit", "a Python framework for creating interactive data applications"),
    ("Git", "a version control system for tracking changes in files"),
    ("GitHub", "a platform for hosting and collaborating on code repositories"),
    ("Cloud Computing", "the delivery of computing resources over a network"),
    ("Cybersecurity", "the practice of protecting systems, networks, and information"),
    ("Authentication", "the process of verifying a user's or system's identity"),
    ("Retrieval Augmented Generation", "a pattern that retrieves relevant information before generating a response"),
]

angles = [
    "overview",
    "purpose",
    "common use",
    "key terminology",
    "workflow",
    "advantages",
    "limitations",
    "security considerations",
    "troubleshooting",
    "revision summary",
]

now = datetime.now(timezone.utc).isoformat()
rows = []

for topic_number, (topic, description) in enumerate(topics, start=1):
    for angle_number, angle in enumerate(angles, start=1):
        record_number = (topic_number - 1) * len(angles) + angle_number
        title = f"SYNTHETIC DEMO {record_number:03d} - {topic} - {angle.title()}"

        content = (
            f"SYNTHETIC DEMO RECORD - NOT A REAL SOURCE DOCUMENT.\\n"
            f"Topic: {topic}.\\n"
            f"General description: {description}.\\n"
            f"Test category: {angle}.\\n"
            f"Purpose: test document search, retrieval, filtering, and chatbot "
            f"handling of clearly labelled sample content.\\n"
            f"Important: this generated record is a demo fixture, not verified "
            f"evidence for a factual answer. Consult a real source to verify "
            f"specific claims about {topic}."
        )

        metadata = {
            "synthetic": True,
            "dataset_role": "demo_testing_only",
            "record_id": f"SYN-{record_number:03d}",
            "topic": topic,
            "test_category": angle,
            "warning": "Not real source evidence; do not report as collected data",
        }

        rows.append({
            "source_type": "synthetic_demo",
            "title": title,
            "content": content,
            "url": "",
            "language": "en",
            "modified_time": now,
            "metadata": json.dumps(metadata, ensure_ascii=False),
        })

if len(rows) < 500:
    raise SystemExit(f"Expected at least 500 records, generated {len(rows)}.")

rows = rows[:500]
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=[
        "source_type", "title", "content", "url",
        "language", "modified_time", "metadata"
    ])
    writer.writeheader()
    writer.writerows(rows)

print("Synthetic demo dataset created successfully.")
print("File:", OUTPUT)
print("Records:", len(rows))
print("Unique titles:", len({row['title'] for row in rows}))
print("Source type:", "synthetic_demo")
print("Original datasets were not modified.")

