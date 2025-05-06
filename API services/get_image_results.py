import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'ImageRecognitionTasks'

def lambda_handler(event, context):
    # Extract TaskId from path parameters
    try:
        task_id = event['pathParameters']['taskId']
    except (KeyError, TypeError):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing TaskId in path parameters'}),
            'headers': {'Content-Type': 'application/json'}
        }
    
    # Query DynamoDB
    table = dynamodb.Table(TABLE_NAME)
    try:
        response = table.get_item(Key={'TaskId': task_id})
        item = response.get('Item')
        
        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'No results found for TaskId: {task_id}'}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        # Format the response
        result = {
            'TaskId': item.get('TaskId', ''),
            'Status': item.get('Status', ''),
            'Result': item.get('Result', ''),
            'Labels': json.loads(item.get('Labels', '[]')),
            'ImageKey': item.get('ImageKey', ''),
            'Timestamp': item.get('Timestamp', '')
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {'Content-Type': 'application/json'}
        }
    
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to retrieve results: {str(e)}'}),
            'headers': {'Content-Type': 'application/json'}
        }