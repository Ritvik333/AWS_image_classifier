import boto3
import json
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
TABLE_NAME = 'ImageRecognitionTasks'

def get_item_by_task_id(task_id):
    """Retrieve a single item by TaskId using GetItem."""
    try:
        response = dynamodb.get_item(
            TableName=TABLE_NAME,
            Key={
                'TaskId': {'S': task_id}
            }
        )
        item = response.get('Item')
        if item:
            # Convert DynamoDB item to a readable format
            result = {
                'Status': item.get('Status',{}).get('S'),
                'TaskId': item.get('TaskId', {}).get('S'),
                'ImageKey': item.get('ImageKey', {}).get('S'),
                'Labels': json.loads(item.get('Labels', {}).get('S')) if item.get('Labels') else [],
                'Timestamp': item.get('Timestamp', {}).get('S')
            }
            print(f"Result for TaskId {task_id}:")
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"No item found for TaskId: {task_id}")
            return None
    except ClientError as e:
        print(f"Error retrieving item: {e.response['Error']['Message']}")
        return None

def scan_all_results():
    """Retrieve all items in the table using Scan."""
    try:
        results = []
        response = dynamodb.scan(TableName=TABLE_NAME)
        for item in response.get('Items', []):
            result = {
                'Status': item.get('Status',{}).get('S'),
                'TaskId': item.get('TaskId', {}).get('S'),
                'ImageKey': item.get('ImageKey', {}).get('S'),
                'Labels': json.loads(item.get('Labels', {}).get('S')) if item.get('Labels') else [],
                'Timestamp': item.get('Timestamp', {}).get('S')
            }
            results.append(result)
        
        # Handle pagination if more items exist
        while 'LastEvaluatedKey' in response:
            response = dynamodb.scan(
                TableName=TABLE_NAME,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for item in response.get('Items', []):
                result = {
                    'Status': item.get('Status',{}).get('S'),
                    'TaskId': item.get('TaskId', {}).get('S'),
                    'ImageKey': item.get('ImageKey', {}).get('S'),
                    'Labels': json.loads(item.get('Labels', {}).get('S')) if item.get('Labels') else [],
                    'Timestamp': item.get('Timestamp', {}).get('S')
                }
                results.append(result)
        
        print("All results:")
        for result in results:
            print(json.dumps(result, indent=2))
        return results
    except ClientError as e:
        print(f"Error scanning table: {e.response['Error']['Message']}")
        return []

if __name__ == "__main__":
    # Example: Retrieve a specific item by TaskId
    # Replace 'your-task-id-here' with the actual TaskId from your API response
    task_id = '10b4a708-d623-4efa-a344-1e2351b6c80c'
    get_item_by_task_id(task_id)
    
    # # Retrieve all results
    # print("\nScanning all results:")
    # scan_all_results()