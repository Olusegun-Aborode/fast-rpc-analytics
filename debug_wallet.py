import requests
import json
import os
import sys

# Add the current directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def debug_wallet(address):
    api_key = config.DUNE_API_KEY
    url = f"https://api.sim.dune.com/v1/evm/balances/{address}"
    headers = {'X-Sim-Api-Key': api_key}
    params = {
        'chain_ids': '1',
        'exclude_spam_tokens': 'true'
    }

    try:
        from fetch_wallet_balances import is_spam_token
    except ImportError:
        print("Could not import is_spam_token")
        return

    print(f"Fetching balances for {address}...")
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            balances = data.get('balances', [])
            
            print(f"\nRaw Token List ({len(balances)} items):")
            print(f"{'Symbol':<10} {'Value USD':<15} {'Name':<30} {'Status':<10}")
            print("-" * 80)
            
            total_usd = 0
            for b in balances:
                val = float(b.get('value_usd', 0) or 0)
                amount = b.get('amount', '0')
                symbol = b.get('symbol', 'N/A')
                name = b.get('name', 'N/A')
                
                is_spam = is_spam_token(b)
                status = "SPAM" if is_spam else "OK"
                
                if not is_spam:
                    total_usd += val
                    
                print(f"{symbol:<10} ${val:<14,.2f} {name:<30} {status:<10}")

            print("-" * 80)
            print(f"Total calculated (Filtered): ${total_usd:,.2f}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    wallet = "0x329752d18c51df5b182ad445619cb4028b1fa790"
    debug_wallet(wallet)
