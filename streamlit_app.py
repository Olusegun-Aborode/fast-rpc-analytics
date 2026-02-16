#!/usr/bin/env python3
"""
FAST Protocol User Community Analytics - Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
    from fetch_fast_protocol_data import collect_all_data, save_data
    from analyze_fast_protocol import load_data, calculate_metrics, generate_summary
    from fetch_wallet_balances import fetch_all_wallet_balances
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="FAST Protocol Analytics",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_analysis_data():
    """Load existing analysis data from files."""
    try:
        # Load collection data
        data_path = os.path.join(config.OUTPUT_DIR, 'fast_protocol_data.json')
        with open(data_path, 'r') as f:
            raw_data = json.load(f)
        
        # Load wallet balances
        balance_path = os.path.join(config.OUTPUT_DIR, 'wallet_balances.json')
        with open(balance_path, 'r') as f:
            balance_data = json.load(f)
        
        # Load and process CSV - IMPORTANT: Must call calculate_metrics to add category column
        df = load_data()
        if df is not None:
            df = calculate_metrics(df)  # This adds the 'category' column
        
        return raw_data, balance_data, df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None

def refresh_data():
    """Fetch fresh data from API."""
    with st.spinner("Fetching fresh data from FAST Protocol API..."):
        progress_bar = st.progress(0)
        
        # Step 1: Fetch protocol data
        progress_bar.progress(20)
        raw_data = collect_all_data()
        save_data(raw_data)
        
        # Step 2: Process data
        progress_bar.progress(50)
        df = load_data()
        df = calculate_metrics(df)
        
        # Step 3: Fetch wallet balances
        progress_bar.progress(70)
        balance_data = fetch_all_wallet_balances()
        
        progress_bar.progress(100)
        st.success("Data refreshed successfully!")
        
        # Clear cache to reload new data
        st.cache_data.clear()
        
    return raw_data, balance_data, df

def create_collection_bar_chart(df):
    """Create interactive bar chart for collection performance."""
    fig = px.bar(
        df.sort_values('unique_wallets', ascending=True).tail(10),
        x='unique_wallets',
        y='entity',
        orientation='h',
        title='Top 10 Collections by Wallet Count',
        labels={'unique_wallets': 'Number of Wallets', 'entity': 'Collection'},
        color='unique_wallets',
        color_continuous_scale='Blues',
        text='unique_wallets'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_title="Number of Wallets",
        yaxis_title="Collection"
    )
    return fig

def get_wallet_balances_table(balance_data):
    """Create wallet balances table with Etherscan links."""
    if not balance_data or 'wallet_balances' not in balance_data:
        return pd.DataFrame()
    
    wallets = balance_data['wallet_balances']
    
    # Sort wallets by balance (descending)
    sorted_wallets = sorted(wallets, key=lambda x: x.get('balance_usd', 0), reverse=True)
    
    data = []
    for wallet_info in sorted_wallets:
        address = wallet_info.get('address', '')
        balance_usd = wallet_info.get('balance_usd', 0)
        
        # Create Etherscan link
        etherscan_link = f"https://etherscan.io/address/{address}"
        
        data.append({
            'Wallet': address,
            'Etherscan': etherscan_link,
            'Balance': f"${balance_usd:,.2f}"
        })
    
    return pd.DataFrame(data)

# Main app
def main():
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<p class="main-header">FAST Protocol User Community Analytics</p>', unsafe_allow_html=True)
    with col2:
        if st.button("Refresh Data", use_container_width=True):
            raw_data, balance_data, df = refresh_data()
            st.rerun()
    
    # Load data
    raw_data, balance_data, df = load_analysis_data()
    
    if raw_data is None or df is None:
        st.warning("No data available. Click 'Refresh Data' to fetch data from the API.")
        return
    
    # Calculate summary metrics
    summary = generate_summary(df)
    total_wallets = raw_data.get('total_unique_wallets', 0)
    total_value = balance_data.get('total_value_usd', 0) if balance_data else 0
    avg_value = balance_data.get('avg_value_usd', 0) if balance_data else 0
    total_collections = len(df)
    last_updated = raw_data.get('timestamp', 'Unknown')
    
    # Display last updated time
    st.caption(f"Last Updated: {last_updated}")
    
    st.divider()
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Wallets",
            value=f"{total_wallets:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Total Value",
            value=f"${total_value:,.2f}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Collections",
            value=f"{total_collections}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Avg Wallet Value",
            value=f"${avg_value:,.2f}",
            delta=None
        )
    
    st.divider()
    
    # Collection Performance Section
    st.subheader("Collection Performance")
    
    if len(df) > 0:
        fig_bar = create_collection_bar_chart(df)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No collections data available.")
    
    st.divider()
    
    # Wallet Balances Section
    st.subheader("Wallet Balances")
    
    wallet_df = get_wallet_balances_table(balance_data)
    
    if not wallet_df.empty:
        # Display table with clickable Etherscan links
        st.dataframe(
            wallet_df,
            column_config={
                "Wallet": st.column_config.TextColumn("Wallet", width="large"),
                "Etherscan": st.column_config.LinkColumn("Etherscan Link", display_text="View on Etherscan"),
                "Balance": st.column_config.TextColumn("Balance (USD)", width="medium"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No wallet balance data available.")
    
    # Footer
    st.divider()
    st.caption("Built with Streamlit | Data source: FAST Protocol API")

if __name__ == "__main__":
    main()
