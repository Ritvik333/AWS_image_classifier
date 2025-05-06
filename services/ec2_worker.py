import boto3
import json
import cv2
import numpy as np
import time
import urllib.request
import logging
import os
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# SQS and DynamoDB configuration
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/915696926220/image-processing-queue'
TABLE_NAME = 'ImageRecognitionTasks'
BUCKET = 'image-recognition-bucket-b01021909'

# Download pre-trained model
MODEL_URL = 'https://raw.githubusercontent.com/PINTO0309/MobileNet-SSD-RealSense/master/caffemodel/MobileNetSSD/MobileNetSSD_deploy.caffemodel'
PROTO_URL = 'https://raw.githubusercontent.com/PINTO0309/MobileNet-SSD-RealSense/master/caffemodel/MobileNetSSD/MobileNetSSD_deploy.prototxt'
MODEL_PATH = '/tmp/MobileNetSSD_deploy.caffemodel'
PROTO_PATH = '/tmp/MobileNetSSD_deploy.prototxt'

def download_model():
    if not os.path.exists(MODEL_PATH):
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    if not os.path.exists(PROTO_PATH):
        urllib.request.urlretrieve(PROTO_URL, PROTO_PATH)

# Classes for MobileNet SSD
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus",
           "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike",
           "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]

def process_image(image_path):
    # Load model
    # print("processing image")
    net = cv2.dnn.readNetFromCaffe(PROTO_PATH, MODEL_PATH)
    
    # Read image
    image = cv2.imread(image_path)
    (h, w) = image.shape[:2]
    
    # Prepare blob
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    
    # Detect objects
    detections = net.forward()
    # print("detections: ",detections)
    labels = []
    
    # Process detections
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.2:  # Confidence threshold
            idx = int(detections[0, 0, i, 1])
            labels.append(CLASSES[idx])
    # print(list(set(labels)))
    return list(set(labels))  # Remove duplicates

def main():
    logging.info("Starting EC2 worker")
    download_model()
    last_message_time = time.time()
    
    while True:
        try:
            current_time = time.time()
            if current_time - last_message_time >= 15:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Listening to SQS queue: {QUEUE_URL}")
                logging.info("Listening to SQS queue")
                last_message_time = current_time

            # Poll SQS
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )
            
            if 'Messages' not in response:
                continue
                
            message = response['Messages'][0]
            print("message: ", message)
            receipt_handle = message['ReceiptHandle']
            body = json.loads(message['Body'])
            task_id = body['TaskId']
            s3_key = body['S3Key']
            
            # Download image from S3
            local_path = f'/tmp/{task_id}.jpg'
            s3.download_file(BUCKET, s3_key, local_path)
            
            # Process image
            labels = process_image(local_path)
            
            # Update DynamoDB
            table = dynamodb.Table(TABLE_NAME)
            table.update_item(
                Key={'TaskId': task_id},
                UpdateExpression='SET #status = :status, #result = :result, #image_key = :image_key, #labels = :labels, #timestamp = :timestamp',
                ExpressionAttributeNames={
                    '#status': 'Status',
                    '#result': 'Result',
                    '#image_key': 'ImageKey',
                    '#labels': 'Labels',
                    '#timestamp': 'Timestamp'
                },
                ExpressionAttributeValues={
                    ':status': 'Completed',
                    ':result': ', '.join(labels) if labels else 'No objects detected',
                    ':image_key': s3_key,
                    ':labels': json.dumps(labels),  # Store as JSON string
                    ':timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                }
            )
            
            # Save result to S3
            result_key = f"Results/{task_id}/result.txt"
            s3.put_object(
                Bucket=BUCKET,
                Key=result_key,
                Body=', '.join(labels) if labels else 'No objects detected'
            )
            
            # Delete message from SQS
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=receipt_handle
            )
            
            # Clean up
            if os.path.exists(local_path):
                os.remove(local_path)
                
        except ClientError as e:
            print(f"Error: {e}")
            continue

if __name__ == '__main__':
    main()