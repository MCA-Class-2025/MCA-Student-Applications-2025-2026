"""
config.py

Seed lists of real, publicly-documented Indicators of Compromise (IOCs)
used to demonstrate the VirusTotal and AbuseIPDB integrations.

Why seed lists instead of pulling IOCs from NSL-KDD
-----------------------------------------------------
NSL-KDD contains no IP addresses or file hashes (see docstrings in
modules/api/virustotal.py and modules/api/abuseipdb.py). Rather than
inventing IPs/hashes and falsely presenting them as "found in the
dataset", we query these APIs against real, independently-sourced,
public indicators:

- VT_SEED_HASHES: the EICAR antivirus test file — an industry-standard,
  publicly documented test artifact used worldwide to validate antivirus
  and threat-intel tooling without using live malware. Its SHA256 is
  published by EICAR itself.
- ABUSEIPDB_SEED_IPS: example IP addresses published in AbuseIPDB's own
  API documentation as demonstration lookups, plus two well-known public
  DNS resolvers (Google, Cloudflare) included as clean-reputation
  contrast cases.

Edit these lists to point at IOCs relevant to your own environment/logs
if you have them — the pipeline code does not change.
"""

# EICAR standard antivirus test file (SHA256) — safe, publicly documented.
VT_SEED_HASHES = [
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
]

# Example IPs: one flagged in AbuseIPDB's own public API documentation
# examples, plus two well-known clean public resolvers for contrast.
ABUSEIPDB_SEED_IPS = [
    "118.25.6.39",   # example malicious-reputation IP used in AbuseIPDB docs
    "8.8.8.8",       # Google Public DNS (expected: clean)
    "1.1.1.1",       # Cloudflare Public DNS (expected: clean)
]
