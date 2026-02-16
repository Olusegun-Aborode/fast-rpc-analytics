import json
import os
import sys

# Add the current directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def inspect():
    path = os.path.join(config.OUTPUT_DIR, 'wallet_balances.json')
    if not os.path.exists(path):
        print("No wallet balance file found.")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    wallets = data.get('wallet_balances', [])
    # Sort by balance_usd descending
    wallets.sort(key=lambda x: x['balance_usd'], reverse=True)

    print(f"Total Value: ${data.get('total_value_usd', 0):,.2f}")
    print(f"Top 10 Wallets:")
    for i, w in enumerate(wallets[:10]):
        print(f"{i+1}. {w['address']}: ${w['balance_usd']:,.2f} ({w.get('token_count', 0)} tokens)")

if __name__ == "__main__":
    inspect()
