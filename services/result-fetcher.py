import boto3

s3 = boto3.client('s3')
bucket_name = 'image-recognition-bucket-b01021909'
object_key = 'Results/2eafcfd1-9001-425b-996a-b9f213a2da71/result.txt'

# Option 1: Download the file
s3.download_file(bucket_name, object_key, 'result.txt')

# Option 2: Read the file content directly
response = s3.get_object(Bucket=bucket_name, Key=object_key)
content = response['Body'].read().decode('utf-8')
print(content)