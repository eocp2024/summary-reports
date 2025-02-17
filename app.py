from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
import glob
import shutil

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary', methods=['GET'])
def generate_report():
    start_datetime = request.args.get('start_datetime')
    end_datetime = request.args.get('end_datetime')

    print(f"Received request for summary from {start_datetime} to {end_datetime}")

    # ✅ Dynamically find Chrome path in Render's environment
    chrome_binary_path = shutil.which("google-chrome")  # Auto-detect installed Chrome

    if not chrome_binary_path:
        print("❌ Error: Google Chrome is not installed in Render's environment.")
        return jsonify({"error": "Chrome is missing on the server. Please check the deployment settings."}), 500

    print(f"✅ Chrome found at: {chrome_binary_path}")

    # Configure WebDriver with Headless Chrome
    chrome_options = Options()
    chrome_options.binary_location = chrome_binary_path  # Use detected Chrome path
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # ✅ Use WebDriver Manager to get the correct ChromeDriver version
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Login to HungerRush
        driver.get("https://hub.hungerrush.com/")
        time.sleep(5)
        driver.find_element("id", "UserName").send_keys("guttaman86@gmail.com")
        driver.find_element("id", "Password").send_keys("Eocp2024#")
        driver.find_element("id", "newLogonButton").click()
        print("✅ Login successful!")

        # Navigate to "Order Details"
        time.sleep(5)
        driver.find_element("xpath", "//span[text()='Order Details']").click()
        print("✅ Selected Order Details")

        # Select "Piqua" store
        time.sleep(3)
        driver.find_element("xpath", "//span[contains(@class, 'p-multiselect-trigger-icon')]").click()
        driver.find_element("xpath", "//span[text()='Piqua']").click()
        print("✅ Selected Piqua store")

        # Run the report
        time.sleep(3)
        driver.find_element("xpath", "//button[@id='runReport']//span[text()='Run Report']").click()
        print("✅ Running report...")

        # Export report as Excel
        time.sleep(5)
        driver.find_element("xpath", "//div[@class='dx-button-content']//span[text()=' Export ']").click()
        driver.find_element("xpath", "//div[contains(text(), 'Export all data to Excel')]").click()
        print("✅ Report download initiated!")

        # Find the latest Excel file
        excel_pattern = "/tmp/order-details-*.xlsx"
        time.sleep(10)  # Allow time for the file to download
        excel_files = glob.glob(excel_pattern)

        if not excel_files:
            print("❌ No matching Excel file found.")
            return jsonify({"error": "Excel file not found. Please try again."}), 500

        excel_file_path = max(excel_files, key=os.path.getctime)
        print(f"✅ Excel file found: {excel_file_path}")

        # Read Excel file
        df = pd.read_excel(excel_file_path)

        # Ensure correct column formatting
        df.columns = df.columns.str.strip()  # Remove extra spaces

        # Calculate cash sales and tips
        cash_sales_in_store = df[df['Type'].isin(['Pickup', 'Pick Up', 'Web Pick Up']) & (df['Payment'].str.contains("Cash", na=False))]['Total'].sum()
        cash_sales_delivery = df[df['Type'] == 'Delivery' & df['Payment'].str.contains("Cash", na=False)]['Total'].sum()
        credit_card_tips_in_store = df[df['Type'].isin(['Pickup', 'Pick Up', 'Web Pick Up'])]['Tips'].sum()
        credit_card_tips_delivery = df[df['Type'] == 'Delivery']['Tips'].sum()

        # Prepare JSON response
        summary_data = {
            "Cash Sales (In-Store)": round(cash_sales_in_store, 2),
            "Cash Sales (Delivery)": round(cash_sales_delivery, 2),
            "Credit Card Tips (In-Store)": round(credit_card_tips_in_store, 2),
            "Credit Card Tips (Delivery)": round(credit_card_tips_delivery, 2)
        }

        return jsonify(summary_data)

    except Exception as e:
        print(f"❌ Error during report generation: {e}")
        return jsonify({"error": "Failed to generate report. Please try again later."}), 500

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
