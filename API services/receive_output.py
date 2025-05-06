import requests
import json
import time
import os
import boto3
import hmac
import hashlib
import base64

# Cognito configuration
COGNITO_USER_POOL_ID = "us-east-1_7Cyjty3qt"  # Replace with your User Pool ID
COGNITO_CLIENT_ID = "6fktfi0jqth7lm4n1g6hlde1h6"
COGNITO_CLIENT_SECRET = "hqosu2dq041cqe75pvfvmrdh5i7f42n1tkavl8n135dcv1itpis"  # Replace with your Client Secret
COGNITO_REGION = "us-east-1"
USERNAME = "Ritvik"
PASSWORD = "NewTest@123"  # Updated to the new password # Updated to the new password

# API Gateway endpoint for results
API_ENDPOINT_RESULTS = "https://cdjg6yyn0h.execute-api.us-east-1.amazonaws.com/prod/results"

# File to store TaskIds
TASK_ID_FILE = "task_ids.json"

# Compute the SECRET_HASH
def calculate_secret_hash(client_id, client_secret, username):
    message = username + client_id
    hmac_obj = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(hmac_obj.digest()).decode('utf-8')

# Authenticate with Cognito to get a JWT token
def get_jwt_token():
    secret_hash = calculate_secret_hash(COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, USERNAME)
    client = boto3.client('cognito-idp', region_name=COGNITO_REGION)
    
    try:
        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': USERNAME,
                'PASSWORD': PASSWORD,
                'SECRET_HASH': secret_hash
            },
            ClientId=COGNITO_CLIENT_ID
        )
        return response['AuthenticationResult']['IdToken']
    except client.exceptions.NotAuthorizedException as e:
        print(f"Authentication failed: {e}")
        raise
    except client.exceptions.UserNotFoundException as e:
        print(f"User not found: {e}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

# Get the JWT token
try:
    jwt_token = get_jwt_token()
except Exception as e:
    print(f"Failed to get JWT token: {e}")
    exit(1)

def read_task_ids(file_path):
    """Read TaskIds from a JSON file."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data.get('task_ids', [])
        return []
    except Exception as e:
        print(f"Error reading TaskId file: {e}")
        return []

def fetch_result(task_id):
    """Fetch result for a given TaskId from the API Gateway."""
    url = f"{API_ENDPOINT_RESULTS}/{task_id}"
    try:
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}"
            }
        )
        response.raise_for_status()  # Raise an error for bad status codes
        result = response.json()
        print(f"Result for TaskId {task_id}:")
        print(json.dumps(result, indent=2))
        return result
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching result for TaskId {task_id}: {e}")
        if response.status_code == 404:
            print("Result not found. The task may not have been processed yet.")
        return None
    except Exception as e:
        print(f"Error fetching result for TaskId {task_id}: {e}")
        return None

def main():
    # Read TaskIds from the JSON file
    task_ids = read_task_ids(TASK_ID_FILE)

    if not task_ids:
        print("No TaskIds found in task_ids.json. Please run upload.py to generate TaskIds.")
        return

    print("Fetching results for TaskIds:")
    for task_id in task_ids:
        print(f"Processing TaskId: {task_id}")
        fetch_result(task_id)
        # Small delay to avoid overwhelming the API
        time.sleep(1)

    print("All TaskIds processed.")

if __name__ == "__main__":
    main()