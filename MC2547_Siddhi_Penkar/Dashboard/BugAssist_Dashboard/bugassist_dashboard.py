"""
BugAssist DataFusion - Interactive Python Dashboard
Run:  python bugassist_dashboard.py
Output: Dashboard/bugassist_dashboard.html (opens automatically in your browser)
"""
import os, re
import numpy as np, pandas as pd
import plotly.express as px, plotly.graph_objects as go
from dashkit import build, style, PALETTE

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "Dataset", "BugAssistDataFusion.xlsx")

# ------------------------------------------------------------------ 1. LOAD
df = pd.read_excel(SRC)
print("Loaded", df.shape)

# ------------------------------------------------------------------ 2. CLEAN
# Columns containing missing values are NOT used (as required by the project brief)
null_cols = df.columns[df.isna().any()].tolist()
print("Dropped (contain nulls):", null_cols)
df = df.drop(columns=null_cols)
df = df.drop_duplicates("bug_id")

# Raw text / URL columns are not chartable -> keep only for feature extraction
df["category"] = df["title"].str.replace(r"\s*(Bug\s*)?detected in system", "", regex=True).str.strip()
df["repo"] = df["github_top_issue_url"].str.extract(r"github\.com/([^/]+/[^/]+)/")[0]
TECH = ["Spring Boot", "Django", "Flask", "Laravel", "Vue", "Angular", "React", "Node", "Express",
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", ".NET", "Rails", "FastAPI"]
def tech(txt):
    for t in TECH:
        if re.search(r"\b" + re.escape(t), txt):
            return t
    return None
df["technology"] = df["gemini_root_cause_analysis"].apply(tech)
df["priority"] = pd.Categorical(df["gemini_priority_recommendation"],
                                ["Low", "Medium", "High", "Critical"], ordered=True)
df["severity_band"] = pd.cut(df["cve_top_severity_score"], [-0.1, 3.9, 6.9, 8.9, 10],
                             labels=["Low (0-3.9)", "Medium (4-6.9)", "High (7-8.9)", "Critical (9+)"])
PCOL = {"Low": "#3ddc97", "Medium": "#ffd166", "High": "#ff7a45", "Critical": "#ef476f"}
conf, gh, so, cve = ("gemini_fix_confidence_score", "github_similar_issues_count",
                     "stackoverflow_top_answer_score", "cve_related_count")

# ------------------------------------------------------------------ 3. KPIs
kpis = [("Total Bugs", f"{len(df):,}"),
        ("Avg Fix Confidence", f"{df[conf].mean():.2f} / 10"),
        ("Critical + High", f"{(df.priority.isin(['High','Critical'])).mean()*100:.1f}%"),
        ("Avg CVE Severity", f"{df.cve_top_severity_score.mean():.2f}"),
        ("Avg GitHub Similar Issues", f"{df[gh].mean():,.0f}"),
        ("Bug Categories", f"{df.category.nunique()}")]

# ------------------------------------------------------------------ 4. CHARTS
# ---- Overview
pr = df.priority.value_counts().reindex(["Critical", "High", "Medium", "Low"]).reset_index()
pr.columns = ["priority", "count"]
f1 = px.pie(pr, names="priority", values="count", hole=.55, color="priority", color_discrete_map=PCOL)
f1.update_traces(textinfo="label+percent")
cat = df.category.value_counts().reset_index(); cat.columns = ["category", "count"]
f2 = px.bar(cat.sort_values("count"), x="count", y="category", orientation="h", color="count",
            color_continuous_scale=["#4cc9f0", "#b05cff", "#ff7a45"]); f2.update_coloraxes(showscale=False)
cp = df.groupby(["category", "priority"], observed=True).size().reset_index(name="count")
f3 = px.bar(cp, x="category", y="count", color="priority", color_discrete_map=PCOL,
            category_orders={"priority": ["Low", "Medium", "High", "Critical"]})
f3.update_xaxes(tickangle=-40)
f4 = px.histogram(df, x=conf, nbins=9, color_discrete_sequence=["#b05cff"])
f4.update_traces(marker_line_color="#0b1020", marker_line_width=1)
f4.update_layout(bargap=.08, xaxis_title="Fix confidence score", yaxis_title="Bugs")
tm = px.treemap(df.assign(priority=df.priority.astype(str)), path=[px.Constant("All bugs"), "priority", "category"], color="priority",
                color_discrete_map={**PCOL, "(?)": "#25305a"})
tm.update_traces(root_color="#131b33")

# ---- Gemini AI
cc = df.groupby("category")[conf].mean().sort_values().reset_index()
g1 = px.bar(cc, x=conf, y="category", orientation="h", color=conf,
            color_continuous_scale="Sunset"); g1.update_coloraxes(showscale=False)
g1.update_xaxes(range=[cc[conf].min() - .5, cc[conf].max() + .2], title="Avg confidence")
g2 = px.box(df, x="priority", y=conf, color="priority", color_discrete_map=PCOL,
            category_orders={"priority": ["Low", "Medium", "High", "Critical"]}, points="all")
g2.update_traces(marker_size=3)
tc = df.dropna(subset=["technology"]).groupby("technology").agg(n=("bug_id", "count"), conf=(conf, "mean")).reset_index()
g3 = px.bar(tc.sort_values("n"), x="n", y="technology", orientation="h", color="conf",
            color_continuous_scale="Tealgrn", labels={"n": "Bugs mentioning it", "conf": "Avg conf."})
heat = df.pivot_table(index="category", columns="priority", values=conf, aggfunc="mean", observed=True)
g4 = px.imshow(heat, text_auto=".1f", color_continuous_scale="Magma", aspect="auto")
g4.update_xaxes(title=""); g4.update_yaxes(title="")
sb = px.sunburst(df.assign(priority=df.priority.astype(str)), path=["priority", "category"], color="priority", color_discrete_map=PCOL)
sb.update_traces(insidetextorientation="radial")

# ---- Community (GitHub / StackOverflow)
c1 = px.histogram(df, x=gh, nbins=40, color_discrete_sequence=["#4cc9f0"])
c1.update_layout(xaxis_title="GitHub similar issues", yaxis_title="Bugs", bargap=.05)
c2 = px.scatter(df, x=gh, y="github_top_issue_comments", color="priority", color_discrete_map=PCOL,
                opacity=.7, hover_data=["bug_id", "category"], log_x=True,
                category_orders={"priority": ["Low", "Medium", "High", "Critical"]})
c2.update_layout(xaxis_title="Similar issues (log)", yaxis_title="Top-issue comments")
rp = df.groupby("repo").size().sort_values(ascending=False).head(12).sort_values().reset_index(name="bugs")
c3 = px.bar(rp, x="bugs", y="repo", orientation="h", color="bugs", color_continuous_scale="Purp")
c3.update_coloraxes(showscale=False)
c4 = px.density_heatmap(df, x="stackoverflow_question_count", y=so, nbinsx=10, nbinsy=10,
                        color_continuous_scale="Inferno")
c4.update_layout(xaxis_title="StackOverflow questions", yaxis_title="Top answer score")
cm = df.groupby("category").agg(comments=("github_top_issue_comments", "mean"),
                                so=(so, "mean")).sort_values("comments").reset_index()
c5 = go.Figure([go.Bar(y=cm.category, x=cm.comments, name="Avg GitHub comments", orientation="h", marker_color="#ff7a45"),
                go.Bar(y=cm.category, x=cm.so, name="Avg SO answer score", orientation="h", marker_color="#3ddc97")])
c5.update_layout(barmode="group")

# ---- Security (CVE)
s1 = px.histogram(df, x="cve_top_severity_score", nbins=30, color_discrete_sequence=["#ef476f"])
s1.update_layout(xaxis_title="CVE severity score", yaxis_title="Bugs", bargap=.05)
sv = df.severity_band.value_counts().reindex(df.severity_band.cat.categories).reset_index()
sv.columns = ["band", "count"]
s2 = px.pie(sv, names="band", values="count", hole=.5,
            color_discrete_sequence=["#3ddc97", "#ffd166", "#ff7a45", "#ef476f"])
sc = df.groupby("category").agg(cve=(cve, "mean"), sev=("cve_top_severity_score", "mean")).sort_values("cve").reset_index()
s3 = px.bar(sc, x="cve", y="category", orientation="h", color="sev", color_continuous_scale="YlOrRd",
            labels={"cve": "Avg related CVEs", "sev": "Avg severity"})
s4 = px.scatter(df, x="cve_top_severity_score", y=conf, color="priority", color_discrete_map=PCOL,
                opacity=.65, trendline=None, category_orders={"priority": ["Low", "Medium", "High", "Critical"]})
s4.update_layout(xaxis_title="CVE severity", yaxis_title="Gemini fix confidence")
s5 = px.violin(df, x="priority", y=cve, color="priority", color_discrete_map=PCOL, box=True,
               category_orders={"priority": ["Low", "Medium", "High", "Critical"]})

# ---- Correlation / News
num = [conf, gh, "github_top_issue_comments", "stackoverflow_question_count", so, cve,
       "cve_top_severity_score", "news_related_count"]
short = ["Confidence", "GH issues", "GH comments", "SO questions", "SO score", "CVE count", "CVE severity", "News count"]
corr = df[num].corr(); corr.index = corr.columns = short
n1 = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto")
nc = df.groupby("category").news_related_count.mean().sort_values().reset_index()
n2 = px.bar(nc, x="news_related_count", y="category", orientation="h", color="news_related_count",
            color_continuous_scale="Viridis"); n2.update_coloraxes(showscale=False)
n2.update_layout(xaxis_title="Avg related news articles")
rad = df.groupby("priority", observed=True)[[conf, "cve_top_severity_score", so, "stackoverflow_question_count"]].mean()
radn = (rad - rad.min()) / (rad.max() - rad.min() + 1e-9)
n3 = go.Figure()
for p in radn.index:
    n3.add_trace(go.Scatterpolar(r=radn.loc[p].tolist() + [radn.loc[p].iloc[0]],
                                 theta=["Confidence", "CVE severity", "SO score", "SO questions", "Confidence"],
                                 fill="toself", name=str(p), line_color=PCOL[str(p)], opacity=.6))
n3.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(gridcolor="#25305a", showticklabels=False),
                            angularaxis=dict(gridcolor="#25305a")))
