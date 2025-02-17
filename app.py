from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
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

    print(f"🔹 Received request for summary from {start_datetime} to {end_datetime}")
    print("💻 Running locally, using Firefox.")

    # Configure Firefox WebDriver with binary path and headless options
    service = Service("C:\\Users\\gutta\\Desktop\\Downloads\\geckodriver-v0.35.0-win32\\geckodriver.exe")
    firefox_options = Options()
    firefox_options.binary_location = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
    firefox_options.headless = True

    driver = None
    try:
        driver = webdriver.Firefox(service=service, options=firefox_options)

        # ✅ Step 1: Login to HungerRush
        driver.get("https://hub.hungerrush.com/")
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("guttaman86@gmail.com")
        driver.find_element(By.ID, "Password").send_keys("Eocp2024#")
        driver.find_element(By.ID, "newLogonButton").click()
        print("✅ Login successful!")

        # ✅ Step 2: Navigate to "Order Details"
        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "rptvNextAnchor"))).click()
        print("✅ Navigated to Reporting - NEW!")

        retry_count = 3
        for attempt in range(retry_count):
            try:
                order_details = WebDriverWait(driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Order Details']"))
                )
                order_details.click()
                print("✅ Selected Order Details")
                break
            except:
                if attempt == retry_count - 1:
                    print("❌ Failed to find Order Details after multiple attempts.")
                    return jsonify({"error": "Failed to locate Order Details."}), 500
                print("🔄 Retrying Order Details selection...")
                time.sleep(2)

        # ✅ Step 3: Handle the "Store" dropdown
        store_trigger = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'p-multiselect-trigger-icon')]")))
        store_trigger.click()
        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Piqua']"))).click()
        print("✅ Selected Piqua store")

        # ✅ Step 4: Click "Run Report"
        run_report_button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='runReport']//span[text()='Run Report']")))
        run_report_button.click()
        print("📊 Running report...")

        # ✅ Step 5: Click the Export dropdown and select "Export all data to Excel"
        export_dropdown = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dx-button-content']//span[text()=' Export ']")))
        driver.execute_script("arguments[0].click();", export_dropdown)
        print("✅ Opened Export dropdown")

        export_excel_option = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Export all data to Excel')]")))
        driver.execute_script("arguments[0].click();", export_excel_option)
        print("📂 Report download initiated!")

        # ✅ Step 6: Find the latest downloaded Excel file
        time.sleep(5)  # Wait for file to download
        excel_pattern = "C:\\Users\\gutta\\Downloads\\order-details-*.xlsx"
        excel_files = glob.glob(excel_pattern)
        if not excel_files:
            print("❌ No matching Excel file found.")
            return jsonify({"error": "Excel file not found. Please try again."}), 500

        excel_file_path = max(excel_files, key=os.path.getctime)
        print(f"✅ Excel file found: {excel_file_path}")

        # ✅ Step 7: Process the Excel file using pandas
        df = pd.read_excel(excel_file_path)

        # ✅ Step 8: Filter data by the provided datetime range
        df_filtered = filter_by_datetime(df, start_datetime, end_datetime)

        # ✅ Step 9: Updated calculations
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
        print(f"❌ Error during report generation: {e}")
        if driver:
            print(driver.page_source)  # Print page source for debugging
        return jsonify({"error": "Failed to generate report. Please try again later."}), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
