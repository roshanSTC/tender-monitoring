"""
corrigendum_intelligence.py

Business Intelligence Layer

Responsibilities

1. Categorize Changes
2. Generate Summary
3. Calculate Risk Score
4. Assign Risk Level
"""

from typing import Dict, List


class CorrigendumIntelligence:

    CHANGE_CATEGORY_MAP = {

        "closing_date": {
            "category": "Schedule",
            "label": "Closing Date Changed",
            "score": 20,
        },

        "title": {
            "category": "Tender Details",
            "label": "Tender Title Changed",
            "score": 10,
        },

        "tender_url": {
            "category": "Documents",
            "label": "Tender Document Updated",
            "score": 5,
        },

        "corrigendum": {
            "category": "Corrigendum",
            "label": "Corrigendum Issued",
            "score": 10,
        },

        "corrigendum_url": {
            "category": "Corrigendum",
            "label": "Corrigendum Document Updated",
            "score": 5,
        },

    }

    # -----------------------------------------------------

    @classmethod
    def analyze(
        cls,
        changes: Dict,
    ) -> Dict:

        categories = set()

        summaries = []

        details = []

        risk_score = 0

        for field, values in changes.items():

            mapping = cls.CHANGE_CATEGORY_MAP.get(

                field,

                {
                    "category": "General",
                    "label": field,
                    "score": 5,
                }

            )

            categories.add(mapping["category"])

            summaries.append(mapping["label"])

            risk_score += mapping["score"]

            details.append({

                "field": field,

                "category": mapping["category"],

                "label": mapping["label"],

                "risk_score": mapping["score"],

                "old": values.get("old"),

                "new": values.get("new"),

            })

        risk_level = cls.calculate_risk_level(
            risk_score
        )

        return {

            "categories": sorted(categories),

            "summary": summaries,

            "details": details,

            "risk_score": risk_score,

            "risk_level": risk_level,

        }

    # -----------------------------------------------------

    @staticmethod
    def calculate_risk_level(score):

        if score >= 80:
            return "CRITICAL"

        if score >= 50:
            return "HIGH"

        if score >= 20:
            return "MEDIUM"

        return "LOW"