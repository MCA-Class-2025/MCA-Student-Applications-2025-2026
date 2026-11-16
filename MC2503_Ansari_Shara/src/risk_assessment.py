import pandas as pd
from rag_engine import RAGEngine
from risk_engine import RiskEngine
from llm_engine import LLMEngine


# ==========================================
# Load Clean Dataset
# ==========================================

df = pd.read_csv("data/processed/authentication_dataset_cleaned.csv")

# Read first authentication record
record = df.iloc[0]

# ==========================================
# Initialize Engines
# ==========================================

risk_engine = RiskEngine()
llm = LLMEngine()
rag = RAGEngine()
# ==========================================
# Calculate Risk
# ==========================================

result = risk_engine.calculate_risk(record)
knowledge = rag.load_knowledge()

# ==========================================
# Generate AI Explanation
# ==========================================

recommendation = llm.generate_recommendation(result, knowledge)

# ==========================================
# Display Authentication Record
# ==========================================

print("=" * 60)
print("AUTHENTICATION RECORD")
print("=" * 60)

fields_to_display = [
    "user_id",
    "ip_address",
    "device_type",
    "os_type",
    "browser",
    "success",
    "account_status",
    "failed_attempts",
    "session_duration",
    "role"
]

for field in fields_to_display:
    print(f"{field}: {record[field]}")

# ==========================================
# Display Risk Assessment
# ==========================================

print("\n" + "=" * 60)
print("RESPONSIBLE AI RISK ASSESSMENT")
print("=" * 60)

print(f"Risk Score           : {result['risk_score']}")
print(f"Risk Level           : {result['risk_level']}")
print(f"Threat Level         : {result['threat_level']}")
print(f"Suspicious Activity  : {result['suspicious_activity']}")
print(f"System Action        : {result['recommended_action']}")

print("\nReasons:")

for reason in result["reasons"]:
    print(f"- {reason}")

# ==========================================
# AI Explanation
# ==========================================

print("\nRecommendation:")
print(recommendation)