# LambdaVision

**LambdaVision** is a cloud-based platform developed for the **Cloud Computing Term Assignment** at Dalhousie University. The system allows users to upload images, which are then processed using MobileNetSSD, which combines MobileNet, a streamlined convolutional neural network (CNN) architecture, with Single Shot MultiBox Detector (SSD), a method for detecting objects in images in a single pass to identify objects within the images. The primary goal of the system is to provide a scalable, secure, and cost-effective solution for image recognition tasks. The system is designed for general users who need to classify images (e.g., identifying animals, multiple objects in a single image) and is expected to handle moderate traffic with low latency responses.

---

## Features

- 🔐 **User Authentication**: Secure login and signup via AWS Cognito
- 📤 **Image Upload and Processing**: Seamless image uploads through AWS API Gateway and Lambda
- ⏳ **Asynchronous Task Handling**: Efficient processing with Amazon SQS and EC2 Auto Scaling
- 💾 **Results Storage and Retrieval**: Fast access to task metadata and results using Amazon DynamoDB
- 📊 **Monitoring and Notifications**: Real-time system health tracking with Amazon CloudWatch and SNS
- 🌐 **Responsive Frontend**: User-friendly web interface hosted on Amazon S3
- ⚙️ **Infrastructure as Code**: Automated deployment with Terraform

---

## Tech Stack

- **Frontend**: React (JavaScript)
- **Backend**: Python (AWS Lambda, EC2)
- **Compute**: AWS Lambda, Amazon EC2
- **Storage**: Amazon S3, Amazon DynamoDB
- **Messaging**: Amazon SQS
- **Authentication**: AWS Cognito
- **Monitoring**: Amazon CloudWatch, Amazon SNS
- **Infrastructure**: Terraform
- **Image Processing**: OpenCV (Python)
- **Deployment**: AWS CLI

---
