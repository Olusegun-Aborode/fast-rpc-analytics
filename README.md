# FAST Protocol Analytics Dashboard

An interactive Streamlit dashboard for analyzing FAST Protocol user community data.

## Features

- Real-time data refresh from FAST Protocol API
- Key metrics display (Total Wallets, Total Value, Collections, Avg Wallet Value)
- Interactive collection performance visualization
- Wallet balances table with Etherscan links
- Clean, professional interface

## Live Dashboard

🔗 [View Live Dashboard](https://your-app-name.streamlit.app) *(Update this after deployment)*

## Local Development

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd fast_protocol_analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
streamlit run streamlit_app.py
```

The dashboard will be available at `http://localhost:8501`

## Deployment

This app is deployed on Streamlit Community Cloud. Any push to the main branch will automatically update the live dashboard.

## Data Sources

- FAST Protocol API: https://www.fastprotocol.io
- Wallet balances fetched via custom API integration

## Project Structure

```
fast_protocol_analysis/
├── streamlit_app.py          # Main dashboard application
├── config.py                 # Configuration settings
├── fetch_fast_protocol_data.py  # API data fetching
├── fetch_wallet_balances.py     # Wallet balance fetching
├── analyze_fast_protocol.py     # Data analysis functions
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── output/                  # Generated data and reports
```

## License

MIT License
