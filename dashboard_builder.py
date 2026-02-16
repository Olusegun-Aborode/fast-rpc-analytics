import os
import sys
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Add the current directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
    from analyze_fast_protocol import load_data, calculate_metrics, generate_summary
except ImportError:
    try:
        from . import config
        from .analyze_fast_protocol import load_data, calculate_metrics, generate_summary
    except ImportError:
        import config
        from analyze_fast_protocol import load_data, calculate_metrics, generate_summary

def build_interactive_dashboard(df, summary):
    """Generate the HTML dashboard."""
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
    template = env.get_template('dashboard.html')

    # Prepare data for Chart.js
    # Top Collections (Label: Entity, Value: Unique Wallets)
    top_collections = df.head(10).sort_values('unique_wallets', ascending=False)
    
    # Category Distribution
    category_counts = df.groupby('category')['unique_wallets'].sum().reset_index()

    chart_data = {
        'top_collections': {
            'labels': top_collections['entity'].tolist(),
            'values': top_collections['unique_wallets'].tolist()
        },
        'categories': {
            'labels': category_counts['category'].tolist(),
            'values': category_counts['unique_wallets'].tolist()
        }
    }

    output_html = template.render(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_unique_wallets=summary['total_unique_wallets'],
        total_claims=summary['total_claims'],
        total_collections=summary['total_collections'],
        top_collection=summary['top_collection'],
        top_collection_wallets=summary['top_collection_wallets'],
        avg_wallets=f"{summary['avg_wallets_per_collection']:.2f}",
        total_wallet_value=f"${summary.get('total_wallet_value', 0):,.2f}",
        table_data=df.to_dict('records'),
        chart_data=chart_data
    )

    output_path = os.path.join(config.OUTPUT_DIR, 'fast_protocol_dashboard.html')
    with open(output_path, 'w') as f:
        f.write(output_html)
    
    print(f"Dashboard generated at: {output_path}")
    return output_path

if __name__ == "__main__":
    print("Building dashboard...")
    df = load_data()
    if df is not None:
        df = calculate_metrics(df)
        summary = generate_summary(df)
        build_interactive_dashboard(df, summary)
