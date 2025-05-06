provider "aws" {
  region = "us-east-1"
}

# Variables
variable "s3_bucket_name" {
  description = "S3 bucket for images and Lambda code"
  type        = string
  default     = "image-recognition-bucket-b01021909"
}

variable "sqs_queue_name" {
  description = "SQS queue for task processing"
  type        = string
  default     = "image-processing-queue"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table for task metadata"
  type        = string
  default     = "ImageRecognitionTasks"
}

variable "lambda_function_name" {
  description = "Lambda function for image upload"
  type        = string
  default     = "ImageUploadHandler"
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

# Configure API Gateway account settings to use the existing LabRole
resource "aws_api_gateway_account" "api_gateway_account" {
  cloudwatch_role_arn = "arn:aws:iam::915696926220:role/LabRole"
}

# S3 Bucket for images and Lambda code
resource "aws_s3_bucket" "image_bucket" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_versioning" "image_bucket_versioning" {
  bucket = aws_s3_bucket.image_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
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
  name                       = var.sqs_queue_name
  visibility_timeout_seconds = 60
  receive_wait_time_seconds  = 10
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

# Lambda Function for POST /upload
resource "aws_lambda_function" "image_upload_lambda" {
  function_name = var.lambda_function_name
  handler       = "lambda_service.lambda_handler"
  runtime       = "python3.9"
  role          = "arn:aws:iam::915696926220:role/LabRole"
  timeout       = 30
  memory_size   = 128
  s3_bucket     = aws_s3_bucket.image_bucket.bucket
  s3_key        = "lambda_code/lambda_service.zip"
  environment {
    variables = {
      S3_BUCKET      = var.s3_bucket_name
      SQS_QUEUE_URL  = aws_sqs_queue.image_processing_queue.url
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }
}

# Lambda Function for GET /results/{taskId}
resource "aws_lambda_function" "get_image_results_lambda" {
  function_name = "GetImageResultsHandler"
  handler       = "get_image_results.lambda_handler"
  runtime       = "python3.8"
  role          = "arn:aws:iam::915696926220:role/LabRole"
  timeout       = 30
  memory_size   = 128
  s3_bucket     = aws_s3_bucket.image_bucket.bucket
  s3_key        = "lambda_code/get_image_results.zip"
  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
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
    cidr_blocks = ["0.0.0.0/0"]  # Restrict in production
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_instance_profile" "lab_role_profile" {
  name = "LabRoleProfile"
  role = "LabRole"
}

# EC2 Instances
resource "aws_instance" "ec2_worker_1" {
  ami           = "ami-07a6f770277670015"
  instance_type = var.ec2_instance_type
  security_groups = [aws_security_group.ec2_sg.name]
  key_name      = "cloud-proj"
  iam_instance_profile = aws_iam_instance_profile.lab_role_profile.name
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install python3 mesa-libGL -y
              curl -O https://bootstrap.pypa.io/get-pip.py
              python3 get-pip.py
              pip3 install boto3 opencv-python numpy
              echo "export S3_BUCKET=${var.s3_bucket_name}" >> /etc/environment
              echo "export SQS_QUEUE_URL=${aws_sqs_queue.image_processing_queue.url}" >> /etc/environment
              echo "export DYNAMODB_TABLE=${var.dynamodb_table_name}" >> /etc/environment
              aws s3 cp s3://image-recognition-bucket-b01021909/scripts/ec2_worker.py /home/ec2-user/ec2_worker.py
              chown ec2-user:ec2-user /home/ec2-user/ec2_worker.py
              su - ec2-user -c "nohup python3 /home/ec2-user/ec2_worker.py &"
              EOF
  tags = {
    Name = "ImageProcessingWorker1"
  }
}

resource "aws_instance" "ec2_worker_2" {
  ami           = "ami-07a6f770277670015"
  instance_type = var.ec2_instance_type
  security_groups = [aws_security_group.ec2_sg.name]
  key_name      = "cloud-proj"
  iam_instance_profile = aws_iam_instance_profile.lab_role_profile.name
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install python3 mesa-libGL -y
              curl -O https://bootstrap.pypa.io/get-pip.py
              python3 get-pip.py
              pip3 install boto3 opencv-python numpy
              echo "export S3_BUCKET=${var.s3_bucket_name}" >> /etc/environment
              echo "export SQS_QUEUE_URL=${aws_sqs_queue.image_processing_queue.url}" >> /etc/environment
              echo "export DYNAMODB_TABLE=${var.dynamodb_table_name}" >> /etc/environment
              aws s3 cp s3://image-recognition-bucket-b01021909/scripts/ec2_worker.py /home/ec2-user/ec2_worker.py
              chown ec2-user:ec2-user /home/ec2-user/ec2_worker.py
              su - ec2-user -c "nohup python3 /home/ec2-user/ec2_worker.py &"
              EOF
  tags = {
    Name = "ImageProcessingWorker2"
  }
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "image_recognition_api_new" {
  name        = "ImageRecognitionApiNew"
  description = "New API for image upload and processing with proper Lambda proxy integration"
}

resource "aws_api_gateway_resource" "image_resource_new" {
  rest_api_id = aws_api_gateway_rest_api.image_recognition_api_new.id
  parent_id   = aws_api_gateway_rest_api.image_recognition_api_new.root_resource_id
  path_part   = "upload"
}

resource "aws_api_gateway_method" "image_upload_method_new" {
  rest_api_id   = aws_api_gateway_rest_api.image_recognition_api_new.id
  resource_id   = aws_api_gateway_resource.image_resource_new.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration_new" {
  rest_api_id             = aws_api_gateway_rest_api.image_recognition_api_new.id
  resource_id             = aws_api_gateway_resource.image_resource_new.id
  http_method             = aws_api_gateway_method.image_upload_method_new.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.image_upload_lambda.invoke_arn
}

resource "aws_api_gateway_resource" "results_resource_new" {
  rest_api_id = aws_api_gateway_rest_api.image_recognition_api_new.id
  parent_id   = aws_api_gateway_rest_api.image_recognition_api_new.root_resource_id
  path_part   = "results"
}

resource "aws_api_gateway_resource" "results_taskid_resource_new" {
  rest_api_id = aws_api_gateway_rest_api.image_recognition_api_new.id
  parent_id   = aws_api_gateway_resource.results_resource_new.id
  path_part   = "{taskId}"
}

resource "aws_api_gateway_method" "results_get_method_new" {
  rest_api_id   = aws_api_gateway_rest_api.image_recognition_api_new.id
  resource_id   = aws_api_gateway_resource.results_taskid_resource_new.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "results_lambda_integration_new" {
  rest_api_id             = aws_api_gateway_rest_api.image_recognition_api_new.id
  resource_id             = aws_api_gateway_resource.results_taskid_resource_new.id
  http_method             = aws_api_gateway_method.results_get_method_new.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_image_results_lambda.invoke_arn
}

resource "aws_lambda_permission" "api_gateway_permission_new" {
  statement_id  = "AllowAPIGatewayInvokeNewPost"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.image_upload_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.image_recognition_api_new.execution_arn}/*/POST/upload"
}

resource "aws_lambda_permission" "results_api_gateway_permission_new" {
  statement_id  = "AllowAPIGatewayInvokeGetResultsNew"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_image_results_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.image_recognition_api_new.execution_arn}/*/GET/results/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "api_deployment_new" {
  rest_api_id = aws_api_gateway_rest_api.image_recognition_api_new.id
  depends_on = [
    aws_api_gateway_integration.lambda_integration_new,
    aws_api_gateway_integration.results_lambda_integration_new,
    aws_api_gateway_method.image_upload_method_new,
    aws_api_gateway_method.results_get_method_new,
    aws_lambda_permission.api_gateway_permission_new,
    aws_lambda_permission.results_api_gateway_permission_new
  ]
  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage with Access Logs
resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.image_recognition_api_new.id
  stage_name    = "prod"
  deployment_id = aws_api_gateway_deployment.api_deployment_new.id

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format          = "$context.requestId $context.identity.sourceIp $context.requestTime $context.httpMethod $context.path"
  }

  depends_on = [aws_api_gateway_account.api_gateway_account]
}

# CloudWatch Log Group for API Gateway Logs
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name = "api_gateway_logs"
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "ImageProcessingAlerts"
}

# SNS Subscription
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "ritvik.wuyyuru@gmail.com"  # Replace with your actual email
}

# CloudWatch Alarm for SQS Queue Depth
resource "aws_cloudwatch_metric_alarm" "sqs_backlog" {
  alarm_name          = "SQSBacklogAlarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300  # 5 minutes
  statistic           = "Average"
  threshold           = 100
  alarm_actions       = [aws_sns_topic.alerts.arn]
  dimensions = {
    QueueName = aws_sqs_queue.image_processing_queue.name
  }
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

output "api_endpoint_upload" {
  description = "API Gateway endpoint for image upload"
  value       = "https://${aws_api_gateway_rest_api.image_recognition_api_new.id}.execute-api.us-east-1.amazonaws.com/prod/upload"
}

output "api_endpoint_results" {
  description = "API Gateway endpoint for retrieving results"
  value       = "https://${aws_api_gateway_rest_api.image_recognition_api_new.id}.execute-api.us-east-1.amazonaws.com/prod/results"
}

output "api_gateway_id" {
  description = "API Gateway ID for debugging"
  value       = aws_api_gateway_rest_api.image_recognition_api_new.id
}

output "ec2_instance_ids" {
  description = "IDs of the EC2 instances"
  value       = [aws_instance.ec2_worker_1.id, aws_instance.ec2_worker_2.id]
}