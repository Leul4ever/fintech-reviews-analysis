"""
Task 4: Create visualizations for insights and recommendations.
"""
import ast
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

try:
    from wordcloud import WordCloud
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


def load_data():
    """Load all necessary data files."""
    reviews_df = pd.read_csv("data/processed/reviews_with_sentiment.csv")
    theme_summary_df = pd.read_csv("data/processed/theme_summary.csv")
    sentiment_summary_df = pd.read_csv("data/processed/sentiment_summary.csv")
    
    # Parse themes if they're strings
    if 'themes' in reviews_df.columns:
        reviews_df['themes'] = reviews_df['themes'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else x
        )
    
    return reviews_df, theme_summary_df, sentiment_summary_df


def plot_sentiment_by_bank_and_rating(reviews_df: pd.DataFrame, sentiment_summary_df: pd.DataFrame):
    """Plot 1: Sentiment trends by bank and rating."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Left: Mean sentiment by bank and rating
    ax1 = axes[0]
    pivot_data = sentiment_summary_df.pivot(index='rating', columns='bank', values='mean_sentiment')
    pivot_data.plot(kind='line', ax=ax1, marker='o', linewidth=2, markersize=8)
    ax1.axhline(0, color='black', linewidth=1, linestyle='--', alpha=0.3)
    ax1.set_xlabel('Star Rating', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Mean Sentiment Score', fontsize=12, fontweight='bold')
    ax1.set_title('Sentiment Trends by Bank and Rating', fontsize=14, fontweight='bold')
    ax1.legend(title='Bank', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Right: Sentiment distribution by bank
    ax2 = axes[1]
    sentiment_dist = reviews_df.groupby(['bank', 'sentiment_label']).size().unstack(fill_value=0)
    sentiment_dist_pct = sentiment_dist.div(sentiment_dist.sum(axis=1), axis=0) * 100
    sentiment_dist_pct.plot(kind='bar', stacked=True, ax=ax2, 
                           color=['#dc3545', '#ffc107', '#28a745'], width=0.8)
    ax2.set_xlabel('Bank', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Sentiment Distribution by Bank', fontsize=14, fontweight='bold')
    ax2.legend(title='Sentiment', fontsize=10)
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('data/processed/visualizations/sentiment_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: sentiment_analysis.png")
    plt.close()


def plot_rating_distributions(reviews_df: pd.DataFrame):
    """Plot 2: Rating distributions by bank."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Left: Rating distribution comparison
    ax1 = axes[0]
    rating_data = reviews_df.groupby(['bank', 'rating']).size().unstack(fill_value=0)
    rating_data.plot(kind='bar', ax=ax1, color=['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#20c997'], 
                     width=0.8, edgecolor='black', linewidth=0.5)
    ax1.set_xlabel('Bank', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Reviews', fontsize=12, fontweight='bold')
    ax1.set_title('Rating Distribution by Bank', fontsize=14, fontweight='bold')
    ax1.legend(title='Rating', labels=['1⭐', '2⭐', '3⭐', '4⭐', '5⭐'], fontsize=10)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Right: Average rating comparison
    ax2 = axes[1]
    avg_ratings = reviews_df.groupby('bank')['rating'].mean().sort_values(ascending=False)
    colors = ['#28a745' if r > 3.5 else '#ffc107' if r > 2.5 else '#dc3545' for r in avg_ratings.values]
    bars = ax2.barh(avg_ratings.index, avg_ratings.values, color=colors, edgecolor='black', linewidth=0.5)
    ax2.set_xlabel('Average Rating', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Bank', fontsize=12, fontweight='bold')
    ax2.set_title('Average Rating by Bank', fontsize=14, fontweight='bold')
    ax2.set_xlim(0, 5)
    ax2.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bank, rating) in enumerate(avg_ratings.items()):
        ax2.text(rating, i, f' {rating:.2f} ⭐', va='center', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('data/processed/visualizations/rating_distributions.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: rating_distributions.png")
    plt.close()


def plot_theme_analysis(reviews_df: pd.DataFrame, theme_summary_df: pd.DataFrame):
    """Plot 3: Theme coverage and sentiment by theme."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))
    
    # Top: Theme coverage by bank
    ax1 = axes[0]
    theme_pivot = theme_summary_df[theme_summary_df['theme'] != 'Other Feedback'].pivot(
        index='theme', columns='bank', values='coverage_pct'
    )
    theme_pivot.plot(kind='barh', ax=ax1, width=0.8, edgecolor='black', linewidth=0.5)
    ax1.set_xlabel('Coverage (%)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Theme', fontsize=12, fontweight='bold')
    ax1.set_title('Theme Coverage by Bank', fontsize=14, fontweight='bold')
    ax1.legend(title='Bank', fontsize=10)
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Bottom: Pain points vs drivers heatmap
    ax2 = axes[1]
    
    # Calculate sentiment by theme and bank
    theme_sentiment = []
    for bank in reviews_df['bank'].unique():
        bank_reviews = reviews_df[reviews_df['bank'] == bank]
        for _, row in bank_reviews.iterrows():
            themes = row['themes'] if isinstance(row['themes'], list) else []
            for theme in themes:
                if theme != 'Other Feedback':
                    theme_sentiment.append({
                        'bank': bank,
                        'theme': theme,
                        'sentiment': row['sentiment_score'],
                        'rating': row['rating']
                    })
    
    theme_sentiment_df = pd.DataFrame(theme_sentiment)
    if not theme_sentiment_df.empty:
        heatmap_data = theme_sentiment_df.groupby(['bank', 'theme'])['sentiment'].mean().unstack(fill_value=0)
        sns.heatmap(heatmap_data, annot=True, fmt='.3f', cmap='RdYlGn', center=0, 
                   ax=ax2, cbar_kws={'label': 'Mean Sentiment Score'}, 
                   linewidths=0.5, linecolor='gray')
        ax2.set_xlabel('Theme', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Bank', fontsize=12, fontweight='bold')
        ax2.set_title('Sentiment Heatmap: Themes vs Banks', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('data/processed/visualizations/theme_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: theme_analysis.png")
    plt.close()


def create_keyword_clouds(reviews_df: pd.DataFrame):
    """Plot 4: Keyword word clouds for each bank."""
    import os
    os.makedirs('data/processed/visualizations', exist_ok=True)
    
    banks = reviews_df['bank'].unique()
    n_banks = len(banks)
    
    fig, axes = plt.subplots(1, n_banks, figsize=(6*n_banks, 6))
    if n_banks == 1:
        axes = [axes]
    
    for idx, bank in enumerate(banks):
        ax = axes[idx]
        bank_reviews = reviews_df[reviews_df['bank'] == bank]
        
        # Combine all reviews for this bank
        text = ' '.join(bank_reviews['review'].astype(str).tolist())
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='white',
            max_words=100,
            colormap='viridis',
            relative_scaling=0.5,
            min_font_size=10
        ).generate(text)
        
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(f'{bank}\nKeyword Cloud', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('data/processed/visualizations/keyword_clouds.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: keyword_clouds.png")
    plt.close()


def plot_drivers_pain_points(insights_df: pd.DataFrame):
    """Plot 5: Drivers and Pain Points visualization."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left: Drivers
    ax1 = axes[0]
    drivers = insights_df[insights_df['type'] == 'Driver']
    if not drivers.empty:
        driver_summary = drivers.groupby(['bank', 'theme']).agg({
            'evidence_count': 'sum',
            'sentiment_score': 'mean'
        }).reset_index()
        
        driver_pivot = driver_summary.pivot(index='theme', columns='bank', values='evidence_count')
        driver_pivot.plot(kind='barh', ax=ax1, width=0.8, edgecolor='black', linewidth=0.5)
        ax1.set_xlabel('Evidence Count (Reviews)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Theme', fontsize=12, fontweight='bold')
        ax1.set_title('Drivers (Positive Themes)', fontsize=14, fontweight='bold', color='green')
        ax1.legend(title='Bank', fontsize=10)
        ax1.grid(True, alpha=0.3, axis='x')
    
    # Right: Pain Points
    ax2 = axes[1]
    pain_points = insights_df[insights_df['type'] == 'Pain Point']
    if not pain_points.empty:
        pain_point_summary = pain_points.groupby(['bank', 'theme']).agg({
            'evidence_count': 'sum',
            'sentiment_score': 'mean'
        }).reset_index()
        
        pain_point_pivot = pain_point_summary.pivot(index='theme', columns='bank', values='evidence_count')
        pain_point_pivot.plot(kind='barh', ax=ax2, width=0.8, edgecolor='black', linewidth=0.5, color='red')
        ax2.set_xlabel('Evidence Count (Reviews)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Theme', fontsize=12, fontweight='bold')
        ax2.set_title('Pain Points (Negative Themes)', fontsize=14, fontweight='bold', color='red')
        ax2.legend(title='Bank', fontsize=10)
        ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('data/processed/visualizations/drivers_pain_points.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: drivers_pain_points.png")
    plt.close()


def main():
    """Main function to create all visualizations."""
    print("=" * 60)
    print("🎨 Task 4: Creating Visualizations")
    print("=" * 60)
    
    # Create output directory
    import os
    os.makedirs('data/processed/visualizations', exist_ok=True)
    
    # Load data
    print("\n📂 Loading data...")
    reviews_df, theme_summary_df, sentiment_summary_df = load_data()
    
    # Check if insights data exists
    try:
        insights_df = pd.read_csv('data/processed/insights_summary.csv')
    except FileNotFoundError:
        print("⚠️  insights_summary.csv not found. Run generate_insights.py first.")
        insights_df = pd.DataFrame()
    
    # Create visualizations
    print("\n🎨 Creating visualizations...")
    
    print("\n[1/5] Creating sentiment analysis plots...")
    plot_sentiment_by_bank_and_rating(reviews_df, sentiment_summary_df)
    
    print("[2/5] Creating rating distribution plots...")
    plot_rating_distributions(reviews_df)
    
    print("[3/5] Creating theme analysis plots...")
    plot_theme_analysis(reviews_df, theme_summary_df)
    
    print("[4/5] Creating keyword clouds...")
    if HAS_WORDCLOUD:
        try:
            create_keyword_clouds(reviews_df)
        except Exception as e:
            print(f"⚠️  Warning: Could not create word clouds: {e}")
            print("   (Skipping word cloud generation...)")
    else:
        print("⚠️  WordCloud not available. Install with: pip install wordcloud")
        print("   (Skipping word cloud generation...)")
    
    print("[5/5] Creating drivers/pain points visualization...")
    if not insights_df.empty:
        plot_drivers_pain_points(insights_df)
    else:
        print("⚠️  Skipping drivers/pain points plot (insights data not available)")
    
    print("\n" + "=" * 60)
    print("✅ All visualizations created successfully!")
    print("=" * 60)
    print("\n📁 Visualizations saved to: data/processed/visualizations/")


if __name__ == "__main__":
    main()

