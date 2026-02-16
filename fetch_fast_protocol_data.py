import requests
import json
import time
import pandas as pd
from datetime import datetime
import os
import sys

# Add the current directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
except ImportError:
    # Fallback if running from a different directory context
    try:
        from . import config
    except ImportError:
        import config

def get_all_entities():
    """Fetch all available entities/collections."""
    url = f"{config.BASE_URL}/api/user-community-activity/entities"
    try:
        response = requests.get(url, timeout=config.API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and 'entities' in data:
            return data['entities']
        elif isinstance(data, list):
            return data
        else:
            print(f"Unexpected response format for entities: {type(data)}")
            return []
    except requests.RequestException as e:
        print(f"Error fetching entities: {e}")
        return []

def get_entity_stats(entity_name):
    """Fetch aggregate statistics for a specific entity."""
    url = f"{config.BASE_URL}/api/user-community-activity/stats"
    params = {'entity': entity_name}
    try:
        response = requests.get(url, params=params, timeout=config.API_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching stats for {entity_name}: {e}")
        return {}

def get_entity_users(entity_name, max_users=None):
    """
    Fetch users who claimed a specific collection.
    Handles pagination.
    """
    all_users = []
    limit = 200
    offset = 0
    
    print(f"  Fetching users for {entity_name}...", end="", flush=True)

    while True:
        # Check if we reached the max_users limit if specified
        if max_users and len(all_users) >= max_users:
            break
            
        url = f"{config.BASE_URL}/api/user-community-activity/entity/{entity_name}"
        params = {'limit': limit, 'offset': offset} # Assuming API supports offest/pagination this way based on description
        # Note: The plan mentioned 'limit' but didn't explicitly specify 'offset' or cursor in the description, 
        # but typically pagination requires it. The example showed just ?limit=200.
        # If the API uses cursor-based pagination or just returns random users, we might need to adjust.
        # Let's assume standard offset or that repeated calls return different data if we don't specify offset? 
        # Actually, the plan's code snippet for get_entity_users didn't use offset, it just checked if users were returned.
        # If the API doesn't support offset/page, we might get the same 200 users every time.
        # Let's re-read the plan's snippet carefully.
        # The plan snippet:
        # while len(all_users) < max_users:
        #    url = f"...?limit={limit}"
        #    response = requests.get(url)
        #    users = response.json()
        #    if not users: break
        #    all_users.extend(users)
        # 
        # This implies the API inherently handles "next page" or we aren't paginating correctly in the snippet.
        # WITHOUT an offset or page parameter, or a 'next' link, fetching the same URL repeatedly usually returns the same data.
        # However, for now, I will implement it as per the plan BUT adding an offset locally to be safe 
        # or checking if the API supports it. The prompt description said:
        # "limit (default 50, max 200)"
        # nothing about offset. 
        # Let's assume for now we might need to rely on the plan's logic or add a 'skip'/'offset' if typical.
        # I'll add 'offset' to the params just in case, leveraging standard common practices, 
        # but I will adhere to the loop structure.
        
        # Let's stick to the plan's loop but add an offset which is common.
        
        try:
            # We'll try passing offset, if API ignores it, we might get duplicates
            # which we can filter out later.
            
            response = requests.get(url, params=params, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            users = []
            if isinstance(data, list):
                users = data
            elif isinstance(data, dict):
                if 'users' in data:
                    users = data['users']
                elif 'data' in data:
                    users = data['data']
                else:
                    # Maybe the keys are user IDs or something? 
                    # Or maybe it's paginated with 'results' key?
                    print(f" Warning: Unexpected user response keys: {list(data.keys())}")
            
            if not users:
                print(" Done (No more users).")
                break
                
            # initial_count = len(all_users) # Unused
            all_users.extend(users)
            
            # If we didn't get a full page, we're likely done
            if len(users) < limit:
                print(f" Done ({len(all_users)} users).")
                break
            
            # Increment offset for next iteration
            offset += limit
            
            # Rate limiting
            time.sleep(config.RATE_LIMIT_DELAY)
            
            print(".", end="", flush=True)

        except requests.RequestException as e:
            print(f" Error: {e}")
            break
            
    return all_users

def collect_all_data():
    """Main function to consolidate all data."""
    print("Fetching all entities...")
    entities = get_all_entities()
    print(f"Found {len(entities)} entities: {entities}")

    collection_data = []
    all_wallets = set()

    for entity in entities:
        print(f"\nProcessing entity: {entity}")
        stats = get_entity_stats(entity)
        users = get_entity_users(entity, max_users=config.MAX_USERS_PER_ENTITY)

        # Extract wallet addresses
        # API response structure for users isn't fully detailed in plan, 
        # but plan assumes user['walletAddress'].
        # We need to be careful if key is different.
        # The plan says: "Returns: Array of user records with wallet addresses..."
        # And code says: user['walletAddress']
        
        wallet_addresses = []
        for user in users:
            # Try specific keys if 'walletAddress' isn't there, or just use it if we trust the plan
            # Let's trust the plan for now but add a fallback print if key missing
            if isinstance(user, dict):
                if 'wallet' in user:
                    wallet_addresses.append(user['wallet'])
                elif 'walletAddress' in user:
                    wallet_addresses.append(user['walletAddress'])
            elif isinstance(user, str): # Maybe it returns list of strings?
                wallet_addresses.append(user)
        
        unique_entity_wallets = set(wallet_addresses)
        all_wallets.update(unique_entity_wallets)

        collection_data.append({
            'entity': entity,
            'unique_wallets': len(unique_entity_wallets),
            'total_activities': len(users), # or use stats.get('totalActivities')
            'stats': stats,
            'users': users # We might want to save this or not depending on size. 
                           # Plan's save_data saves 'collection_data', so yes.
        })

    result = {
        'collections': collection_data,
        'total_unique_wallets': len(all_wallets),
        'timestamp': datetime.now().isoformat()
    }
    
    return result

def save_data(data, filename='fast_protocol_data.json'):
    output_path = os.path.join(config.OUTPUT_DIR, filename)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nData saved to {output_path}")

    # Also save as CSV for easy analysis
    # Flattening might be needed if structure is complex
    # The plan implementation:
    # df = pd.DataFrame(data['collections'])
    # df.to_csv('fast_protocol_collections.csv', index=False)
    
    # We should exclude the full 'users' list from the CSV to keep it manageable
    csv_data = []
    for item in data['collections']:
        row = item.copy()
        if 'users' in row:
            del row['users'] # Remove detailed user list for CSV summary
        # Flatten stats if needed
        if 'stats' in row and isinstance(row['stats'], dict):
            for k, v in row['stats'].items():
                row[f"stat_{k}"] = v
            del row['stats']
        csv_data.append(row)

    df = pd.DataFrame(csv_data)
    csv_path = os.path.join(config.OUTPUT_DIR, 'fast_protocol_collections.csv')
    df.to_csv(csv_path, index=False)
    print(f"CSV saved to {csv_path}")

if __name__ == "__main__":
    print(f"Starting data collection from {config.BASE_URL}...")
    start_time = time.time()
    
    data = collect_all_data()
    save_data(data)
    
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.2f} seconds.")
    print(f"Total Unique Wallets: {data['total_unique_wallets']}")
