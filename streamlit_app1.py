import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit app details
st.set_page_config(page_title="Financial Analysis", layout="wide")
with st.sidebar:
    st.title("Financial Analysis")
    ticker = st.text_input("Enter a stock ticker (e.g., AAPL)", "AAPL")
    period = st.selectbox("Enter a time frame", ("1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"), index=2)
    show_options = st.checkbox("Include Options Data", value=False)
    button = st.button("Submit")

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

# If Submit button is clicked
if button:
    if not ticker.strip():
        st.error("Please provide a valid stock ticker.")
    else:
        try:
            with st.spinner('Please wait...'):
                # Retrieve stock data
                stock = yf.Ticker(ticker)
                info = stock.info

                st.subheader(f"{ticker} - {info.get('longName', 'N/A')}")

                # Plot historical stock price data
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

                # Display business metrics as a dataframe
                forward_eps = safe_format(info.get('forwardEps'))
                forward_pe = safe_format(info.get('forwardPE'))
                peg_ratio = safe_format(info.get('pegRatio'))
                dividend_rate = safe_format(info.get('dividendRate'))
                dividend_yield = safe_format(info.get('dividendYield') * 100) if info.get('dividendYield') is not None else "N/A"
                recommendation = info.get('recommendationKey', 'N/A').capitalize()
                
                biz_metrics = [
                    ("Business Metrics", "Value"),
                    ("EPS (FWD)", forward_eps),
                    ("P/E (FWD)", forward_pe),
                    ("PEG Ratio", peg_ratio),
                    ("Div Rate (FWD)", f"${dividend_rate}"),
                    ("Div Yield (FWD)", f"{dividend_yield}%"),
                    ("Recommendation", recommendation)
                ]
                
                df = pd.DataFrame(biz_metrics[1:], columns=biz_metrics[0])
                col3.dataframe(df, width=400, hide_index=True)

                # Include options data if selected
                if show_options:
                    st.subheader("Options Data")
                    expiration_dates = stock.options
                    selected_date = st.selectbox("Select an expiration date", expiration_dates)

                    if selected_date:
                        options_chain = stock.option_chain(selected_date)
                        
                        # Display options volume and open interest
                        call_data = options_chain.calls
                        put_data = options_chain.puts
                        
                        st.write(f"**Calls for {selected_date}**")
                        st.dataframe(call_data)

                        st.write(f"**Puts for {selected_date}**")
                        st.dataframe(put_data)

                        # Calculate and display the Put/Call Ratio
                        call_volume = call_data['volume'].sum() if not call_data.empty else 0
                        put_volume = put_data['volume'].sum() if not put_data.empty else 0
                        put_call_ratio = safe_format(put_volume / call_volume) if call_volume > 0 else "N/A"
                        st.write(f"**Put/Call Ratio**: {put_call_ratio}")

                        # Display options Greeks (Delta, Theta, Vega)
                        st.subheader("Options Greeks (for selected contracts)")
                        call_data['delta'] = call_data['delta'].apply(safe_format)
                        call_data['theta'] = call_data['theta'].apply(safe_format)
                        call_data['vega'] = call_data['vega'].apply(safe_format)

                        put_data['delta'] = put_data['delta'].apply(safe_format)
                        put_data['theta'] = put_data['theta'].apply(safe_format)
                        put_data['vega'] = put_data['vega'].apply(safe_format)

                        st.write("**Calls Greeks**")
                        st.dataframe(call_data[['strike', 'delta', 'theta', 'vega']])

                        st.write("**Puts Greeks**")
                        st.dataframe(put_data[['strike', 'delta', 'theta', 'vega']])

        except Exception as e:
            st.exception(f"An error occurred: {e}")