n4 = px.scatter(df, x="news_related_count", y=gh, color="category", opacity=.7, log_y=True,
                color_discrete_sequence=px.colors.qualitative.Vivid)
n4.update_layout(xaxis_title="Related news", yaxis_title="GitHub similar issues (log)")
pc = px.parallel_coordinates(df, dimensions=[conf, "cve_top_severity_score", so, "stackoverflow_question_count"],
                             color=conf, color_continuous_scale="Sunset",
                             labels={conf: "Confidence", "cve_top_severity_score": "CVE sev.",
                                     so: "SO score", "stackoverflow_question_count": "SO Qs"})
pc.update_layout(margin=dict(t=50))

# ------------------------------------------------------------------ 5. BUILD
tabs = {
 "Overview": [("Priority split", style(f1, 360), 4), ("Bugs per category", style(f2, 360, False), 8),
              ("Category x priority", style(f3, 380), 8), ("Fix-confidence distribution", style(f4, 380, False), 4),
              ("Priority > category treemap", style(tm, 420, False), 12)],
 "Gemini AI": [("Avg confidence by category", style(g1, 400, False), 6), ("Confidence by priority", style(g2, 400, False), 6),
               ("Technology mentioned in root-cause", style(g3, 380), 6), ("Avg confidence heat-map", style(g4, 380), 6),
               ("Priority > category sunburst", style(sb, 480, False), 12)],
 "Community": [("GitHub similar-issue counts", style(c1, 360, False), 4), ("Issues vs comments", style(c2, 360), 8),
               ("Top GitHub repos", style(c3, 400, False), 6), ("StackOverflow density", style(c4, 400), 6),
               ("Engagement by category", style(c5, 460), 12)],
 "Security (CVE)": [("CVE severity distribution", style(s1, 360, False), 6), ("Severity bands", style(s2, 360), 6),
                    ("Avg CVEs by category", style(s3, 420), 6), ("Severity vs AI confidence", style(s4, 420), 6),
                    ("CVE count by priority", style(s5, 380, False), 12)],
 "Correlations & News": [("Correlation matrix", style(n1, 440), 6), ("News coverage by category", style(n2, 440, False), 6),
                         ("Priority profile (normalised)", style(n3, 420), 4), ("News vs GitHub issues", style(n4, 420, False), 8),
                         ("Parallel coordinates", style(pc, 420, False), 12)],
}
build("BugAssist DataFusion Dashboard",
      f"{len(df):,} bugs fused from Gemini AI, GitHub, StackOverflow, CVE and News  |  columns with missing values excluded",
      kpis, tabs, os.path.join(BASE, "Dashboard", "bugassist_dashboard.html"),
      footer="Python - pandas - Plotly  |  BugAssist DataFusion visualization project")
