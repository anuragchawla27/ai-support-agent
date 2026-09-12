"""
Confidence scoring -- the primary guardrail. Combines retrieval relevance
score + LLM self-reported confidence into one score. Threshold is
configurable via CONFIDENCE_AUTO_RESOLVE_THRESHOLD (config.py), tested
against real queries rather than assumed.

Built: Day 11
"""
