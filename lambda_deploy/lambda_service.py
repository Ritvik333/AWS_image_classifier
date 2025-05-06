import json
import boto3
import base64
import uuid
import os
from PIL import Image
import io
import logging
import time

logging.getLogger().setLevel(logging.INFO)

s3 = boto3.client('s3')
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

try:
    S3_BUCKET = os.environ['S3_BUCKET']
    SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']
    DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
except KeyError as e:
    logging.error(f"Missing environment variable: {e}")
    raise

ALLOWED_FORMATS = {'PNG', 'JPEG'}

def lambda_handler(event, context):
    try:
        logging.info(f"Received event: {json.dumps(event)}")
        body = json.loads(event['body'])
        if 'image' not in body:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing image data'})
            }

        logging.info("Decoding base64 image")
        image_data = base64.b64decode(body['image'])

        logging.info("Opening and validating image")
        try:
            image = Image.open(io.BytesIO(image_data))
            image_format = image.format
            if image_format is None:
                logging.error("Image format could not be determined")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Could not determine image format'})
                }
            if image_format not in ALLOWED_FORMATS:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'Unsupported image format: {image_format}. Allowed formats: {ALLOWED_FORMATS}'})
                }
        except Exception as e:
            logging.error(f"Failed to open image: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid image data'})
            }

        logging.info("Resizing image to 224x224")
        image = image.resize((224, 224))

        logging.info("Converting image back to bytes")
        output_buffer = io.BytesIO()
        image.save(output_buffer, format=image_format)
        preprocessed_image_data = output_buffer.getvalue()

        task_id = str(uuid.uuid4())
        extension = body.get('extension', image_format.lower())
        image_key = f"images/{task_id}.{extension}"
        logging.info(f"Generated task ID: {task_id}, image key: {image_key}")

        logging.info("Uploading image to S3")
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=image_key,
            Body=preprocessed_image_data
        )

        logging.info("Storing task metadata in DynamoDB")
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(
            Item={
                'TaskId': task_id,
                'Status': 'Pending',
                'ImageKey': image_key,
                'CreatedAt': int(time.time())
            }
        )

        logging.info("Sending message to SQS")
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps({
                'TaskId': task_id,
                'S3Key': image_key
            })
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'taskId': task_id})
        }

    except Exception as e:
        logging.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }