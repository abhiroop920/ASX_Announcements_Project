import streamlit as st
import requests
from datetime import datetime

def fetch_announcements(ticker):
    url = f"https://www.asx.com.au/asx/1/company/{ticker}/announcements?count=20&market_sensitive=false"
    headers = {
    'Authority': 'www.asx.com.au',  # Optional, not typically needed
    'Method': 'GET',                # Optional, not typically needed
    'Path': '/asx/1/company/AEE/announcements?count=20&market_sensitive=false',  # Optional, not typically needed
    'Scheme': 'https',              # Optional, not typically needed
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en-GB;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Cookie': 'JSESSIONID=.node104; nlbi_2835827_2708396=O2ihIGFbuQ7zQ5uu2S5TNgAAAAB0R6iDxDQhA5hzOrQ2eft3; affinity="5df11493f8c25962"; nlbi_2835827=TAwVbOOQrhsFSt0f2S5TNgAAAACJME3ibkWRVtKJy+Qovxlm; visid_incap_2835827=0zBSCjuHTYy+ppDyafJC4oqWvmYAAAAAREIPAAAAAACAXGW2AWIuT/zgLd+T5qjusNPGrpy26mSp; TS019c39fc=01856a822a67aa02a595ed5cd6115b8ec6c2090d45f6d7a5ac56417b4ba74d672c7976d9d545613870f267e5c7848e20d1917302b9; incap_ses_1000_2835827=5Hq4KMJcqgq15oK01rbgDYfJv2YAAAAAjOv07G4Zw2pLZsSWCXvSsw==',
    'Priority': 'u=0, i',
    'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"macOS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    try:
        response.raise_for_status()
        data = response.json()
        if data:
            announcements = data['data']
            announcements.sort(key=lambda x: datetime.strptime(x['document_release_date'], '%Y-%m-%dT%H:%M:%S%z'), reverse=True)
            return announcements
        else:
            return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f'HTTP error occurred for {ticker}: {http_err}')
    except requests.exceptions.RequestException as err:
        st.error(f'Request error occurred for {ticker}: {err}')
    except ValueError as ve:
        st.error(f"Failed to decode JSON from response for {ticker}: {ve}")
    return None

# List of tickers to process
tickers = ["AEE", "REZ", "1AE", "IMC", "NRZ"]

# Check for 'Trading Halt' announcements
def check_trading_halts():
    trading_halt_tickers = []
    trading_halt_details = {}
    for ticker in tickers:
        announcements = fetch_announcements(ticker)
        if announcements:
            trading_halt_announcements = [ann for ann in announcements if 'Trading Halt' in ann.get('header', '')]
            if trading_halt_announcements:
                trading_halt_tickers.append(ticker)
                trading_halt_details[ticker] = trading_halt_announcements
    return trading_halt_tickers, trading_halt_details

# Get trading halt tickers and details
trading_halt_tickers, trading_halt_details = check_trading_halts()

st.title('ASX Announcements Viewer')

# Display tickers with 'Trading Halt' announcements at the top
if trading_halt_tickers:
    st.write("**Tickers with 'Trading Halt' announcements:**")
    st.write(", ".join(trading_halt_tickers))

# Dropdown menu for ticker selection
ticker = st.selectbox('Select Ticker', tickers)

if ticker:
    announcements = fetch_announcements(ticker)
    if announcements:
        if ticker in trading_halt_details:
            st.write("---")
            st.write(f"**Trading Halt Announcements for {ticker}:**")
            trading_halt_announcements = trading_halt_details[ticker]
            st.write(f"{len(trading_halt_announcements)} announcement(s) found, with the ID(s)")
            for ann in trading_halt_announcements:
                st.write(f"**ID:** {ann.get('id')}")
        else:
            st.write("---")
            st.write(f"No 'Trading Halt' announcements here in {ticker} ticker.")

        st.write("---")
        st.write(f"**Recent Announcements for {ticker}:**")
        for ann in announcements:
            st.write(f"**ID:** {ann.get('id')}")
            st.write(f"**Date:** {ann.get('document_release_date')}")
            st.write(f"**Document Date:** {ann.get('document_date')}")
            st.write(f"**URL:** [Link to Announcement]({ann.get('url')})")
            st.write(f"**Header:** {ann.get('header')}")
            st.write(f"**Market Sensitive:** {'Yes' if ann.get('market_sensitive') else 'No'}")
            st.write(f"**Number of Pages:** {ann.get('number_of_pages')}")
            st.write(f"**Size:** {ann.get('size')}")
            st.write(f"**Legacy Announcement:** {'Yes' if ann.get('legacy_announcement') else 'No'}")
            st.write(f"**Issuer Code:** {ann.get('issuer_code')}")
            st.write(f"**Issuer Short Name:** {ann.get('issuer_short_name')}")
            st.write(f"**Issuer Full Name:** {ann.get('issuer_full_name')}")
            st.write("---")
    else:
        st.write(f"No announcements found for ticker {ticker}")
