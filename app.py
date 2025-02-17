from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import os
import glob

app = Flask(__name__)

def filter_by_datetime(df, start_datetime, end_datetime):
    if 'Date' in df.columns and 'Time' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    else:
        raise Exception("Date and Time columns are required to filter by datetime.")
    
    start_dt = pd.to_datetime(start_datetime)
    end_dt = pd.to_datetime(end_datetime)
    
    filtered_df = df[(df['Datetime'] >= start_dt) & (df['Datetime'] <= end_dt)]
    return filtered_df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary', methods=['GET'])
def generate_report():
    start_datetime = request.args.get('start_datetime')
    end_datetime = request.args.get('end_datetime')

    print(f"Received request for summary from {start_datetime} to {end_datetime}")

    # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
    chrome_options.add_argument("--no-sandbox")  # Required for Render
    chrome_options.add_argument("--disable-dev-shm-usage")  # Avoid memory issues
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"  # Ensure correct path on Render

    driver = None  # Initialize driver as None to avoid UnboundLocalError

    try:
        # Start Chrome WebDriver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome WebDriver started successfully!")

        # Login to HungerRush
        driver.get("https://hub.hungerrush.com/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("guttaman86@gmail.com")
        driver.find_element(By.ID, "Password").send_keys("Eocp2024#")
        driver.find_element(By.ID, "newLogonButton").click()
        print("Login successful!")

        # Navigate to "Order Details"
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "rptvNextAnchor"))).click()
        print("Navigated to Reporting - NEW!")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//span[text()='Order Details']"))).click()
        print("Selected Order Details")

        # Handle the "Store" dropdown
        store_trigger = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'p-multiselect-trigger-icon')]")))
        store_trigger.click()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Piqua']"))).click()
        print("Selected Piqua store")

        # Click "Run Report"
        run_report_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='runReport']//span[text()='Run Report']")))
        run_report_button.click()
        print("Running report...")

        # Click Export dropdown and then "Export all data to Excel"
        export_dropdown = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dx-button-content']//span[text()=' Export ']")))
        driver.execute_script("arguments[0].click();", export_dropdown)
        print("Opened Export dropdown")
        export_excel_option = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Export all data to Excel')]")))
        driver.execute_script("arguments[0].click();", export_excel_option)
        print("Report download initiated!")

        # Find the latest Excel file that matches the pattern "order-details-*.xlsx"
        excel_pattern = "/tmp/order-details-*.xlsx"
        excel_files = glob.glob(excel_pattern)
        if not excel_files:
            print("No matching Excel file found.")
            return jsonify({"error": "Excel file not found. Please try again."}), 500

        excel_file_path = max(excel_files, key=os.path.getctime)
        print(f"Excel file found: {excel_file_path}")

        # Process the Excel file using pandas
        df = pd.read_excel(excel_file_path)

        # Filter data by the provided datetime range
        df_filtered = filter_by_datetime(df, start_datetime, end_datetime)

        # Updated calculations
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

        return jsonify(summary_data)

    except Exception as e:
        print(f"Error during report generation: {e}")
        return jsonify({"error": "Failed to generate report. Please try again later."}), 500

    finally:
        if driver is not None:
            driver.quit()  # Only quit if driver was successfully initialized

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
