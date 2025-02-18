from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import os
import time
import glob

app = Flask(__name__)

# ✅ Define paths for prebuilt Chrome and ChromeDriver
CHROME_BIN = "/opt/google/chrome/chrome"
CHROMEDRIVER_PATH = "/opt/chromedriver"

# ✅ Configure Chrome WebDriver for Railway/Render Deployment
def get_chrome_driver():
    chrome_options = Options()
    chrome_options.binary_location = CHROME_BIN
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # ✅ Initialize WebDriver with proper binary paths
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary', methods=['GET'])
def generate_report():
    start_datetime = request.args.get('start_datetime')
    end_datetime = request.args.get('end_datetime')

    print(f"🔹 Received request for summary from {start_datetime} to {end_datetime}")

    driver = get_chrome_driver()

    try:
        # ✅ Login to HungerRush
        driver.get("https://hub.hungerrush.com/")
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("guttaman86@gmail.com")
        driver.find_element(By.ID, "Password").send_keys("Eocp2024#")
        driver.find_element(By.ID, "newLogonButton").click()
        print("✅ Login successful!")

        # ✅ Navigate to "Order Details"
        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "rptvNextAnchor"))).click()
        print("✅ Navigated to Reporting - NEW!")

        order_details = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Order Details']"))
        )
        order_details.click()
        print("✅ Selected Order Details")

        # ✅ Select Store (Piqua)
        store_trigger = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'p-multiselect-trigger-icon')]")))
        store_trigger.click()
        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Piqua']"))).click()
        print("✅ Selected Piqua store")

        # ✅ Run Report
        run_report_button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='runReport']//span[text()='Run Report']")))
        run_report_button.click()
        print("📊 Running report...")

        # ✅ Export to Excel
        export_dropdown = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dx-button-content']//span[text()=' Export ']")))
        driver.execute_script("arguments[0].click();", export_dropdown)
        print("✅ Opened Export dropdown")

        export_excel_option = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Export all data to Excel')]")))
        driver.execute_script("arguments[0].click();", export_excel_option)
        print("📂 Report download initiated!")

        # ✅ Find the latest downloaded Excel file
        time.sleep(5)
        excel_pattern = "/tmp/order-details-*.xlsx"
        excel_files = glob.glob(excel_pattern)
        if not excel_files:
            print("❌ No matching Excel file found.")
            return jsonify({"error": "Excel file not found. Please try again."}), 500

        excel_file_path = max(excel_files, key=os.path.getctime)
        print(f"✅ Excel file found: {excel_file_path}")

        # ✅ Process the Excel file using pandas
        df = pd.read_excel(excel_file_path)

        # ✅ Calculate report summary
        cash_sales_in_store = df[(df['Payment'].str.contains('Cash', na=False)) & 
                                 (df['Type'].str.contains('Pick Up|Pickup|To Go|Web Pickup|Web Pick Up', na=False))]['Total'].sum()
        cash_sales_delivery = df[(df['Payment'].str.contains('Cash', na=False)) & 
                                 (df['Type'].str.contains('Delivery', na=False))]['Total'].sum()
        credit_card_tips_in_store = df[(df['Payment'].str.contains('Visa|MC|AMEX', na=False)) & 
                                       (df['Type'].str.contains('Pick Up|Pickup|To Go|Web Pickup|Web Pick Up', na=False))]['Tips'].sum()
        credit_card_tips_delivery = df[(df['Payment'].str.contains('Visa|MC|AMEX', na=False)) & 
                                       (df['Type'].str.contains('Delivery', na=False))]['Tips'].sum()

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
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
