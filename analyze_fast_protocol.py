import pandas as pd
import numpy as np
import json
import os
import sys

# Add the current directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
except ImportError:
    try:
        from . import config
    except ImportError:
        import config

def load_data(json_path=None):
    """Load raw data from JSON file."""
    if json_path is None:
        json_path = os.path.join(config.OUTPUT_DIR, 'fast_protocol_data.json')
    
    if not os.path.exists(json_path):
        print(f"Error: Data file not found at {json_path}")
        return None

    with open(json_path, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data['collections'])

def calculate_metrics(df):
    """Calculate key metrics for each collection."""
    if df is None or df.empty:
        return df

    # Sort by wallet count
    df = df.sort_values('unique_wallets', ascending=False).reset_index(drop=True)

    # Calculate percentages
    total_wallets = df['unique_wallets'].sum()
    if total_wallets > 0:
        df['percentage'] = (df['unique_wallets'] / total_wallets * 100).round(2)
    else:
        df['percentage'] = 0.0

    # Add rank
    df['rank'] = range(1, len(df) + 1)

    # Categorize collections
    nft_collections = ['pudgy', 'moonbirds', 'azuki', 'bayc', 'mayc', 'doodles',
                       'cryptopunks', 'meebits', 'beanz', 'bakc', 'otherdeed', 'yuga']
    defi_protocols = ['hyperliquid', 'aave', 'uniswap', 'compound', 'curve',
                      'balancer', 'sushiswap', 'dydx', 'lido', 'rocketpool']

    def categorize(entity):
        entity_lower = str(entity).lower()
        if any(nft in entity_lower for nft in nft_collections):
            return 'NFT'
        elif any(defi in entity_lower for defi in defi_protocols):
            return 'DeFi'
        else:
            return 'Other'

    df['category'] = df['entity'].apply(categorize)

    return df

def generate_summary(df):
    """Generate summary statistics from the analyzed dataframe."""
    if df is None or df.empty:
        return {}

    # Calculate total unique wallets across all collections
    all_wallets = set()
    if not df.empty and 'users' in df.columns:
        for users_list in df['users']:
            if isinstance(users_list, list):
                for user in users_list:
                    if isinstance(user, dict):
                        if 'wallet' in user:
                            all_wallets.add(user['wallet'])
                        elif 'walletAddress' in user:
                            all_wallets.add(user['walletAddress'])
                    elif isinstance(user, str):
                        all_wallets.add(user)
    
    summary = {
        'total_collections': len(df),
        'total_claims': int(df['unique_wallets'].sum()),
        'total_unique_wallets': len(all_wallets),
        'top_collection': df.iloc[0]['entity'] if len(df) > 0 else "N/A",
        'top_collection_wallets': int(df.iloc[0]['unique_wallets']) if len(df) > 0 else 0,
        'avg_wallets_per_collection': float(df['unique_wallets'].mean()),
        'median_wallets_per_collection': float(df['unique_wallets'].median()),
        'collections_by_category': df.groupby('category')['unique_wallets'].sum().to_dict()
    }
    return summary

if __name__ == "__main__":
    print("Loading and analyzing data...")
    df = load_data()
    
    if df is not None:
        df = calculate_metrics(df)
        summary = generate_summary(df)
        
        print("\nAnalysis Summary:")
        print("-" * 30)
        print(f"Total Collections: {summary['total_collections']}")
        print(f"Total Claims: {summary['total_claims']}")
        print(f"Top Collection: {summary['top_collection']} ({summary['top_collection_wallets']} wallets)")
        print(f"Avg Wallets/Collection: {summary['avg_wallets_per_collection']:.2f}")
        
        print("\nCategory Breakdown:")
        for cat, count in summary['collections_by_category'].items():
            print(f"  {cat}: {count} wallets")
            
        # Save analyzed data back to CSV with more details
        output_csv = os.path.join(config.OUTPUT_DIR, 'analyzed_collections.csv')
        
        # Drop complex columns like 'users' or 'stats' for CSV export if they complicate things
        # But 'stats' is a dict, pandas handles it poorly in one cell sometimes or stringifies it.
        # Let's drop 'users' and 'stats' for the clean CSV
        export_df = df.drop(columns=['users', 'stats'], errors='ignore')
        export_df.to_csv(output_csv, index=False)
        print(f"\nAnalyzed data saved to {output_csv}")
