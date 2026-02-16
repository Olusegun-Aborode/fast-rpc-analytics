import json
import csv
import os
import sys

# Add the current directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def export_wallets():
    json_path = os.path.join(config.OUTPUT_DIR, 'wallet_balances.json')
    csv_path = os.path.join(config.OUTPUT_DIR, 'fast_protocol_wallet_list.csv')
    
    if not os.path.exists(json_path):
        print("No wallet balance file found.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    wallets = data.get('wallet_balances', [])
    # Sort by balance_usd descending
    wallets.sort(key=lambda x: x['balance_usd'], reverse=True)

    print(f"Exporting {len(wallets)} wallets to {csv_path}...")
    
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Address', 'Balance USD', 'Token Count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for w in wallets:
            writer.writerow({
                'Address': w['address'],
                'Balance USD': f"{w['balance_usd']:.2f}",
                'Token Count': w.get('token_count', 0)
            })

    print(f"✅ Export complete: {csv_path}")
    return csv_path

if __name__ == "__main__":
    export_wallets()
