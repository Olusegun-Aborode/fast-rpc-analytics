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

# Known Hyperliquid EVM tokens — VERIFIED contract addresses only
# Symbol-based matching is insecure (anyone can deploy a token with any symbol)
# Only price tokens from these verified contracts:
HL_VERIFIED_TOKENS = {
    # HYPE-pegged (price × HYPE/USD)
    '0x5555555555555555555555555555555555555555': ('WHYPE', 'hype'),    # Official Wrapped HYPE
    '0xffaa4a3d97fe9107cef8a3f48c069f577ff76cc1': ('stHYPE', 'hype'),  # Thunderhead Staked HYPE
    '0x2831775cb5e64b1d892853893858a261e898fbeb': ('wHYPE', 'hype'),   # wHYPE (secondary)
    # Stablecoins (price = $1)
    '0xb88339cb7199b77e23db6e890353e22632ba630f': ('USDC', 'stable'),  # Circle USDC
    '0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34': ('USDe', 'stable'),  # Ethena USDe
}
