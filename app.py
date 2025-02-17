from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os
import glob
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary', methods=['GET'])
def generate_report():
    start_datetime = request.args.get('start_datetime')
    end_datetime = request.args.get('end_datetime')

    print(f"Received request for summary from {start_datetime} to {end_datetime}")

    # Set up Chrome WebDriver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        chrome_options.binary_location = "/usr/bin/chromium-browser"  # Render Chromium Path
driver = webdriver.Chrome(options=chrome_options)
        print("✅ Chrome WebDriver started successfully.")

        # Open HungerRush login page
        driver.get("https://hub.hungerrush.com/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("guttaman86@gmail.com")
        driver.find_element(By.ID, "Password").send_keys("Eocp2024#")
        driver.find_element(By.ID, "newLogonButton").click()
        print("✅ Login successful!")

        # Navigate to "Order Details"
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "rptvNextAnchor"))).click()
        print("✅ Navigated to Reporting - NEW!")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//span[text()='Order Details']"))).click()
        print("✅ Selected Order Details")

        # Select store
        store_trigger = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'p-multiselect-trigger-icon')]")))
        store_trigger.click()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Piqua']"))).click()
        print("✅ Selected Piqua store")

        # Click "Run Report"
        run_report_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='runReport']//span[text()='Run Report']")))
        run_report_button.click()
        print("✅ Running report...")

        # Open Export dropdown and select Excel
        export_dropdown = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dx-button-content']//span[text()=' Export ']")))
        driver.execute_script("arguments[0].click();", export_dropdown)
        print("✅ Opened Export dropdown")

        export_xlsx_option = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Export all data to Excel')]")))
        driver.execute_script("arguments[0].click();", export_xlsx_option)
        print("✅ Report download initiated!")

        # Wait for the file to appear
        download_dir = "C:\\Users\\gutta\\Downloads\\"
        time.sleep(10)  # Give it time to download

        # Find the latest Excel file
        xlsx_files = glob.glob(os.path.join(download_dir, "order-details-*.xlsx"))
        if not xlsx_files:
            print("❌ No matching Excel file found.")
            return jsonify({"error": "Excel file not found. Please try again."}), 500

        xlsx_file_path = max(xlsx_files, key=os.path.getctime)  # Get most recent file
        print(f"✅ Excel file found: {xlsx_file_path}")

        # Process the Excel file
        df = pd.read_excel(xlsx_file_path)

        # Ensure correct Payment and Type handling
        cash_sales_instore = df[df['Payment'].str.contains('Cash', na=False) & df['Type'].isin(["Pickup", "Pick Up", "Web Pick Up"])]
        cash_sales_delivery = df[df['Payment'].str.contains('Cash', na=False) & df['Type'].str.contains("Delivery", na=False)]
        tips_instore = df[df['Type'].isin(["Pickup", "Pick Up", "Web Pick Up"])]['Tips'].sum()
        tips_delivery = df[df['Type'].str.contains("Delivery", na=False)]['Tips'].sum()

        summary_data = {
            "Cash Sales (In-Store)": round(cash_sales_instore['Total'].sum(), 2),
            "Cash Sales (Delivery)": round(cash_sales_delivery['Total'].sum(), 2),
            "Credit Card Tips (In-Store)": round(tips_instore, 2),
            "Credit Card Tips (Delivery)": round(tips_delivery, 2)
        }

        return jsonify(summary_data)

    except Exception as e:
        print(f"❌ Error during report generation: {e}")
        return jsonify({"error": "Failed to generate report. Please try again later."}), 500

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True, port=10000, host="0.0.0.0")
