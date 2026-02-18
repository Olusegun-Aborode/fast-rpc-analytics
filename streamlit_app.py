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

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import config
    from analyze_fast_protocol import load_data, calculate_metrics, generate_summary
    from fetch_wallet_balances import is_spam_token, get_wallet_balance_multi_chain, get_hype_price
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
def fetch_live_stats():
    """Fetch live collection stats directly from the Fast Protocol API."""
    try:
        # Fetch overall stats (single fast API call with all collection counts)
        stats_url = f"{config.BASE_URL}/api/user-community-activity/stats"
        response = requests.get(stats_url, timeout=config.API_TIMEOUT)
        response.raise_for_status()
        stats = response.json()

        # Build collection DataFrame from the byEntity breakdown
        by_entity = stats.get('byEntity', {})
        collections = []
        for entity, count in by_entity.items():
            collections.append({
                'entity': entity,
                'unique_wallets': count,
                'total_activities': count,
            })

        df = pd.DataFrame(collections)
        if not df.empty:
            df = calculate_metrics(df)

        raw_data = {
            'total_unique_wallets': stats.get('uniqueUsers', 0),
            'total_records': stats.get('totalRecords', 0),
            'by_chain': stats.get('byChain', {}),
            'timestamp': datetime.now().isoformat(),
        }

        return raw_data, df
    except Exception as e:
        st.warning(f"Could not fetch live data: {e}. Falling back to saved data.")
        return None, None


