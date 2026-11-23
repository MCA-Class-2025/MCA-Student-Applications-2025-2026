import pandas as pd
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,precision_recall_fscore_support,classification_report,confusion_matrix

BASE=Path(__file__).resolve().parent
DATA=BASE/"final_api_enriched_interview_dataset.csv"
OUT=BASE/"ml_results"; OUT.mkdir(exist_ok=True)

df=pd.read_csv(DATA)
df=df[df["difficulty"].notna()].copy()
df["difficulty"]=df["difficulty"].astype(str).str.strip().str.title()
df=df[df["difficulty"].isin(["Easy","Medium","Hard"])].copy()

for c in ["question","category","skill","programming_language"]:
    df[c]=df[c].fillna("").astype(str)
df["model_text"]="Question: "+df["question"]+" Category: "+df["category"]+" Skill: "+df["skill"]+" Language: "+df["programming_language"]

X=df["model_text"]; y=df["difficulty"]
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.20,random_state=42,stratify=y)

models={
"Logistic Regression":LogisticRegression(max_iter=2000,class_weight="balanced",random_state=42),
"Naive Bayes":MultinomialNB(),
"Random Forest":RandomForestClassifier(n_estimators=250,random_state=42,class_weight="balanced_subsample",n_jobs=-1)
}
rows=[]
for name,m in models.items():
    pipe=Pipeline([("tfidf",TfidfVectorizer(stop_words="english",ngram_range=(1,2),min_df=2,max_features=20000)),("model",m)])
    pipe.fit(Xtr,ytr); pred=pipe.predict(Xte)
    a=accuracy_score(yte,pred); pr,re,f1,_=precision_recall_fscore_support(yte,pred,average="weighted",zero_division=0)
    print("\n",name,"Accuracy:",round(a,4),"Precision:",round(pr,4),"Recall:",round(re,4),"F1:",round(f1,4))
    print(classification_report(yte,pred,zero_division=0))
    cm=confusion_matrix(yte,pred,labels=["Easy","Medium","Hard"])
    pd.DataFrame(cm,index=["Easy","Medium","Hard"],columns=["Easy","Medium","Hard"]).to_csv(OUT/(name.lower().replace(" ","_")+"_confusion_matrix.csv"))
    (OUT/(name.lower().replace(" ","_")+"_report.txt")).write_text(classification_report(yte,pred,zero_division=0),encoding="utf-8")
    joblib.dump(pipe,OUT/(name.lower().replace(" ","_")+"_model.pkl"))
    rows.append({"algorithm":name,"accuracy":a,"precision_weighted":pr,"recall_weighted":re,"f1_weighted":f1})

cmp=pd.DataFrame(rows).sort_values("f1_weighted",ascending=False)
cmp.to_csv(OUT/"model_comparison.csv",index=False)
print("\nMODEL COMPARISON\n",cmp.to_string(index=False))
print("\nBEST MODEL:",cmp.iloc[0]["algorithm"])
print("Results:",OUT)
