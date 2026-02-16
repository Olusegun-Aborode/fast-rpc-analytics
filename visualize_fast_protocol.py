import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import sys

# Add the current directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
    from analyze_fast_protocol import load_data, calculate_metrics
except ImportError:
    try:
        from . import config
        from .analyze_fast_protocol import load_data, calculate_metrics
    except ImportError:
        import config
        from analyze_fast_protocol import load_data, calculate_metrics

CHARTS_DIR = os.path.join(config.OUTPUT_DIR, "charts")

if not os.path.exists(CHARTS_DIR):
    os.makedirs(CHARTS_DIR)

def create_top_collections_chart(df):
    """Create a bar chart of top collections."""
    top_15 = df.head(15).sort_values('unique_wallets', ascending=True) # Ascending for correct bar order in h-bar

    fig = px.bar(
        top_15,
        x='unique_wallets',
        y='entity',
        orientation='h',
        title='Top 15 Collections by Unique Wallets',
        labels={'unique_wallets': 'Unique Wallets', 'entity': 'Collection'},
        color='unique_wallets',
        color_continuous_scale='Blues',
        text='unique_wallets'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(height=600, showlegend=False)
    return fig

def create_category_pie_chart(df):
    """Create a pie chart of wallet distribution by category."""
    category_totals = df.groupby('category')['unique_wallets'].sum().reset_index()

    fig = px.pie(
        category_totals,
        values='unique_wallets',
        names='category',
        title='Wallet Distribution by Collection Category',
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_distribution_chart(df):
    """Create a histogram of wallet counts."""
    fig = px.histogram(
        df,
        x='unique_wallets',
        nbins=20,
        title='Distribution of Wallet Counts Across Collections',
        labels={'unique_wallets': 'Unique Wallets', 'count': 'Number of Collections'},
        color_discrete_sequence=['#636EFA']
    )
    fig.update_layout(bargap=0.1)
    return fig

def create_category_comparison(df):
    """Create a bar chart comparing categories."""
    category_stats = df.groupby('category').agg({
        'unique_wallets': 'sum'
    }).reset_index()

    fig = px.bar(
        category_stats,
        x='category',
        y='unique_wallets',
        title='Total Unique Wallets by Category',
        labels={'unique_wallets': 'Total Unique Wallets', 'category': 'Category'},
        color='category',
        text='unique_wallets'
    )
    fig.update_traces(textposition='outside')
    return fig

def save_chart(fig, filename):
    """Save chart as HTML and static image (if supported/needed)."""
    # Saving as HTML guarantees interactivity and works without kaleido
    html_path = os.path.join(CHARTS_DIR, f"{filename}.html")
    fig.write_html(html_path)
    print(f"Saved chart to {html_path}")
    
    # Try saving as PNG if kaleido is installed, otherwise skip or handle gracefully
    # We didn't install kaleido in plan, so we stick to HTML or JSON for client-side rendering.
    # The dashboard plan uses Chart.js, but here we generate Plotly charts.
    # Wait, the plan for dashboard said "Main Charts... Top Collections Bar Chart (interactive)".
    # And "Export charts as PNG".
    # Without kaleido, `fig.write_image` fails.
    # I'll stick to HTML for now as it's interactive. 
    # Or I can output JSON to be embedded.
    # The dashboard builder plan said: "HTML + Chart.js".
    # If I use Chart.js for the dashboard, I might not strictly need Plotly images unless for the PDF report.
    # But `visualize_fast_protocol.py` was supposed to create charts.
    # I'll generate HTMLs which can be viewed directly.
    pass

def create_all_charts(df):
    """Generate all charts."""
    charts = {}
    
    print("Generating Top Collections Chart...")
    fig1 = create_top_collections_chart(df)
    save_chart(fig1, "top_collections")
    charts['top_collections'] = fig1

    print("Generating Category Pie Chart...")
    fig2 = create_category_pie_chart(df)
    save_chart(fig2, "category_distribution")
    charts['category_distribution'] = fig2

    print("Generating Distribution Histogram...")
    fig3 = create_distribution_chart(df)
    save_chart(fig3, "wallet_distribution")
    charts['wallet_distribution'] = fig3
    
    print("Generating Category Comparison Chart...")
    fig4 = create_category_comparison(df)
    save_chart(fig4, "category_comparison")
    charts['category_comparison'] = fig4

    return charts

if __name__ == "__main__":
    print("Loading data for visualization...")
    df = load_data()
    if df is not None:
        df = calculate_metrics(df)
        create_all_charts(df)
        print("\nVisualization complete!")
