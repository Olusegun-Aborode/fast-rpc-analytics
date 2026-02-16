#!/usr/bin/env python3
"""
Fast Protocol User Metrics Analysis Pipeline
"""

import os
import sys
import time

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
    from fetch_fast_protocol_data import collect_all_data, save_data
    from analyze_fast_protocol import load_data, calculate_metrics, generate_summary
    from visualize_fast_protocol import create_all_charts
    from dashboard_builder import build_interactive_dashboard
    from generate_report import create_report
except ImportError:
    try:
        from . import config
        from .fetch_fast_protocol_data import collect_all_data, save_data
        from .analyze_fast_protocol import load_data, calculate_metrics, generate_summary
        from .visualize_fast_protocol import create_all_charts
        from .dashboard_builder import build_interactive_dashboard
        from .generate_report import create_report
    except ImportError:
        print("Error: Could not import necessary modules. Check your path.")
        sys.exit(1)

def main():
    print("🚀 Starting Fast Protocol Analysis Pipeline...")
    start_time = time.time()

    # Step 1: Fetch data
    print("\n📥 Step 1/5: Fetching data from Fast Protocol API...")
    raw_data = collect_all_data()
    save_data(raw_data)
    print(f"✅ Data collected: {raw_data['total_unique_wallets']} unique wallets")

    # Step 2: Process and analyze
    print("\n📊 Step 2/5: Processing and analyzing data...")
    df = load_data()
    if df is not None:
        df = calculate_metrics(df)
        summary = generate_summary(df)
        print(f"✅ Analyzed {len(df)} collections")

        # Step 3: Create visualizations
        print("\n📈 Step 3/5: Creating visualizations...")
        charts = create_all_charts(df)
        print(f"✅ Generated {len(charts)} charts")

        # Step 4: Build dashboard
        print("\n🎨 Step 4/5: Building interactive dashboard...")
        dashboard_path = build_interactive_dashboard(df, summary)
        print(f"✅ Dashboard saved: {dashboard_path}")

        # Step 6: Fetch Wallet Balances (New)
        print("\n💰 Step 6/6: Fetching wallet balances...")
        try:
            from fetch_wallet_balances import fetch_all_wallet_balances
            balance_data = fetch_all_wallet_balances()
            if balance_data:
                summary['total_wallet_value'] = balance_data['total_value_usd']
                summary['avg_wallet_value'] = balance_data['avg_value_usd']
                print(f"✅ Total Wallet Value: ${balance_data['total_value_usd']:,.2f}")
            else:
                summary['total_wallet_value'] = 0
                summary['avg_wallet_value'] = 0
                print("⚠️  Could not fetch wallet balances.")
        except ImportError:
            print("⚠️  Wallet balance module not found, skipping.")
            summary['total_wallet_value'] = 0

        # Step 5: Generate report (Moved after balance fetch to include data)
        print("\n📝 Step 5/6: Generating analysis report...")
        report_path = create_report(df, summary)
        print(f"✅ Report saved: {report_path}")
        
        total_time = time.time() - start_time
        print(f"\n✨ Analysis complete in {total_time:.2f} seconds!")
        print(f"\n📂 Outputs available in: {config.OUTPUT_DIR}")
        print(f"   - Dashboard: {dashboard_path}")
        print(f"   - Report: {report_path}")
        print(f"   - Data: fast_protocol_data.json")
        print(f"   - CSV: fast_protocol_collections.csv")
    else:
        print("❌ Error: Failed to load data for analysis.")

if __name__ == "__main__":
    main()
