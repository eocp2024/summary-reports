from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import os
import glob

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Serves the UI page

@app.route('/summary', methods=['GET'])
def generate_report():
    try:
        start_datetime = request.args.get('start_datetime')
        end_datetime = request.args.get('end_datetime')

        print(f"Received request for summary from {start_datetime} to {end_datetime}")

        # Set up Selenium for cloud deployment
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Firefox(options=firefox_options)

        try:
            driver.get("https://hub.hungerrush.com/")

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys(os.environ.get("HR_USERNAME"))
            driver.find_element(By.ID, "Password").send_keys(os.environ.get("HR_PASSWORD"))
            driver.find_element(By.ID, "newLogonButton").click()
            print("Login successful!")

            # Navigate to order details
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Order Details']"))).click()
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Piqua']"))).click()
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='runReport']//span[text()='Run Report']"))).click()
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Export all data to Excel')]"))).click()

            # Locate the latest Excel file
            excel_pattern = "/home/eocp2024/order-details-*.xlsx"
            excel_files = glob.glob(excel_pattern)
            if not excel_files:
                return jsonify({"error": "Excel file not found."}), 500

            excel_file_path = max(excel_files, key=os.path.getctime)

            # Load the Excel file
            df = pd.read_excel(excel_file_path)
            df.columns = df.columns.str.strip()

            # Convert Date and Time into a single datetime column
            df["Datetime"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), errors="coerce")
            df = df.dropna(subset=["Datetime"])

            # Filter data within selected time range
            start_dt = pd.to_datetime(start_datetime, errors="coerce")
            end_dt = pd.to_datetime(end_datetime, errors="coerce")

            if start_dt is pd.NaT or end_dt is pd.NaT:
                return jsonify({"error": "Invalid start or end datetime format"}), 400

            df_filtered = df[(df["Datetime"] >= start_dt) & (df["Datetime"] <= end_dt)].copy()

            # Calculate sales summary
            cash_sales = df_filtered[df_filtered["Payment"].str.contains("cash", na=False, regex=True)]["Total"].sum()
            tips = df_filtered[df_filtered["Payment"].str.contains("visa|mc|amex", na=False, regex=True)]["Tips"].sum()

            return jsonify({
                "Cash Sales": round(cash_sales, 2),
                "Credit Card Tips": round(tips, 2),
            })

        except Exception as e:
            return jsonify({"error": f"Failed to retrieve report: {str(e)}"}), 500

        finally:
            driver.quit()

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Railway's dynamic port assignment
    app.run(host='0.0.0.0', port=port)