def load_wallet_balances():
    """Load wallet balances from session_state or disk."""
    # Prefer session_state (from deep refresh)
    if 'wallet_balance_data' in st.session_state:
        return st.session_state['wallet_balance_data']
    # Fallback to disk
    try:
        balance_path = os.path.join(config.OUTPUT_DIR, 'wallet_balances.json')
        with open(balance_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def load_analysis_data():
    """Load live API data for collections, with wallet balances from session/disk."""
    # Always try live data first
    raw_data, df = fetch_live_stats()

    # Fallback to disk if the API call failed
    if raw_data is None or df is None:
        try:
            data_path = os.path.join(config.OUTPUT_DIR, 'fast_protocol_data.json')
            with open(data_path, 'r') as f:
                raw_data = json.load(f)
            df = load_data()
            if df is not None:
                df = calculate_metrics(df)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None, None, None

    # Wallet balances from session_state or disk
    balance_data = load_wallet_balances()

    return raw_data, balance_data, df


def _fetch_all_wallet_addresses():
    """Fetch all unique wallet addresses by querying each entity endpoint."""
    # Step 1: Get entity list
    entities_url = f"{config.BASE_URL}/api/user-community-activity/entities"
    resp = requests.get(entities_url, timeout=config.API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    entities = data.get('entities', data) if isinstance(data, dict) else data

    # Step 2: For each entity, fetch users (paginated)
    all_wallets = set()
    for entity in entities:
        offset = 0
        limit = 200
        while True:
            url = f"{config.BASE_URL}/api/user-community-activity/entity/{entity}"
            r = requests.get(url, params={'limit': limit, 'offset': offset}, timeout=config.API_TIMEOUT)
            r.raise_for_status()
            users = r.json()
            if isinstance(users, dict):
                users = users.get('users', users.get('data', []))
            if not users:
                break
            for user in users:
                if isinstance(user, dict):
                    addr = user.get('wallet') or user.get('walletAddress')
                    if addr:
                        all_wallets.add(addr)
                elif isinstance(user, str):
                    all_wallets.add(user)
            if len(users) < limit:
                break
            offset += limit
    return list(all_wallets)


def refresh_data():
    """Deep refresh: fetch wallet balances across Ethereum + Hyperliquid."""
    try:
        status = st.status("🔄 Deep Refresh in progress...", expanded=True)

        # Step 1: Fetch wallet addresses from Fast Protocol API
        status.update(label="📡 Fetching wallet addresses from API...")
        wallets = _fetch_all_wallet_addresses()
        st.write(f"Found **{len(wallets)}** unique wallets to scan")

        if not wallets:
            st.error("No wallet addresses found from the API.")
            return None, None, None

        if not hasattr(config, 'DUNE_API_KEY') or not config.DUNE_API_KEY:
            st.error("DUNE_API_KEY not configured. Cannot fetch wallet balances.")
            return None, None, None

        # Step 1b: Get HYPE price upfront
        hype_price = get_hype_price()
        st.write(f"HYPE price: **${hype_price:,.2f}**")

        # Step 2: Multi-chain balance scan (Ethereum via Dune + Hyperliquid via Alchemy)
        status.update(label=f"💰 Scanning {len(wallets)} wallets (ETH + Hyperliquid)...")
        progress_bar = st.progress(0)
        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_wallet = {
                executor.submit(get_wallet_balance_multi_chain, w, config.DUNE_API_KEY): w
                for w in wallets
            }
            for future in as_completed(future_to_wallet):
                result = future.result()
                results.append(result)
                completed += 1
                progress_bar.progress(completed / len(wallets))

        # Step 3: Calculate totals
        total_value = sum(r.get('balance_usd', 0) for r in results)
        total_eth = sum(r.get('eth_balance_usd', 0) for r in results)
        total_hl = sum(r.get('hl_balance_usd', 0) for r in results)
        successful = sum(1 for r in results if r.get('success'))
        avg_value = total_value / successful if successful else 0

        balance_data = {
            'total_value_usd': total_value,
            'total_eth_usd': total_eth,
            'total_hl_usd': total_hl,
            'avg_value_usd': avg_value,
            'hype_price': hype_price,
            'wallet_balances': results,
            'wallets_scanned': len(wallets),
            'wallets_successful': successful,
            'timestamp': datetime.now().isoformat(),
        }

        # Store in session_state so it persists across reruns
        st.session_state['wallet_balance_data'] = balance_data

        # Also try to save to disk (may fail on Cloud, that's OK)
        try:
            output_path = os.path.join(config.OUTPUT_DIR, 'wallet_balances.json')
            with open(output_path, 'w') as f:
                json.dump(balance_data, f, indent=2)
        except Exception:
            pass

        status.update(label=f"✅ Scanned {successful}/{len(wallets)} wallets — Total: ${total_value:,.2f} (ETH: ${total_eth:,.2f} | HL: ${total_hl:,.2f})", state="complete")
        progress_bar.progress(1.0)

        # Clear the stats cache so next load picks up fresh data
        st.cache_data.clear()

        # Reload live stats
        raw_data, df = fetch_live_stats()
        return raw_data, balance_data, df

    except Exception as e:
        st.error(f"Deep refresh failed: {e}")
        return None, None, None

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
    """Create wallet balances table with per-chain breakdown and explorer links."""
    if not balance_data or 'wallet_balances' not in balance_data:
        return pd.DataFrame()
    
    wallets = balance_data['wallet_balances']
    
    # Sort wallets by total balance (descending)
    sorted_wallets = sorted(wallets, key=lambda x: x.get('balance_usd', 0), reverse=True)
    
    data = []
    for wallet_info in sorted_wallets:
        address = wallet_info.get('address', '')
        total_usd = wallet_info.get('balance_usd', 0)
        eth_usd = wallet_info.get('eth_balance_usd', total_usd)  # fallback for old data
        hl_usd = wallet_info.get('hl_balance_usd', 0)
        hl_hype = wallet_info.get('hl_balance_hype', 0)
        
        etherscan_link = f"https://etherscan.io/address/{address}"
        hl_explorer_link = f"https://explorer.hyperliquid.xyz/address/{address}"
        
        data.append({
            'Wallet': address,
            'Total (USD)': f"${total_usd:,.2f}",
            'ETH (USD)': f"${eth_usd:,.2f}",
            'HL (USD)': f"${hl_usd:,.2f}",
            'HYPE': f"{hl_hype:,.4f}" if hl_hype else "—",
            'Etherscan': etherscan_link,
            'HL Explorer': hl_explorer_link,
        })
    
    return pd.DataFrame(data)

# Main app
def main():
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<p class="main-header">FAST Protocol User Community Analytics</p>', unsafe_allow_html=True)
        st.caption("🟢 Collection stats update live from the API")
    with col2:
        if st.button("🔄 Deep Refresh (Wallets)", use_container_width=True, help="Re-fetches wallet balances from Dune API. Collection stats already update automatically."):
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
    total_records = raw_data.get('total_records', raw_data.get('totalRecords', 0))
    total_value = balance_data.get('total_value_usd', 0) if balance_data else 0
    avg_value = balance_data.get('avg_value_usd', 0) if balance_data else 0
    total_collections = len(df)
    last_updated = raw_data.get('timestamp', 'Unknown')
    
    # Display last updated time
    st.caption(f"Stats fetched: {last_updated}")
    
    st.divider()
    
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Unique Users",
            value=f"{total_wallets:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Total Claims",
            value=f"{total_records:,}",
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
            label="Total Wallet Value",
            value=f"${total_value:,.2f}",
            delta=None,
            help="From last deep refresh"
        )
    
    with col5:
        st.metric(
            label="Avg Wallet Value",
            value=f"${avg_value:,.2f}",
            delta=None,
            help="From last deep refresh"
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
        st.dataframe(
            wallet_df,
            column_config={
                "Wallet": st.column_config.TextColumn("Wallet", width="medium"),
                "Total (USD)": st.column_config.TextColumn("Total", width="small"),
                "ETH (USD)": st.column_config.TextColumn("Ethereum", width="small"),
                "HL (USD)": st.column_config.TextColumn("Hyperliquid", width="small"),
                "HYPE": st.column_config.TextColumn("HYPE", width="small"),
                "Etherscan": st.column_config.LinkColumn("Etherscan", display_text="View"),
                "HL Explorer": st.column_config.LinkColumn("HL Explorer", display_text="View"),
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
