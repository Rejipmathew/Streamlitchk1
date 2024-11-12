import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import matplotlib.pyplot as plt

# Streamlit app details
st.set_page_config(page_title="Financial Analysis", layout="wide")
with st.sidebar:
    st.title("Financial Analysis")
    ticker = st.text_input("Enter a stock ticker (e.g., TSLA)", "TSLA")
    period = st.selectbox("Enter a time frame", ("1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"), index=2)

    # Drop-down menu to select data type (Stock data or Options data)
    data_type = st.selectbox("Select Data Type", ["Stock Data", "Options Data"])

    # Options data selection on right sidebar if selected
    if data_type == "Options Data":
        show_options = True
        expiration_dates = []
        option_type = st.selectbox("Select Option Type", ("Call", "Put"), index=0)
        expiration_dates = []
    else:
        show_options = False
        option_type = None
    
    button = st.button("Submit for Stock Data")
    options_button = st.button("Submit for Options Data")

# Helper function to safely format numerical values
def safe_format(value, decimal_places=2):
    if isinstance(value, (int, float)):
        return f"{value:.{decimal_places}f}"
    return "N/A"

# Format market cap and enterprise value into something readable
def format_value(value):
    if isinstance(value, (int, float)):
        suffixes = ["", "K", "M", "B", "T"]
        suffix_index = 0
        while value >= 1000 and suffix_index < len(suffixes) - 1:
            value /= 1000
            suffix_index += 1
        return f"${value:.1f}{suffixes[suffix_index]}"
    return "N/A"

