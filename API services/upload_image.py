import requests
import base64
import json
import os
import boto3
import hmac
import hashlib

# Cognito configuration
COGNITO_USER_POOL_ID = "us-east-1_7Cyjty3qt"  # Replace with your User Pool ID
COGNITO_CLIENT_ID = "6fktfi0jqth7lm4n1g6hlde1h6"
COGNITO_CLIENT_SECRET = "hqosu2dq041cqe75pvfvmrdh5i7f42n1tkavl8n135dcv1itpis"  # Replace with your Client Secret
COGNITO_REGION = "us-east-1"
USERNAME = "Ritvik"
PASSWORD = "NewTest@123"  # Updated to the new password

# API Gateway endpoint
API_URL = "https://cdjg6yyn0h.execute-api.us-east-1.amazonaws.com/prod/upload"

# Directory containing images
IMAGE_DIR = "images2"

# File to store TaskIds
TASK_ID_FILE = "task_ids.json"

# Supported image formats
SUPPORTED_EXTENSIONS = ['jpg', 'jpeg', 'png']

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

# Save TaskIds to a JSON file
def save_task_ids(task_ids, file_path):
    """Save TaskIds to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump({"task_ids": task_ids}, f, indent=2)
        print(f"TaskIds saved to {file_path}")
    except Exception as e:
        print(f"Error saving TaskIds to {file_path}: {e}")

# Get the JWT token
try:
    jwt_token = get_jwt_token()
except Exception as e:
    print(f"Failed to get JWT token: {e}")
    exit(1)

# List to store TaskIds
task_ids = []

# Get list of image files in the directory
image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

for image_file in image_files:
    image_path = os.path.join(IMAGE_DIR, image_file)
    print(f"Processing image: {image_path}")

    # Read the image file
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except Exception as e:
        print(f"Error: Failed to read image {image_path}: {e}")
        continue

    # Get the file extension
    file_extension = os.path.splitext(image_file)[1].lstrip('.').lower()  # e.g., 'jpeg'
    if file_extension not in SUPPORTED_EXTENSIONS:
        print(f"Error: Unsupported file extension for {image_path}: {file_extension}")
        continue

    # Encode image as Base64
    image_data = base64.b64encode(image_bytes).decode('utf-8')

    # Create payload
    payload = {
        "image": image_data,
        "extension": file_extension
    }

    # Send POST request to API Gateway with the JWT token
    try:
        response = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}"
            },
            data=json.dumps(payload)
        )
        response_data = response.json()
        print(f"Response for {image_file}: {response_data}")
        
        # Extract and store TaskId
        if 'taskId' in response_data:
            task_ids.append(response_data['taskId'])
    except Exception as e:
        print(f"Error: Failed to send request for {image_path}: {e}")
        continue

# Save TaskIds to file
if task_ids:
    save_task_ids(task_ids, TASK_ID_FILE)
else:
    print("No TaskIds were collected.")

print("All images processed.")