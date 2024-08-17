import streamlit as st
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
import time
import random
import os
import subprocess

# Ensure Playwright browsers are installed
def install_playwright_browsers():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        subprocess.run(["playwright", "install", "chromium"])

install_playwright_browsers()

# List of tickers to process
tickers = ["AEE", "REZ", "1AE", "IMC", "NRZ"]

def init_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    return context, browser

context, browser = init_browser()

def fetch_announcements_via_browser(ticker, retries=2, delay=1):
    page = context.new_page()
    url = f"https://www.asx.com.au/asx/1/company/{ticker}/announcements?count=20&market_sensitive=false"
    
    page.goto(url)
    time.sleep(random.uniform(1, 3))  # Reduce human pause simulation for better performance
    
    for attempt in range(retries):
        try:
            # Try to parse the JSON content
            data = page.evaluate("JSON.parse(document.querySelector('body').innerText)")
            if data:
                announcements = data['data']
                announcements.sort(key=lambda x: datetime.strptime(x['document_release_date'], '%Y-%m-%dT%H:%M:%S%z'), reverse=True)
                return ticker, announcements
            else:
                return ticker, None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)  # Wait before retrying, if retries remain
            else:
                st.error(f"Error occurred while parsing JSON for ticker {ticker}: {e}")
                return ticker, None

    return ticker, None

def check_trading_halts():
    trading_halt_tickers = []
    trading_halt_details = {}

    for ticker in tickers:
        ticker, announcements = fetch_announcements_via_browser(ticker)
        if announcements:
            trading_halt_announcements = [ann for ann in announcements if 'Trading Halt' in ann.get('header', '')]
            if trading_halt_announcements:
                trading_halt_tickers.append(ticker)
                trading_halt_details[ticker] = trading_halt_announcements

    trading_halt_tickers.sort(key=lambda x: tickers.index(x))
    
    return trading_halt_tickers, trading_halt_details

# Streamlit interface
st.title('ASX Announcements Viewer')

# Get trading halt tickers and details
trading_halt_tickers, trading_halt_details = check_trading_halts()

# Display tickers with 'Trading Halt' announcements at the top
if trading_halt_tickers:
    st.write("**Tickers with 'Trading Halt' announcements:**")
    st.write(", ".join(trading_halt_tickers))

# Dropdown menu for ticker selection
ticker = st.selectbox('Select Ticker', tickers)

if ticker:
    announcements = fetch_announcements_via_browser(ticker)[1]
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
            st.write(f"No 'Trading Halt' announcements found for ticker {ticker}")

        st.write("---")
        st.write(f"**Recent Announcements for {ticker}:**")
        for ann in announcements:
            st.write(f"**ID:** {ann.get('id')}")
            st.write(f"**Date:** {ann.get('document_release_date')}")
            st.write(f"**Header:** {ann.get('header')}")
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

# Ensure to close the browser when done
browser.close()
