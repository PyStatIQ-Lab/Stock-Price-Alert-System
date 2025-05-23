import streamlit as st
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
import time
import json
import os
from datetime import datetime

# Configuration file
CONFIG_FILE = 'stock_alerts_config.json'

def load_config():
    """Load configuration from JSON file"""
    if not os.path.exists(CONFIG_FILE):
        # Create default config if file doesn't exist
        default_config = {
            "stocks_to_monitor": {},
            "email_settings": {
                "sender_email": "",
                "sender_password": "",
                "receiver_email": "",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587
            },
            "check_interval": 60  # seconds
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(config):
    """Save configuration to JSON file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_current_price(ticker):
    """Get current price of a stock using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d')
        return data['Close'].iloc[-1]
    except Exception as e:
        st.error(f"Error getting price for {ticker}: {e}")
        return None

def send_email_alert(config, ticker, current_price, resistance_level):
    """Send email notification when resistance is broken"""
    email_settings = config['email_settings']
    
    subject = f"ALERT: {ticker} broke resistance level!"
    body = (f"Stock {ticker} has broken through your resistance level of {resistance_level}.\n"
            f"Current price: {current_price}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = email_settings['sender_email']
    msg['To'] = email_settings['receiver_email']
    
    try:
        with smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port']) as server:
            server.starttls()
            server.login(email_settings['sender_email'], email_settings['sender_password'])
            server.send_message(msg)
        st.success(f"Email alert sent for {ticker}")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def check_stocks(config):
    """Check all stocks against their resistance levels"""
    stocks = config.get('stocks_to_monitor', {})
    alerts_sent = []
    
    for ticker, resistance in stocks.items():
        current_price = get_current_price(ticker)
        if current_price is None:
            continue
            
        st.write(f"{ticker}: Current price: {current_price}, Resistance: {resistance}")
        
        if current_price >= resistance:
            send_email_alert(config, ticker, current_price, resistance)
            alerts_sent.append(ticker)
    
    # Remove stocks that triggered alerts (to avoid repeated alerts)
    for ticker in alerts_sent:
        del config['stocks_to_monitor'][ticker]
    
    if alerts_sent:
        save_config(config)
        st.experimental_rerun()

def main():
    st.title("📈 Stock Price Alert System")
    st.markdown("Monitor stocks and get email alerts when they break resistance levels")
    
    config = load_config()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Email settings
        st.subheader("Email Settings")
        sender_email = st.text_input("Sender Email", value=config['email_settings']['sender_email'])
        sender_password = st.text_input("Sender Password", type="password", value=config['email_settings']['sender_password'])
        receiver_email = st.text_input("Receiver Email", value=config['email_settings']['receiver_email'])
        smtp_server = st.text_input("SMTP Server", value=config['email_settings']['smtp_server'])
        smtp_port = st.number_input("SMTP Port", value=config['email_settings']['smtp_port'])
        
        # Check interval
        check_interval = st.number_input("Check Interval (seconds)", min_value=10, value=config['check_interval'])
        
        # Save config button
        if st.button("Save Configuration"):
            config['email_settings'] = {
                "sender_email": sender_email,
                "sender_password": sender_password,
                "receiver_email": receiver_email,
                "smtp_server": smtp_server,
                "smtp_port": smtp_port
            }
            config['check_interval'] = check_interval
            save_config(config)
            st.success("Configuration saved!")
    
    # Main content
    tab1, tab2 = st.tabs(["Monitor Stocks", "Add/Remove Stocks"])
    
    with tab1:
        st.header("Stock Monitoring")
        
        if st.button("Check Prices Now"):
            check_stocks(config)
        
        if config['stocks_to_monitor']:
            st.subheader("Currently Monitoring")
            for ticker, resistance in config['stocks_to_monitor'].items():
                st.write(f"- {ticker}: Resistance at {resistance}")
        else:
            st.warning("No stocks being monitored. Add some in the 'Add/Remove Stocks' tab.")
    
    with tab2:
        st.header("Manage Stocks")
        
        # Add stock
        st.subheader("Add Stock")
        col1, col2 = st.columns(2)
        with col1:
            new_ticker = st.text_input("Stock Ticker (e.g., AAPL)").upper()
        with col2:
            new_resistance = st.number_input("Resistance Level", min_value=0.0, step=0.1)
        
        if st.button("Add Stock"):
            if new_ticker and new_resistance > 0:
                config['stocks_to_monitor'][new_ticker] = new_resistance
                save_config(config)
                st.success(f"Added {new_ticker} with resistance level {new_resistance}")
                st.experimental_rerun()
            else:
                st.error("Please enter a valid ticker and resistance level")
        
        # Remove stock
        st.subheader("Remove Stock")
        if config['stocks_to_monitor']:
            ticker_to_remove = st.selectbox(
                "Select stock to remove",
                options=list(config['stocks_to_monitor'].keys())
            )
            if st.button("Remove Selected Stock"):
                del config['stocks_to_monitor'][ticker_to_remove]
                save_config(config)
                st.success(f"Removed {ticker_to_remove}")
                st.experimental_rerun()
        else:
            st.info("No stocks to remove")

if __name__ == "__main__":
    main()
