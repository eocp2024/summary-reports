from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os
import glob

app = Flask(__name__)

def filter_by_datetime(df, start_datetime, end_datetime):
    """Filters data based on provided datetime range."""
    if 'Date' in df.columns and 'Time' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    else:
        raise Exception("Date and Time columns are required to filter by datetime.")
    
    start_dt = pd.to_datetime(start_datetime)
    end_dt = pd.to_datetime(end_datetime)
    
    return df[(df['Datetime'] >= start_dt) & (df['Datetime'] <= end_dt)]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary', methods=['GET'])
def generate_report():
    start_datetime = request.args.get('start_datetime')
    end_datetime = request.args.get('end_datetime')

    print(f"🔹 Received request for summary from {start_datetime} to {end_datetime}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # ✅ Step 1: Login to HungerRush
            page.goto("https://hub.hungerrush.com/")
            page.fill("#UserName", "guttaman86@gmail.com")
            page.fill("#Password", "Eocp2024#")
            page.click("#newLogonButton")
            page.wait_for_selector("#rptvNextAnchor")
            print("✅ Login successful!")

            # ✅ Step 2: Navigate to "Order Details"
            page.click("#rptvNextAnchor")
            print("✅ Navigated to Reporting - NEW!")

            page.wait_for_selector("//span[text()='Order Details']").click()
            print("✅ Selected Order Details")

            # ✅ Step 3: Select Store (Piqua)
            page.wait_for_selector("//span[contains(@class, 'p-multiselect-trigger-icon')]").click()
            page.wait_for_selector("//span[text()='Piqua']").click()
            print("✅ Selected Piqua store")

            # ✅ Step 4: Run Report
            page.wait_for_selector("//button[@id='runReport']//span[text()='Run Report']").click()
            print("📊 Running report...")

            # ✅ Step 5: Export to Excel
            page.wait_for_selector("//div[@class='dx-button-content']//span[text()=' Export ']").click()
            page.wait_for_selector("//div[contains(text(), 'Export all data to Excel')]").click()
            print("📂 Report download initiated!")

            # ✅ Step 6: Find the latest downloaded Excel file
            time.sleep(5)  # Wait for file to download
            excel_pattern = "/tmp/order-details-*.xlsx"
            excel_files = glob.glob(excel_pattern)
            if not excel_files:
                print("❌ No matching Excel file found.")
                return jsonify({"error": "Excel file not found. Please try again."}), 500

            excel_file_path = max(excel_files, key=os.path.getctime)
            print(f"✅ Excel file found: {excel_file_path}")

            # ✅ Step 7: Process the Excel file using pandas
            df = pd.read_excel(excel_file_path)
            df_filtered = filter_by_datetime(df, start_datetime, end_datetime)

            # ✅ Step 8: Updated calculations
            cash_sales_in_store = df_filtered[(df_filtered['Payment'].str.contains('Cash', na=False)) & 
                                              (df_filtered['Type'].str.contains('Pick Up|Pickup|To Go|Web Pickup|Web Pick Up', na=False))]['Total'].sum()
            cash_sales_delivery = df_filtered[(df_filtered['Payment'].str.contains('Cash', na=False)) & 
                                              (df_filtered['Type'].str.contains('Delivery', na=False))]['Total'].sum()
            credit_card_tips_in_store = df_filtered[(df_filtered['Payment'].str.contains('Visa|MC|AMEX', na=False)) & 
                                                    (df_filtered['Type'].str.contains('Pick Up|Pickup|To Go|Web Pickup|Web Pick Up', na=False))]['Tips'].sum()
            credit_card_tips_delivery = df_filtered[(df_filtered['Payment'].str.contains('Visa|MC|AMEX', na=False)) & 
                                                    (df_filtered['Type'].str.contains('Delivery', na=False))]['Tips'].sum()

            summary_data = {
                "Cash Sales (In-Store)": round(cash_sales_in_store, 2),
                "Cash Sales (Delivery)": round(cash_sales_delivery, 2),
                "Credit Card Tips (In-Store)": round(credit_card_tips_in_store, 2),
                "Credit Card Tips (Delivery)": round(credit_card_tips_delivery, 2)
            }

            browser.close()
            return jsonify(summary_data)

    except Exception as e:
        print(f"❌ Error during report generation: {e}")
        return jsonify({"error": "Failed to generate report. Please try again later."}), 500

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
