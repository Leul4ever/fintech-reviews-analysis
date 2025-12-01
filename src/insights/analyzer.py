"""
Insights Analyzer: Extract drivers, pain points, and recommendations from review data.
"""
import ast
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class DriverPainPoint:
    """Represents a driver (positive) or pain point (negative) with evidence."""
    bank: str
    category: str  # 'driver' or 'pain_point'
    theme: str
    description: str
    evidence_count: int
    avg_rating: float
    sentiment_score: float
    example_reviews: List[str]


@dataclass
class BankInsights:
    """Complete insights for a single bank."""
    bank: str
    drivers: List[DriverPainPoint]
    pain_points: List[DriverPainPoint]
    avg_rating: float
    sentiment_score: float
    total_reviews: int


@dataclass
class Recommendation:
    """Recommendation for app improvement."""
    bank: str
    priority: str  # 'High', 'Medium', 'Low'
    theme: str
    recommendation: str
    rationale: str
    estimated_impact: str


class InsightsAnalyzer:
    """Analyze reviews to extract drivers, pain points, and generate recommendations."""

    def __init__(self, reviews_df: pd.DataFrame, theme_summary_df: pd.DataFrame) -> None:
        """
        Initialize analyzer with review and theme data.
        
        Args:
            reviews_df: DataFrame with reviews, sentiment, themes
            theme_summary_df: DataFrame with theme summaries per bank
        """
        self.reviews_df = reviews_df.copy()
        self.theme_summary_df = theme_summary_df.copy()
        
        # Parse themes if they're strings
        if 'themes' in self.reviews_df.columns:
            self.reviews_df['themes'] = self.reviews_df['themes'].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )

    def extract_drivers_pain_points(self, bank: str) -> Tuple[List[DriverPainPoint], List[DriverPainPoint]]:
        """
        Extract drivers (positive) and pain points (negative) for a bank.
        
        Args:
            bank: Bank name
            
        Returns:
            Tuple of (drivers, pain_points) lists
        """
        bank_reviews = self.reviews_df[self.reviews_df['bank'] == bank].copy()
        if bank_reviews.empty:
            return [], []

        drivers: List[DriverPainPoint] = []
        pain_points: List[DriverPainPoint] = []

        # Get themes for this bank from theme summary
        bank_themes = self.theme_summary_df[self.theme_summary_df['bank'] == bank]
        
        # Theme descriptions mapping
        theme_descriptions = {
            'Transaction Performance': 'Transaction speed, processing, and reliability',
            'User Interface & Experience': 'App design, navigation, and user-friendliness',
            'Reliability & Stability': 'App crashes, bugs, and technical stability',
            'Account Access Issues': 'Login problems, authentication, and access difficulties',
            'Customer Support & Communication': 'Support quality and responsiveness',
            'Feature Requests': 'Desired new features and functionality',
            'Other Feedback': 'General feedback and miscellaneous comments'
        }

        # Analyze each theme
        for _, theme_row in bank_themes.iterrows():
            theme = theme_row['theme']
            if theme == 'Other Feedback':
                continue  # Skip generic category
            
            # Get reviews with this theme
            theme_reviews = bank_reviews[
                bank_reviews['themes'].apply(lambda x: theme in x if isinstance(x, list) else False)
            ]
            
            if theme_reviews.empty:
                continue

            # Calculate metrics
            avg_rating = theme_reviews['rating'].mean()
            avg_sentiment = theme_reviews['sentiment_score'].mean()
            count = len(theme_reviews)
            
            # Get example reviews (top positive or negative)
            if avg_sentiment > 0:
                example_reviews = theme_reviews.nlargest(2, 'sentiment_score')['review'].tolist()
            else:
                example_reviews = theme_reviews.nsmallest(2, 'sentiment_score')['review'].tolist()
            
            # Truncate example reviews
            example_reviews = [r[:150] + '...' if len(r) > 150 else r for r in example_reviews[:2]]
            
            # Classify as driver or pain point (more lenient thresholds)
            is_driver = avg_sentiment > 0.1 and avg_rating >= 3.5
            is_pain_point = avg_sentiment < -0.1 and avg_rating <= 3.0
            
            description = theme_descriptions.get(theme, theme)
            
            if is_driver:
                drivers.append(DriverPainPoint(
                    bank=bank,
                    category='driver',
                    theme=theme,
                    description=description,
                    evidence_count=count,
                    avg_rating=avg_rating,
                    sentiment_score=avg_sentiment,
                    example_reviews=example_reviews
                ))
            elif is_pain_point:
                pain_points.append(DriverPainPoint(
                    bank=bank,
                    category='pain_point',
                    theme=theme,
                    description=description,
                    evidence_count=count,
                    avg_rating=avg_rating,
                    sentiment_score=avg_sentiment,
                    example_reviews=example_reviews
                ))

        # Sort by sentiment score
        drivers.sort(key=lambda x: x.sentiment_score, reverse=True)
        pain_points.sort(key=lambda x: x.sentiment_score)

        return drivers, pain_points

    def analyze_all_banks(self) -> Dict[str, BankInsights]:
        """Analyze all banks and return comprehensive insights."""
        banks = self.reviews_df['bank'].unique()
        insights: Dict[str, BankInsights] = {}

        for bank in banks:
            drivers, pain_points = self.extract_drivers_pain_points(bank)
            
            bank_reviews = self.reviews_df[self.reviews_df['bank'] == bank]
            avg_rating = bank_reviews['rating'].mean()
            avg_sentiment = bank_reviews['sentiment_score'].mean()
            
            insights[bank] = BankInsights(
                bank=bank,
                drivers=drivers,
                pain_points=pain_points,
                avg_rating=avg_rating,
                sentiment_score=avg_sentiment,
                total_reviews=len(bank_reviews)
            )

        return insights

    def compare_banks(self, bank1: str, bank2: str) -> Dict[str, any]:
        """Compare two banks across key metrics."""
        bank1_reviews = self.reviews_df[self.reviews_df['bank'] == bank1]
        bank2_reviews = self.reviews_df[self.reviews_df['bank'] == bank2]

        comparison = {
            'bank1': bank1,
            'bank2': bank2,
            'avg_rating': {
                bank1: bank1_reviews['rating'].mean(),
                bank2: bank2_reviews['rating'].mean(),
            },
            'avg_sentiment': {
                bank1: bank1_reviews['sentiment_score'].mean(),
                bank2: bank2_reviews['sentiment_score'].mean(),
            },
            'positive_share': {
                bank1: (bank1_reviews['sentiment_label'] == 'POSITIVE').mean(),
                bank2: (bank2_reviews['sentiment_label'] == 'POSITIVE').mean(),
            },
            'rating_distribution': {
                bank1: bank1_reviews['rating'].value_counts().sort_index().to_dict(),
                bank2: bank2_reviews['rating'].value_counts().sort_index().to_dict(),
            }
        }

        return comparison

    def generate_recommendations(
        self, insights: Dict[str, BankInsights]
    ) -> List[Recommendation]:
        """
        Generate improvement recommendations based on insights.
        
        Args:
            insights: Dictionary of BankInsights per bank
            
        Returns:
            List of recommendations
        """
        recommendations: List[Recommendation] = []

        # Mapping of pain points to recommendations
        pain_point_to_recommendation = {
            'Reliability & Stability': {
                'recommendation': 'Implement comprehensive crash reporting and automated testing',
                'rationale': 'High volume of stability issues indicates need for better QA and error handling',
                'impact': 'High - Will directly address user frustration and improve app ratings'
            },
            'Transaction Performance': {
                'recommendation': 'Optimize transaction processing pipeline and add transaction status tracking',
                'rationale': 'Transaction delays and failures are major pain points affecting user trust',
                'impact': 'High - Critical for banking app credibility'
            },
            'Account Access Issues': {
                'recommendation': 'Improve authentication system with biometric login and password recovery',
                'rationale': 'Login problems prevent users from accessing the app, causing immediate frustration',
                'impact': 'High - Blocks user access to all app features'
            },
            'Customer Support & Communication': {
                'recommendation': 'Implement in-app chat support and proactive communication system',
                'rationale': 'Users need accessible support channels within the app',
                'impact': 'Medium - Improves customer satisfaction and retention'
            },
            'User Interface & Experience': {
                'recommendation': 'Redesign key user flows based on user feedback and conduct UX testing',
                'rationale': 'UI/UX issues affect daily usability and user satisfaction',
                'impact': 'Medium - Improves overall user experience'
            },
            'Feature Requests': {
                'recommendation': 'Prioritize most requested features: budgeting tools, transaction history export, bill reminders',
                'rationale': 'Feature requests indicate gaps in current functionality',
                'impact': 'Medium - Enhances app value proposition'
            }
        }

        for bank, bank_insights in insights.items():
            # Generate recommendations from top pain points
            for pain_point in bank_insights.pain_points[:3]:  # Top 3 pain points
                if pain_point.theme in pain_point_to_recommendation:
                    rec_info = pain_point_to_recommendation[pain_point.theme]
                    
                    # Determine priority based on sentiment and evidence
                    if pain_point.sentiment_score < -0.7 and pain_point.evidence_count > 50:
                        priority = 'High'
                    elif pain_point.sentiment_score < -0.5:
                        priority = 'Medium'
                    else:
                        priority = 'Low'
                    
                    recommendations.append(Recommendation(
                        bank=bank,
                        priority=priority,
                        theme=pain_point.theme,
                        recommendation=rec_info['recommendation'],
                        rationale=rec_info['rationale'],
                        estimated_impact=rec_info['impact']
                    ))

        return recommendations

