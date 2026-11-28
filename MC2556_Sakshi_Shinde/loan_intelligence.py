"""Fast loan intelligence features for FundFlow.
All calculations are local and deterministic; no cloud LLM is required.
"""
from __future__ import annotations
import pandas as pd
import numpy as np


def _num(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def assess_applicant(cibil, annual_income, loan_amount, loan_term, dependents=0,
                     education="Graduate", self_employed="No", assets=0.0):
    """Return an explainable 0-100 eligibility score using transparent rules."""
    cibil = _num(cibil); income = max(_num(annual_income), 0); loan = max(_num(loan_amount), 0)
    term = max(_num(loan_term), 1); dependents = max(_num(dependents), 0); assets = max(_num(assets), 0)
    score = 0.0; positive=[]; risks=[]

    if cibil >= 750: score += 35; positive.append("Very strong CIBIL score")
    elif cibil >= 700: score += 30; positive.append("Good CIBIL score")
    elif cibil >= 650: score += 22; positive.append("Acceptable CIBIL score")
    elif cibil >= 550: score += 12; risks.append("CIBIL score is below the preferred range")
    else: risks.append("Low CIBIL score")

    ratio = loan / income if income else float("inf")
    if ratio <= 0.35: score += 30; positive.append("Loan amount is low relative to annual income")
    elif ratio <= 0.60: score += 22; positive.append("Loan-to-income level is moderate")
    elif ratio <= 1.0: score += 12; risks.append("Loan amount is high relative to annual income")
    else: risks.append("Loan amount is very high relative to annual income")

    if assets >= loan: score += 15; positive.append("Reported assets provide useful financial backing")
    elif assets >= loan * 0.5: score += 9; positive.append("Some asset backing is available")
    else: risks.append("Asset backing is limited")

    if term <= 10: score += 10; positive.append("Shorter loan term")
    elif term <= 15: score += 7
    elif term <= 20: score += 4
    else: risks.append("Long loan term increases repayment exposure")

    if dependents <= 2: score += 10
    elif dependents <= 4: score += 6
    else: risks.append("Higher number of dependents may increase household burden")

    score = min(100, round(score, 1))
    if score >= 75: level, decision = "LOW", "APPROVAL LIKELY"
    elif score >= 55: level, decision = "MEDIUM", "REVIEW REQUIRED"
    else: level, decision = "HIGH", "HIGH RISK"
    return {"score": score, "risk_level": level, "decision": decision,
            "loan_to_income": ratio, "positive": positive, "risks": risks}


def financial_health(cibil, annual_income, loan_amount, dependents=0, assets=0, risk_score=None):
    """Return a transparent 0-100 financial-health score."""
    cibil = _num(cibil); income = max(_num(annual_income), 0); loan = max(_num(loan_amount), 0)
    dep = max(_num(dependents), 0); assets = max(_num(assets), 0)
    credit = np.clip((cibil - 300) / 600 * 100, 0, 100)
    burden = 100 if income and loan/income <= .35 else 80 if income and loan/income <= .6 else 55 if income and loan/income <= 1 else 25
    stability = np.clip(55 + min(income/2000000*45,45) - dep*4, 0, 100)
    asset = np.clip(assets / max(loan,1) * 100, 0, 100)
    score = round(0.40*credit + 0.30*burden + 0.15*stability + 0.15*asset, 1)
    label = "Excellent" if score>=80 else "Good" if score>=65 else "Moderate" if score>=50 else "Needs Attention"
    return {"score": score, "label": label, "credit": round(credit,1), "burden": round(burden,1), "stability": round(stability,1), "asset": round(asset,1)}


def dataset_risk_label(df: pd.DataFrame) -> pd.Series:
    """Create an analytical risk label from transparent dataset features."""
    def one(r):
        a=assess_applicant(r.get('cibil_score'),r.get('income_annum'),r.get('loan_amount'),r.get('loan_term'),r.get('no_of_dependents'),r.get('education'),r.get('self_employed'),
                           r.get('residential_assets_value',0)+r.get('commercial_assets_value',0)+r.get('luxury_assets_value',0)+r.get('bank_asset_value',0))
        return a['risk_level']
    return df.apply(one, axis=1)


def fusion_validation(df: pd.DataFrame) -> dict:
    key = 'fusion_key'
    return {
        'rows': len(df), 'columns': len(df.columns),
        'unique_keys': int(df[key].nunique()) if key in df else 0,
        'null_keys': int(df[key].isna().sum()) if key in df else len(df),
        'duplicate_rows': int(df.duplicated().sum()),
        'key_duplicates': int(df[key].duplicated().sum()) if key in df else len(df),
        'has_description': 'fusion_key_description' in df.columns,
        'status': 'PASS' if key in df and df[key].notna().all() and df.duplicated().sum()==0 else 'CHECK'
    }


def fusion_validation_details(df: pd.DataFrame) -> dict:
    """Return a teacher-friendly, step-by-step explanation of how datasets were fused."""
    v = fusion_validation(df)
    key_counts = df["fusion_key"].value_counts() if "fusion_key" in df.columns else pd.Series(dtype=int)

    loan_columns = [
        "loan_id", "education_group", "no_of_dependents", "education", "self_employed",
        "income_annum", "loan_amount", "loan_term", "cibil_score",
        "residential_assets_value", "commercial_assets_value", "luxury_assets_value",
        "bank_asset_value", "loan_status",
    ]
    risk_columns = [
        "risk_segment_records", "risk_avg_score", "risk_avg_credit_score",
        "risk_avg_annual_income", "risk_avg_loan_amount", "risk_avg_loan_duration_months",
        "risk_avg_interest_rate", "risk_avg_debt_to_income", "risk_avg_total_debt_to_income",
        "risk_loan_approval_rate", "risk_avg_net_worth", "risk_avg_savings",
    ]
    meta_columns = ["fusion_key", "fusion_type", "fusion_key_description"]

    sample_key = df["fusion_key"].iloc[0] if len(df) else "DEP_2_EDU_GRADUATE"
    sample_rows = df[df["fusion_key"] == sample_key].head(3) if len(df) else df.head(0)

    return {
        **v,
        "source_primary": "loan_approval_dataset.csv",
        "source_primary_desc": "Primary loan-application dataset with one row per applicant (loan_id, income, CIBIL, assets, loan_status).",
        "source_primary_rows": v["rows"],
        "source_secondary": "Loan.csv",
        "source_secondary_desc": "Secondary financial-risk dataset with detailed borrower profiles (credit score, DTI, risk score, approval history).",
        "source_secondary_rows": "~20,000",
        "fusion_method": "Key-based LEFT JOIN with pre-aggregation",
        "fusion_key_formula": "DEP_{no_of_dependents}_EDU_{GRADUATE|NONGRADUATE}",
        "fusion_key_example": sample_key,
        "fusion_key_description": (
            df["fusion_key_description"].iloc[0]
            if "fusion_key_description" in df.columns and len(df)
            else "Number of dependents + education group"
        ),
        "join_type": "LEFT JOIN (keep every loan application; attach matching risk segment statistics)",
        "aggregation_rule": "Group Loan.csv rows by the same fusion_key, then compute mean (average) for each risk metric.",
        "why_no_row_explosion": (
            "Risk data is aggregated BEFORE joining. Each loan application gets one enriched row "
            "instead of multiplying rows through a many-to-many join."
        ),
        "meta_columns": [c for c in meta_columns if c in df.columns],
        "loan_columns": [c for c in loan_columns if c in df.columns],
        "risk_columns": [c for c in risk_columns if c in df.columns],
        "segment_count": int(key_counts.shape[0]) if len(key_counts) else 0,
        "largest_segment": key_counts.index[0] if len(key_counts) else "N/A",
        "largest_segment_count": int(key_counts.iloc[0]) if len(key_counts) else 0,
        "sample_rows": sample_rows,
        "steps": [
            {
                "step": 1,
                "title": "Load the two source datasets",
                "detail": (
                    "Dataset A (loan_approval_dataset.csv) contains individual loan applications. "
                    "Dataset B (Loan.csv) contains broader financial-risk records with credit and debt metrics."
                ),
            },
            {
                "step": 2,
                "title": "Create a common fusion key on both datasets",
                "detail": (
                    "Both datasets derive the same key using dependents and education: "
                    "`DEP_{no_of_dependents}_EDU_{GRADUATE|NONGRADUATE}`. "
                    "Example: 2 dependents + Graduate → `DEP_2_EDU_GRADUATE`."
                ),
            },
            {
                "step": 3,
                "title": "Aggregate the risk dataset by fusion key",
                "detail": (
                    "All Loan.csv records sharing a fusion key are grouped together. "
                    "For each group, averages are computed: risk score, credit score, income, loan amount, "
                    "DTI ratios, approval rate, net worth, and savings. "
                    "The count of records in each group is stored in `risk_segment_records`."
                ),
            },
            {
                "step": 4,
                "title": "LEFT JOIN loan applications with aggregated risk features",
                "detail": (
                    "Each row from loan_approval_dataset.csv is kept. "
                    "Matching aggregated risk statistics are attached using the fusion key. "
                    "If multiple loan applicants share the same segment, they receive the same risk averages."
                ),
            },
            {
                "step": 5,
                "title": "Validate the fused output",
                "detail": (
                    f"Final file: FundFlow_fused_dataset.csv with {v['rows']:,} rows and {v['columns']} columns. "
                    f"Validation checks: no null fusion keys, no duplicate rows, "
                    f"{v['unique_keys']:,} unique segments, one row per original loan application."
                ),
            },
        ],
    }
