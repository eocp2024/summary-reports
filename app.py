import os
import time
import glob
import pandas as pd
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# Load Browserless WebDriver URL from environment variables
BROWSER_WEBDRIVER_ENDPOINT = os.getenv("BROWSER_WEBDRIVER_ENDPOINT")
BROWSER_TOKEN = os.getenv("BROWSER_TOKEN")

if not BROWSER_WEBDRIVER_ENDPOINT or not BROWSER_TOKEN:
    raise ValueError("Browserless WebDriver endpoint or token is missing!")

# Set Chrome options for remote WebDriver
chrome_options = Options()
chrome_options.set_capability("browserless:token", BROWSER_TOKEN)
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

def filter_by_datetime(df, start_datetime, end_datetime):
    """Filters the DataFrame by start and end datetime."""
    if 'Date' in df.columns and 'Time' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    else:
        return df  # Return unfiltered if Date/Time columns are missing
    
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

    try:
        driver = webdriver.Remote(
            command_executor=BROWSER_WEBDRIVER_ENDPOINT,
            options=chrome_options
        )

        # Login to HungerRush
        driver.get("https://hub.hungerrush.com/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("guttaman86@gmail.com")
        driver.find_element(By.ID, "Password").send_keys("Eocp2024#")
        driver.find_element(By.ID, "newLogonButton").click()

        # Navigate to Reports > Order Details
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "rptvNextAnchor"))).click()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//span[text()='Order Details']"))).click()

        # Select store and run report
        store_trigger = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'p-multiselect-trigger-icon')]")))
        store_trigger.click()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Piqua']"))).click()
        run_report_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='runReport']//span[text()='Run Report']")))
        run_report_button.click()

        # Export report to Excel
        export_dropdown = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dx-button-content']//span[text()=' Export ']")))
        driver.execute_script("arguments[0].click();", export_dropdown)
        export_excel_option = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Export all data to Excel')]")))
        driver.execute_script("arguments[0].click();", export_excel_option)

        # Wait for download
        time.sleep(5)

        # Get the latest Excel file
        excel_pattern = "/app/downloads/order-details-*.xlsx"  # Adjust path for Railway
        excel_files = glob.glob(excel_pattern)
        if not excel_files:
            return jsonify({"error": "Excel file not found."}), 500
        excel_file_path = max(excel_files, key=os.path.getctime)

        # Read the Excel file
        df = pd.read_excel(excel_file_path)
        df_filtered = filter_by_datetime(df, start_datetime, end_datetime)

        # Calculate sales and tips
        cash_sales_in_store = df_filtered[df_filtered['Payment'].str.contains('Cash', na=False) & 
                                          df_filtered['Type'].str.contains('Pick Up|Pickup|To Go|Web Pickup|Web Pick Up', na=False)]['Total'].sum()
        cash_sales_delivery = df_filtered[df_filtered['Payment'].str.contains('Cash', na=False) & 
                                          df_filtered['Type'].str.contains('Delivery', na=False)]['Total'].sum()
        credit_card_tips_in_store = df_filtered[df_filtered['Payment'].str.contains('Visa|MC|AMEX', na=False) & 
                                                df_filtered['Type'].str.contains('Pick Up|Pickup|To Go|Web Pickup|Web Pick Up', na=False)]['Tips'].sum()
        credit_card_tips_delivery = df_filtered[df_filtered['Payment'].str.contains('Visa|MC|AMEX', na=False) & 
                                                df_filtered['Type'].str.contains('Delivery', na=False)]['Tips'].sum()

        # Return the summary
        summary_data = {
            "Cash Sales (In-Store)": round(cash_sales_in_store, 2),
            "Cash Sales (Delivery)": round(cash_sales_delivery, 2),
            "Credit Card Tips (In-Store)": round(credit_card_tips_in_store, 2),
            "Credit Card Tips (Delivery)": round(credit_card_tips_delivery, 2)
        }
        return jsonify(summary_data)

    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
