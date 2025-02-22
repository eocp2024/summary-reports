


import requests

# HungerRush GraphQL API Endpoint (Replace with the actual API URL)
GRAPHQL_URL = "https://api.hungerrush.com/graphql"

# Replace with your actual API Key
API_KEY = "your_hungerrush_api_key_here"

# Headers for authentication
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# GraphQL Query to Fetch Orders
query = """
query GetOrders($startDate: String!, $endDate: String!) {
  orders(startDate: $startDate, endDate: $endDate) {
    orderId
    date
    total
    paymentType
  }
}
"""

# Define query variables
variables = {
    "startDate": "2025-02-18",
    "endDate": "2025-02-18"
}

# Send the request
response = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)

# Check response
if response.status_code == 200:
    print("✅ Successfully fetched data!")
    print(response.json())
else:
    print("❌ Error:", response.status_code, response.text)
