import json
import boto3

# --- CONFIGURATION ---
ACCESS_KEY = "ASIAXXXXXXXXXXXXXXXX"  # Replace with your temporary Access Key
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
SESSION_TOKEN = "FwoGZXIvYXdzEKB//////////..." # Replace with your long session token
REGION = "us-east-1"                 # Replace with your AWS region

TABLE_NAME = "YourTableName"
PK_NAME = "CustomerId"               # Replace with your Partition Key name
SK_NAME = "OrderDate"                # Replace with your Sort Key name
OUTPUT_FILE = "dynamodb_keys.json"
# ---------------------

# Initialize DynamoDB Client with credentials
dynamodb = boto3.client(
    'dynamodb',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN,
    region_name=REGION
)

def fetch_and_save_keys():
    print(f"Scanning table '{TABLE_NAME}' to gather keys...")
    all_keys = []
    
    paginator = dynamodb.get_paginator('scan')
    page_iterator = paginator.paginate(
        TableName=TABLE_NAME,
        ProjectionExpression=f"{PK_NAME}, {SK_NAME}"
    )
    
    for page in page_iterator:
        for item in page.get('Items', []):
            # Extracting string values ('S'). Change to 'N' if your keys are Numbers.
            pk_value = item[PK_NAME]['S'] 
            sk_value = item[SK_NAME]['S']
            
            all_keys.append({
                'pk': pk_value,
                'sk': sk_value
            })
            
    # Save keys to a local JSON file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_keys, f, indent=4)
        
    print(f"Successfully fetched {len(all_keys)} items.")
    print(f"Keys saved locally to '{OUTPUT_FILE}'. Review this file before deleting!")

if __name__ == "__main__":
    fetch_and_save_keys()
