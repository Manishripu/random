import json
import boto3

# --- CONFIGURATION ---
ACCESS_KEY = "ASIAXXXXXXXXXXXXXXXX"  # Use your current active access key
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
SESSION_TOKEN = "FwoGZXIvYXdzEKB//////////..." # Use your current active token
REGION = "us-east-1"

TABLE_NAME = "YourTableName"
PK_NAME = "CustomerId"               # Must match Step 1
SK_NAME = "OrderDate"                # Must match Step 1
INPUT_FILE = "dynamodb_keys.json"
# ---------------------

# Initialize DynamoDB Client
dynamodb = boto3.client(
    'dynamodb',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN,
    region_name=REGION
)

def delete_items_from_file():
    # Load keys from the JSON file
    try:
        with open(INPUT_FILE, 'r') as f:
            keys_to_delete = json.load(f)
    except FileNotFoundError:
        print(f"Error: '{INPUT_FILE}' not found. Please run Step 1 first.")
        return

    if not keys_to_delete:
        print("No keys found in the file to delete.")
        return

    print(f"Loaded {len(keys_to_delete)} items from file. Starting deletion...")
    deleted_count = 0

    for key_pair in keys_to_delete:
        pk_val = key_pair['pk']
        sk_val = key_pair['sk']
        
        statement = f'DELETE FROM "{TABLE_NAME}" WHERE {PK_NAME} = ? AND {SK_NAME} = ?'
        
        try:
            dynamodb.execute_statement(
                Statement=statement,
                Parameters=[{'S': pk_val}, {'S': sk_val}]
            )
            deleted_count += 1
            if deleted_count % 10 == 0:
                print(f"Progress: Deleted {deleted_count}/{len(keys_to_delete)} items...")
                
        except Exception as e:
            print(f"Failed to delete item [PK: {pk_val}, SK: {sk_val}]. Error: {e}")

    print(f"Execution finished! Successfully deleted {deleted_count} items.")

if __name__ == "__main__":
    # Safety confirmation prompt
    confirm = input("Are you sure you want to delete these items from DynamoDB? (yes/no): ")
    if confirm.lower() == 'yes':
        delete_items_from_file()
    else:
        print("Deletion canceled.")
