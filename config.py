# config.py
import os

BASE_URL = "https://www.fastprotocol.io"
API_TIMEOUT = 30
RATE_LIMIT_DELAY = 0.5  # seconds between requests
MAX_RETRIES = 3
MAX_USERS_PER_ENTITY = 1000  # Limit users per entity for faster processing
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
DUNE_API_KEY='sim_2nUBjRsl4R5mY8cHlFORMlbE05rMj9Az'

# Alchemy Hyperliquid RPC
ALCHEMY_HL_URL = 'https://hyperliquid-mainnet.g.alchemy.com/v2/OoNwaQp1YBY03iK3ZMqx2'

# CoinGecko for token pricing
COINGECKO_PRICE_URL = 'https://api.coingecko.com/api/v3/simple/price'

# Known Hyperliquid EVM tokens (address -> symbol mapping)
HL_HYPE_TOKENS = {
    '0x2831775cb5e64b1d892853893858a261e898fbeb': 'wHYPE',
    '0x000b00ba5132aa6308aea44d44dc9bf98e0c086d': 'wHYPE',  # alternate
    '0x000beef24a2179e4fa3871450d329b6bec75ee9b': 'wHYPE',  # alternate
}