# Function to calculate and display Bollinger Bands
def plot_bollinger_bands(stock_data):
    stock_data['SMA'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['STD'] = stock_data['Close'].rolling(window=20).std()
    stock_data['Upper Band'] = stock_data['SMA'] + (stock_data['STD'] * 2)
    stock_data['Lower Band'] = stock_data['SMA'] - (stock_data['STD'] * 2)
    st.line_chart(stock_data[['Close', 'Upper Band', 'Lower Band']])

# Function to calculate and display RSI
def plot_rsi(stock_data):
    stock_data['RSI'] = ta.momentum.RSIIndicator(stock_data['Close'], window=14).rsi()
    st.line_chart(stock_data['RSI'])

# Function to calculate and display MFI (Money Flow Index)
def plot_mfi(stock_data):
    stock_data['MFI'] = ta.volume.MFIIndicator(stock_data['High'], stock_data['Low'], stock_data['Close'], stock_data['Volume'], window=14).money_flow_index()
    st.line_chart(stock_data['MFI'])

# Function to calculate the Put/Call Ratio (PCR)
def calculate_pcr(options_chain):
    if options_chain is not None:
        calls_volume = options_chain.calls['volume'].sum()
        puts_volume = options_chain.puts['volume'].sum()
        pcr = puts_volume / calls_volume if calls_volume > 0 else 0
        st.write(f"Put/Call Ratio (PCR): {pcr:.2f}")
    else:
        st.write("No options data available.")

# Function to calculate Max Pain
def calculate_max_pain(options_chain, ticker):
    if options_chain:
        strike_prices = options_chain.calls['strike'].values
        call_open_interest = options_chain.calls['openInterest'].values
        put_open_interest = options_chain.puts['openInterest'].values

        max_pain = None
        min_loss = float('inf')
        
        for strike in strike_prices:
            call_loss = sum(call_open_interest[strike_prices >= strike])
            put_loss = sum(put_open_interest[strike_prices <= strike])
            total_loss = call_loss + put_loss
            
            if total_loss < min_loss:
                min_loss = total_loss
                max_pain = strike
        
        st.write(f"Max Pain: {max_pain}")
    else:
        st.write("Max Pain data is not available.")

# Function to display Implied Volatility
def display_implied_volatility(options_chain):
    if options_chain:
        st.write("Implied Volatility (IV) data for the options chain:")
        st.write(options_chain.calls[['contractSymbol', 'impliedVolatility']])
        st.write(options_chain.puts[['contractSymbol', 'impliedVolatility']])

# Function to display Volatility Skew
def display_volatility_skew(options_chain):
    if options_chain:
        call_iv = options_chain.calls['impliedVolatility']
        put_iv = options_chain.puts['impliedVolatility']
        iv_diff = call_iv.mean() - put_iv.mean()
        st.write(f"Volatility Skew: {iv_diff:.2f}")
    else:
        st.write("Volatility Skew data is not available.")

# If Submit button is clicked for Stock Data
if button:
    if not ticker.strip():
        st.error("Please provide a valid stock ticker.")
    else:
        try:
            with st.spinner('Please wait...'):
                # Retrieve stock data
                stock = yf.Ticker(ticker)
                info = stock.info

                # Fetch stock history based on user-selected period
                if period == "1D":
                    history = stock.history(period="1d", interval="1h")
                elif period == "5D":
                    history = stock.history(period="5d", interval="1d")
                elif period == "1M":
                    history = stock.history(period="1mo", interval="1d")
                elif period == "6M":
                    history = stock.history(period="6mo", interval="1wk")
                elif period == "YTD":
                    history = stock.history(period="ytd", interval="1mo")
                elif period == "1Y":
                    history = stock.history(period="1y", interval="1mo")
                elif period == "5Y":
                    history = stock.history(period="5y", interval="3mo")
                
                chart_data = pd.DataFrame(history["Close"])
                st.line_chart(chart_data)

                col1, col2, col3 = st.columns(3)

                # Display stock information as a dataframe
                country = info.get('country', 'N/A')
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                market_cap = format_value(info.get('marketCap', 'N/A'))
                ent_value = format_value(info.get('enterpriseValue', 'N/A'))
                employees = info.get('fullTimeEmployees', 'N/A')

                stock_info = [
                    ("Stock Info", "Value"),
                    ("Country", country),
                    ("Sector", sector),
                    ("Industry", industry),
                    ("Market Cap", market_cap),
                    ("Enterprise Value", ent_value),
                    ("Employees", employees)
                ]
                
                df = pd.DataFrame(stock_info[1:], columns=stock_info[0])
                col1.dataframe(df, width=400, hide_index=True)
                
                # Display price information as a dataframe
                current_price = safe_format(info.get('currentPrice'))
                prev_close = safe_format(info.get('previousClose'))
                day_high = safe_format(info.get('dayHigh'))
                day_low = safe_format(info.get('dayLow'))
                ft_week_high = safe_format(info.get('fiftyTwoWeekHigh'))
                ft_week_low = safe_format(info.get('fiftyTwoWeekLow'))
                
                price_info = [
                    ("Price Info", "Value"),
                    ("Current Price", f"${current_price}"),
                    ("Previous Close", f"${prev_close}"),
                    ("Day High", f"${day_high}"),
                    ("Day Low", f"${day_low}"),
                    ("52 Week High", f"${ft_week_high}"),
                    ("52 Week Low", f"${ft_week_low}")
                ]
                
                df = pd.DataFrame(price_info[1:], columns=price_info[0])
                col2.dataframe(df, width=400, hide_index=True)

                # Plot Bollinger Bands, RSI, MFI
                plot_bollinger_bands(history)
                plot_rsi(history)
                plot_mfi(history)

        except Exception as e:
            st.exception(f"An error occurred: {e}")
    
# If Submit button is clicked for Options Data
if options_button:
    if not ticker.strip():
        st.error("Please provide a valid stock ticker.")
    else:
        try:
            with st.spinner('Please wait...'):
                # Retrieve options data for the selected ticker
                options_chain = stock.option_chain(option_type)
                
                # Display Option Indicators
                calculate_pcr(options_chain)
                display_implied_volatility(options_chain)
                display_volatility_skew(options_chain)
                calculate_max_pain(options_chain, ticker)

        except Exception as e:
            st.exception(f"An error occurred: {e}")
