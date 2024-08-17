import streamlit as st
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright



# List of tickers to process
tickers = ["AEE", "REZ", "1AE", "IMC", "NRZ"]


subprocess.run([sys.executable, "-m", "playwright", "install"])
# Initialize Playwright and browser

def init_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    return context, browser


context, browser = init_browser()


# Use Playwright to visit the ASX website and extract the headers and cookies
def get_dynamic_headers():
    page = context.new_page()
    page.goto('https://www.asx.com.au/')

    # Extract headers and cookies
    headers = {
        'User-Agent': page.evaluate("navigator.userAgent;"),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
    }

    cookies = page.context.cookies()
    cookie_header = "; ".join([f"{cookie['name']}={cookie['value']}"for cookie in cookies])
    headers['Cookie'] = cookie_header

    return headers

# Fetch announcements using dynamic headers and cookies
def fetch_announcements(ticker, headers):
    url = f"https://www.asx.com.au/asx/1/company/{ticker}/announcements?count=20&market_sensitive=false"
    response = requests.get(url, headers=headers)

    try:
        response.raise_for_status()
        data = response.json()
        if data:
            announcements = data['data']
            announcements.sort(
                key=lambda x: datetime.strptime(x['document_release_date'], '%Y-%m-%dT%H:%M:%S%z'),
                reverse=True
            )
            return ticker, announcements
        else:
            return ticker, None 
    except requests.exceptions.HTTPError as http_err:
        return ticker, None 
    except requests.exceptions.RequestException as err:
        return ticker, None 
    except ValueError as ve:
        return ticker, None
    


def check_trading_halts(headers):
    trading_halt_tickers = []
    trading_halt_details = {}
    for ticker in tickers:
        ticker, announcements = fetch_announcements(ticker, headers)
        if announcements:
            trading_halt_announcements = [ann for ann in announcements if'Trading Halt'in ann.get('header', '')]
            if trading_halt_announcements:
                trading_halt_tickers.append(ticker)
                trading_halt_details[ticker] = trading_halt_announcements

    # Sort the tickers according to the original order in the tickers list
    trading_halt_tickers.sort(key=lambda x: tickers.index(x))

    return trading_halt_tickers, trading_halt_details

# Streamlit interface
st.title('ASX Announcements Viewer')

# Get dynamic headers once and reuse them
headers = get_dynamic_headers()

# Get trading halt tickers and details
trading_halt_tickers, trading_halt_details = check_trading_halts(headers)

# Display tickers with 'Trading Halt' announcements at the top
if trading_halt_tickers:
    st.write("**Tickers with 'Trading Halt' announcements:**")
    st.write(", ".join(trading_halt_tickers))

# Dropdown menu for ticker selection
ticker = st.selectbox('Select Ticker', tickers)

if ticker:
    announcements = fetch_announcements(ticker, headers)[1]
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
            st.write(f"**Market Sensitive:** {'Yes'if ann.get('market_sensitive') else'No'}")
            st.write(f"**Number of Pages:** {ann.get('number_of_pages')}")
            st.write(f"**Size:** {ann.get('size')}")
            st.write(f"**Legacy Announcement:** {'Yes'if ann.get('legacy_announcement') else'No'}")
            st.write(f"**Issuer Code:** {ann.get('issuer_code')}")
            st.write(f"**Issuer Short Name:** {ann.get('issuer_short_name')}")
            st.write(f"**Issuer Full Name:** {ann.get('issuer_full_name')}")
            st.write("---")
    else:
        st.write(f"No announcements found for ticker {ticker}")

# Ensure to close the browser when done
browser.close()
