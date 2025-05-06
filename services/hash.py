import hmac
import hashlib
import base64

def calculate_secret_hash(client_id, client_secret, username):
    # Concatenate username and client_id
    message = username + client_id
    
    # Compute HMAC-SHA256 of the message using the client_secret as the key
    hmac_obj = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    hmac_digest = hmac_obj.digest()
    
    # Encode the HMAC result in Base64
    secret_hash = base64.b64encode(hmac_digest).decode('utf-8')
    return secret_hash

# Replace these values with your own
client_id = "6fktfi0jqth7lm4n1g6hlde1h6"
client_secret = "hqosu2dq041cqe75pvfvmrdh5i7f42n1tkavl8n135dcv1itpis"  # Replace with the actual client secret
username = "Ritvik"

secret_hash = calculate_secret_hash(client_id, client_secret, username)
print(f"SECRET_HASH: {secret_hash}")