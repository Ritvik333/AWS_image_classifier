provider "aws" {
  region = "us-east-1"  # Adjust for your Learner Lab region
}

# Variables
variable "s3_bucket_name" {
  description = "Image-recognition-bucket_B01021909"
  type        = string
  default     = "my-image-recognition-bucket-learnerlab-1234"  # Update with unique name
}

variable "sqs_queue_name" {
  description = "Name of the SQS queue"
  type        = string
  default     = "image-processing-queue"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
  default     = "ImageRecognitionTasks"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "ImageUploadHandler"
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

# S3 Bucket for images and Lambda code
resource "aws_s3_bucket" "image_bucket" {
  bucket = var.s3_bucket_name
  versioning {
    enabled = true
  }

  # Block public access
  acl = "private"
}

resource "aws_s3_bucket_public_access_block" "image_bucket_block" {
  bucket = aws_s3_bucket.image_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# SQS Queue for task processing
resource "aws_sqs_queue" "image_processing_queue" {
  name                      = var.sqs_queue_name
  visibility_timeout_seconds = 60
  receive_wait_time_seconds = 10
}

# DynamoDB Table for task metadata
resource "aws_dynamodb_table" "image_tasks_table" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "TaskId"

  attribute {
    name = "TaskId"
    type = "S"
  }
}

# Lambda Function
resource "aws_lambda_function" "image_upload_lambda" {
  function_name = var.lambda_function_name
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/LabRole"  # Use Learner Lab's LabRole
  timeout       = 30
  memory_size   = 128

  s3_bucket = aws_s3_bucket.image_bucket.bucket
  s3_key    = "lambda_code/lambda_function.zip"  # Upload ZIP to S3 first

  environment {
    variables = {
      S3_BUCKET       = var.s3_bucket_name
      SQS_QUEUE_URL   = aws_sqs_queue.image_processing_queue.url
      DYNAMODB_TABLE  = var.dynamodb_table_name
    }
  }
}

# Security Group for EC2
resource "aws_security_group" "ec2_sg" {
  name        = "image-processing-ec2-sg"
  description = "Security group for EC2 worker"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Allow SSH; restrict in production
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]  # Allow outbound for S3, SQS, DynamoDB
  }
}

# EC2 Instance
resource "aws_instance" "ec2_worker" {
  ami           = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (us-east-1); update for your region
  instance_type = var.ec2_instance_type
  security_groups = [aws_security_group.ec2_sg.name]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install python3 -y
              pip3 install boto3
              echo "export S3_BUCKET=${var.s3_bucket_name}" >> /etc/environment
              echo "export SQS_QUEUE_URL=${aws_sqs_queue.image_processing_queue.url}" >> /etc/environment
              echo "export DYNAMODB_TABLE=${var.dynamodb_table_name}" >> /etc/environment
              # ec2_worker.py must be copied manually
              EOF

  tags = {
    Name = "ImageProcessingWorker"
  }
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "image_recognition_api" {
  name        = "ImageRecognitionApi"
  description = "API for image upload and processing"
}

resource "aws_api_gateway_resource" "image_resource" {
  rest_api_id = aws_api_gateway_rest_api.image_recognition_api.id
  parent_id   = aws_api_gateway_rest_api.image_recognition_api.root_resource_id
  path_part   = "upload"
}

resource "aws_api_gateway_method" "image_upload_method" {
  rest_api_id   = aws_api_gateway_rest_api.image_recognition_api.id
  resource_id   = aws_api_gateway_resource.image_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.image_recognition_api.id
  resource_id             = aws_api_gateway_resource.image_resource.id
  http_method             = aws_api_gateway_method.image_upload_method.http_method
  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = aws_lambda_function.image_upload_lambda.invoke_arn
}

resource "aws_api_gateway_method_response" "response_200" {
  rest_api_id = aws_api_gateway_rest_api.image_recognition_api.id
  resource_id = aws_api_gateway_resource.image_resource.id
  http_method = aws_api_gateway_method.image_upload_method.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "integration_response" {
  rest_api_id = aws_api_gateway_rest_api.image_recognition_api.id
  resource_id = aws_api_gateway_resource.image_resource.id
  http_method = aws_api_gateway_method.image_upload_method.http_method
  status_code = aws_api_gateway_method_response.response_200.status_code
}

resource "aws_api_gateway_deployment" "api_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration,
    aws_api_gateway_method_response.response_200,
    aws_api_gateway_integration_response.integration_response
  ]
  rest_api_id = aws_api_gateway_rest_api.image_recognition_api.id
  stage_name  = "prod"
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.image_upload_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.image_recognition_api.execution_arn}/*/POST/upload"
}

# Data source for account ID
data "aws_caller_identity" "current" {}

# Outputs
output "s3_bucket_name" {
  description = "S3 bucket for images"
  value       = aws_s3_bucket.image_bucket.bucket
}

output "sqs_queue_url" {
  description = "SQS queue URL"
  value       = aws_sqs_queue.image_processing_queue.url
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.image_tasks_table.name
}

output "api_endpoint" {
  description = "API Gateway endpoint for image upload"
  value       = "${aws_api_gateway_deployment.api_deployment.invoke_url}/upload"
}

output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.ec2_worker.id
}