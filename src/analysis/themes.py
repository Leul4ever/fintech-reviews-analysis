"""
Keyword extraction + simple theme grouping logic.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import nltk
import pandas as pd
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

_NLTK_PACKAGES = ["punkt", "stopwords", "wordnet"]

_lemmatizer = None


def _get_lemmatizer() -> WordNetLemmatizer:
    global _lemmatizer
    if _lemmatizer is None:
        _ensure_nltk_data()
        _lemmatizer = WordNetLemmatizer()
    return _lemmatizer


def _ensure_nltk_data() -> None:
    for pkg in _NLTK_PACKAGES:
        try:
            nltk.data.find(f"tokenizers/{pkg}" if pkg == "punkt" else f"corpora/{pkg}")
        except LookupError:  # pragma: no cover - downloads once
            nltk.download(pkg, quiet=True)


DEFAULT_THEME_KEYWORDS = {
    "Account Access Issues": ["login", "pin", "otp", "password", "credential", "account", "activation", "access", "authenticate"],
    "Transaction Performance": ["transfer", "pending", "delay", "slow", "failed", "processing", "transaction", "speed", "loading"],
    "User Interface & Experience": ["ui", "interface", "design", "navigation", "layout", "experience", "user-friendly", "screen"],
    "Reliability & Stability": ["crash", "error", "bug", "freeze", "lag", "issue", "stability", "reliable", "crashes", "errors", "bugs"],
    "Customer Support & Communication": ["support", "service", "help", "respond", "call", "branch", "customer", "care", "contact"],
    "Feature Requests": ["feature", "add", "need", "would like", "option", "card", "request", "suggestion", "improve"],
}


def _clean_text(text: str, lemmatize: bool = False) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if lemmatize:
        lemmatizer = _get_lemmatizer()
        words = text.split()
        text = " ".join(lemmatizer.lemmatize(word) for word in words)
    return text


@dataclass
class ThemeSummary:
    bank: str
    theme: str
    keywords: List[str]
    coverage: float
    example_reviews: List[str]

    def to_dict(self) -> Dict[str, str]:
        return {
            "bank": self.bank,
            "theme": self.theme,
            "keywords": ", ".join(self.keywords),
            "coverage_pct": round(self.coverage * 100, 2),
            "example_reviews": ", ".join(self.example_reviews[:3]),
        }


class ThemeExtractor:
    """Extracts TF-IDF keywords and maps them into human-readable themes."""

    def __init__(
        self,
        theme_keywords: Optional[Dict[str, List[str]]] = None,
        max_features: int = 1000,
        top_k: int = 20,
    ) -> None:
        _ensure_nltk_data()
        self.theme_keywords = theme_keywords or DEFAULT_THEME_KEYWORDS
        self.max_features = max_features
        self.top_k = top_k
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            stop_words="english",
        )

    def extract_keywords_by_bank(self, df: pd.DataFrame, bank_column: str = "bank", text_column: str = "review") -> Dict[str, List[str]]:
        keywords: Dict[str, List[str]] = {}
        for bank, subset in df.groupby(bank_column):
            texts = subset[text_column].dropna().astype(str).apply(_clean_text).tolist()
            if not texts:
                keywords[bank] = []
                continue
            tfidf = self.vectorizer.fit_transform(texts)
            scores = tfidf.sum(axis=0)
            score_array = scores.A1
            terms = self.vectorizer.get_feature_names_out()
            ranked_indices = score_array.argsort()[::-1][: self.top_k]
            keywords[bank] = [terms[idx] for idx in ranked_indices]
        return keywords

    def _match_theme(self, keyword: str) -> str:
        for theme, hints in self.theme_keywords.items():
            if any(hint in keyword for hint in hints):
                return theme
        return "Other Feedback"

    def annotate_reviews_with_themes(
        self,
        df: pd.DataFrame,
        bank_column: str = "bank",
        text_column: str = "review",
    ) -> pd.DataFrame:
        """Annotate reviews with themes by matching review text against theme keywords."""
        def detect_themes(row: pd.Series) -> List[str]:
            text = _clean_text(row[text_column])
            matched = set()
            # Direct text matching against all theme keywords (not just top TF-IDF)
            for theme, keywords in self.theme_keywords.items():
                if any(keyword in text for keyword in keywords):
                    matched.add(theme)
            return sorted(matched) if matched else ["Other Feedback"]

        df = df.copy()
        df["themes"] = df.apply(detect_themes, axis=1)
        return df

    def summarize_themes(
        self,
        df: pd.DataFrame,
        bank_column: str = "bank",
        text_column: str = "review",
        id_column: str = "review_id",
    ) -> pd.DataFrame:
        summaries: List[ThemeSummary] = []
        bank_keywords = self.extract_keywords_by_bank(df, bank_column, text_column)
        for bank, subset in df.groupby(bank_column):
            total = max(len(subset), 1)
            themes_counts: Dict[str, List[Dict]] = {}
            for _, row in subset.iterrows():
                for theme in row["themes"]:
                    themes_counts.setdefault(theme, []).append(row.to_dict())

            for theme, rows in themes_counts.items():
                coverage = len(rows) / total
                sample_ids = [str(r.get(id_column, "")) for r in rows[:3]]
                keywords = bank_keywords.get(bank, [])
                summaries.append(
                    ThemeSummary(
                        bank=bank,
                        theme=theme,
                        keywords=keywords[:5],
                        coverage=coverage,
                        example_reviews=sample_ids,
                    )
                )

        summary_df = pd.DataFrame([s.to_dict() for s in summaries])
        summary_df = summary_df.sort_values(["bank", "coverage_pct"], ascending=[True, False])
        return summary_df

