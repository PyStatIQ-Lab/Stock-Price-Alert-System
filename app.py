import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import tkinter as tk
from tkinter import ttk, messagebox

# Configuration
STOCK_LEVELS = {
    'AAPL': 180.00,    # Apple
    'MSFT': 350.00,    # Microsoft
    'TSLA': 200.00,    # Tesla
    # Add more stocks and resistance levels here
}

# Email configuration
EMAIL_CONFIG = {
    'sender_email': 'support@predictram.com',
    'sender_password': 'Singh@54812',  # Use app-specific password for Gmail
    'receiver_email': 'support@predictram.com',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

class StockAlertApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Resistance Alert System")
        self.root.geometry("600x400")
        
        # Create GUI elements
        self.create_widgets()
        
        # Initial data
        self.last_update_time = None
        self.alerts = []
        
    def create_widgets(self):
        # Frame for controls
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            control_frame, 
            text="Refresh Stock Prices", 
            command=self.refresh_stock_prices
        )
        self.refresh_btn.pack(side=tk.LEFT)
        
        # Last update label
        self.update_label = ttk.Label(control_frame, text="Last update: Never")
        self.update_label.pack(side=tk.RIGHT)
        
        # Stock data display
        self.tree = ttk.Treeview(
            self.root, 
            columns=('Ticker', 'Current', 'Resistance', 'Status'), 
            show='headings'
        )
        
        # Configure columns
        self.tree.heading('Ticker', text='Ticker')
        self.tree.heading('Current', text='Current Price')
        self.tree.heading('Resistance', text='Resistance Level')
        self.tree.heading('Status', text='Status')
        
        self.tree.column('Ticker', width=100)
        self.tree.column('Current', width=100, anchor=tk.E)
        self.tree.column('Resistance', width=120, anchor=tk.E)
        self.tree.column('Status', width=150)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def refresh_stock_prices(self):
        self.status_var.set("Fetching stock prices...")
        self.refresh_btn.config(state=tk.DISABLED)
        self.root.update()
        
        self.alerts = []
        self.tree.delete(*self.tree.get_children())
        
        for ticker, resistance in STOCK_LEVELS.items():
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period='1d')['Close'].iloc[-1]
                
                if current_price > resistance:
                    status = "RESISTANCE BROKEN!"
                    self.alerts.append(f"{ticker} has broken resistance level! Current: {current_price:.2f}, Resistance: {resistance:.2f}")
                else:
                    status = "Below resistance"
                
                # Add to treeview
                self.tree.insert('', tk.END, values=(
                    ticker, 
                    f"{current_price:.2f}", 
                    f"{resistance:.2f}", 
                    status
                ))
                
            except Exception as e:
                self.tree.insert('', tk.END, values=(
                    ticker, 
                    "Error", 
                    f"{resistance:.2f}", 
                    str(e)
                ))
        
        # Update last refresh time
        self.last_update_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        self.update_label.config(text=f"Last update: {self.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Send alerts if any
        if self.alerts:
            self.send_alert_email(self.alerts)
            messagebox.showinfo(
                "Alerts Sent", 
                f"{len(self.alerts)} resistance levels broken!\nEmail notification sent."
            )
        
        self.status_var.set("Ready")
        self.refresh_btn.config(state=tk.NORMAL)
    
    def send_alert_email(self, alerts):
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_CONFIG['sender_email']
            msg['To'] = EMAIL_CONFIG['receiver_email']
            msg['Subject'] = f"Stock Alert: {len(alerts)} Resistance Levels Broken"
            
            body = "The following stocks have broken their resistance levels:\n\n"
            body += "\n".join(alerts)
            body += "\n\nChecked at: " + self.last_update_time.strftime("%Y-%m-%d %H:%M:%S")
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
            server.quit()
            
            print("Alert email sent successfully")
        except Exception as e:
            messagebox.showerror("Email Error", f"Failed to send email: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StockAlertApp(root)
    root.mainloop()
