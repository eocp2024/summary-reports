from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
import glob

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary', methods=['GET'])
def generate_report():
    start_datetime = request.args.get('start_datetime')
    end_datetime = request.args.get('end_datetime')

    print(f"Received request for summary from {start_datetime} to {end_datetime}")

    # Set up Chrome WebDriver (Headless Mode for Render)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run without a visible UI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Specify ChromeDriver path (Render environment)
    chrome_driver_path = "/usr/bin/chromedriver"
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
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

        # Open the Export dropdown and click "Export all data to Excel"
        export_dropdown = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dx-button-content']//span[text()=' Export ']")))
        driver.execute_script("arguments[0].click();", export_dropdown)
        print("Opened Export dropdown")
        export_excel_option = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Export all data to Excel')]")))
        driver.execute_script("arguments[0].click();", export_excel_option)
        print("Report download initiated!")

        # Wait and find the latest Excel file
        excel_pattern = "/tmp/order-details-*.xlsx"  # Adjust path if needed
        time.sleep(5)  # Allow time for the file to appear
        excel_files = glob.glob(excel_pattern)
        if not excel_files:
            print("No matching Excel file found.")
            return jsonify({"error": "Excel file not found. Please try again."}), 500

        excel_file_path = max(excel_files, key=os.path.getctime)
        print(f"Excel file found: {excel_file_path}")

        # Read the Excel file
        df = pd.read_excel(excel_file_path, engine="openpyxl")

        # Process sales and tips data
        cash_sales_in_store = df[df["Type"].isin(["Pickup", "Pick Up", "Web Pick Up"]) & (df["Payment"].str.contains("Cash", na=False))]["Total"].sum()
        cash_sales_delivery = df[df["Type"] == "Delivery"][df["Payment"].str.contains("Cash", na=False)]["Total"].sum()
        credit_card_tips_in_store = df[df["Type"].isin(["Pickup", "Pick Up", "Web Pick Up"])]["Tips"].sum()
        credit_card_tips_delivery = df[df["Type"] == "Delivery"]["Tips"].sum()

        # Return summary data
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
        driver.quit()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=False)
