"""
Task 4: Generate insights (drivers, pain points) and recommendations.
"""
import sys
from pathlib import Path

import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.insights.analyzer import InsightsAnalyzer


def main():
    """Generate insights and recommendations for all banks."""
    print("=" * 60)
    print("🔍 Task 4: Generating Insights and Recommendations")
    print("=" * 60)

    # Load data
    print("\n📂 Loading data...")
    reviews_df = pd.read_csv("data/processed/reviews_with_sentiment.csv")
    theme_summary_df = pd.read_csv("data/processed/theme_summary.csv")
    
    print(f"✅ Loaded {len(reviews_df)} reviews")
    print(f"✅ Loaded theme data for {theme_summary_df['bank'].nunique()} banks")

    # Initialize analyzer
    analyzer = InsightsAnalyzer(reviews_df, theme_summary_df)
    
    # Analyze all banks
    print("\n📊 Analyzing insights for all banks...")
    insights = analyzer.analyze_all_banks()
    
    # Generate recommendations
    print("\n💡 Generating recommendations...")
    recommendations = analyzer.generate_recommendations(insights)
    
    # Print results
    print("\n" + "=" * 60)
    print("📋 INSIGHTS SUMMARY")
    print("=" * 60)
    
    for bank, bank_insights in insights.items():
        print(f"\n🏦 {bank}")
        print(f"   Average Rating: {bank_insights.avg_rating:.2f} ⭐")
        print(f"   Average Sentiment: {bank_insights.sentiment_score:.4f}")
        print(f"   Total Reviews: {bank_insights.total_reviews}")
        
        print(f"\n   ✅ Drivers ({len(bank_insights.drivers)}):")
        for driver in bank_insights.drivers[:3]:  # Top 3
            print(f"      • {driver.theme}: {driver.description}")
            print(f"        Evidence: {driver.evidence_count} reviews, "
                  f"Avg Rating: {driver.avg_rating:.2f} ⭐")
        
        print(f"\n   ❌ Pain Points ({len(bank_insights.pain_points)}):")
        for pain_point in bank_insights.pain_points[:3]:  # Top 3
            print(f"      • {pain_point.theme}: {pain_point.description}")
            print(f"        Evidence: {pain_point.evidence_count} reviews, "
                  f"Avg Rating: {pain_point.avg_rating:.2f} ⭐")
    
    # Bank comparison
    print("\n" + "=" * 60)
    print("📊 BANK COMPARISON")
    print("=" * 60)
    
    banks = list(insights.keys())
    if len(banks) >= 2:
        comparison = analyzer.compare_banks(banks[0], banks[1])
        print(f"\n{comparison['bank1']} vs {comparison['bank2']}:")
        print(f"   Average Rating: {comparison['avg_rating'][banks[0]]:.2f} vs {comparison['avg_rating'][banks[1]]:.2f}")
        print(f"   Average Sentiment: {comparison['avg_sentiment'][banks[0]]:.4f} vs {comparison['avg_sentiment'][banks[1]]:.4f}")
        print(f"   Positive Share: {comparison['positive_share'][banks[0]]:.1%} vs {comparison['positive_share'][banks[1]]:.1%}")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    
    for rec in recommendations[:10]:  # Top 10
        print(f"\n🏦 {rec.bank} - Priority: {rec.priority}")
        print(f"   Theme: {rec.theme}")
        print(f"   Recommendation: {rec.recommendation}")
        print(f"   Rationale: {rec.rationale}")
        print(f"   Impact: {rec.estimated_impact}")
    
    # Save to files
    print("\n💾 Saving insights to files...")
    
    # Save insights summary
    insights_data = []
    for bank, bank_insights in insights.items():
        for driver in bank_insights.drivers:
            insights_data.append({
                'bank': bank,
                'type': 'Driver',
                'theme': driver.theme,
                'description': driver.description,
                'evidence_count': driver.evidence_count,
                'avg_rating': driver.avg_rating,
                'sentiment_score': driver.sentiment_score
            })
        for pain_point in bank_insights.pain_points:
            insights_data.append({
                'bank': bank,
                'type': 'Pain Point',
                'theme': pain_point.theme,
                'description': pain_point.description,
                'evidence_count': pain_point.evidence_count,
                'avg_rating': pain_point.avg_rating,
                'sentiment_score': pain_point.sentiment_score
            })
    
    insights_df = pd.DataFrame(insights_data)
    insights_df.to_csv('data/processed/insights_summary.csv', index=False)
    
    # Save recommendations
    recs_data = [{
        'bank': rec.bank,
        'priority': rec.priority,
        'theme': rec.theme,
        'recommendation': rec.recommendation,
        'rationale': rec.rationale,
        'estimated_impact': rec.estimated_impact
    } for rec in recommendations]
    
    recs_df = pd.DataFrame(recs_data)
    recs_df.to_csv('data/processed/recommendations.csv', index=False)
    
    print("✅ Saved insights_summary.csv")
    print("✅ Saved recommendations.csv")
    print("\n✅ Insights generation complete!")


if __name__ == "__main__":
    main()

