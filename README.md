Image Recognition System on AWS
This project is an Image Recognition System hosted on Amazon Web Services (AWS). It allows users to upload images, which are then processed using machine learning models to identify objects within the images. The system is designed to be scalable, secure, and cost-effective, making it suitable for general users who need to classify images (e.g., identifying animals or objects). It is built to handle moderate traffic with low latency responses.
Key Features

User Authentication: Secure authentication via AWS Cognito.
Image Upload and Processing: Handled through AWS API Gateway and AWS Lambda.
Asynchronous Task Handling: Managed using Amazon SQS and EC2 Auto Scaling for efficient processing.
Results Storage and Retrieval: Task metadata and results are stored in Amazon DynamoDB.
Monitoring and Notifications: System health is monitored via Amazon CloudWatch, with notifications sent through Amazon SNS.
Frontend: A user-friendly web interface hosted on Amazon S3.

Performance Targets

Handle up to 100 concurrent users.
Process images within 10 seconds.
Maintain 99.9% availability.

Architecture
The system leverages a variety of AWS services to meet both functional and non-functional requirements. Below is an overview of the architecture and the rationale behind the chosen services:

Compute:

AWS Lambda: Used for image upload and results retrieval due to its serverless nature and cost efficiency for short-lived tasks.
Amazon EC2: Used for compute-intensive image processing tasks, providing flexibility and scalability.
Alternatives considered: AWS Fargate and ECS, but Lambda and EC2 were chosen for their cost-effectiveness and suitability for the workload.


Storage:

Amazon S3: Stores images due to its durability, scalability, and cost-effectiveness.
Amazon DynamoDB: Stores task metadata and results for low-latency access.
Alternatives considered: Amazon EBS and RDS, but S3 and DynamoDB were preferred for their simplicity and performance.


Messaging:

Amazon SQS: Handles task queuing for asynchronous image processing.
Alternatives considered: Amazon SNS and Kinesis, but SQS was selected for its simplicity and reliability.


Authentication:

Amazon Cognito: Manages user authentication and integrates seamlessly with API Gateway.
Alternatives considered: AWS IAM and Okta, but Cognito was chosen for its managed service and ease of use.


Monitoring:

Amazon CloudWatch: Monitors system metrics and triggers alarms.
Amazon SNS: Sends notifications based on CloudWatch alarms.
Alternatives considered: Datadog and New Relic, but CloudWatch was sufficient for basic monitoring needs.



Architecture Diagram

Component Integration

Users interact with the frontend hosted on Amazon S3, which authenticates them via Amazon Cognito.
Authenticated users send requests to Amazon API Gateway, which routes:
POST /upload to the Image Upload Lambda, which stores images in S3 and sends task IDs to SQS.
GET /results/{taskId} to the GET Results Lambda, which queries DynamoDB for results.


EC2 instances in an Auto Scaling Group poll SQS, retrieve images from S3, process them, and store results in DynamoDB.
CloudWatch monitors SQS and triggers SNS notifications if the queue depth exceeds 100 messages.

Data Storage

Images: Stored in Amazon S3 for durability and scalability.
Task Metadata and Results: Stored in Amazon DynamoDB for low-latency access.

Programming Languages

Frontend: React (JavaScript) for a responsive user interface.
Lambda Functions: Python for simplicity and compatibility with AWS Lambda.
EC2 Image Processing: Python with OpenCV for image recognition tasks.

Deployment

Infrastructure as Code: Managed using Terraform.
Frontend Deployment: Uploaded to S3 using the AWS CLI.

Architecture Comparison
The architecture aligns with the Serverless and Event-Driven Architecture principles, using Lambda for short-lived tasks and EC2 for compute-intensive operations. Hosting the frontend on S3 is a cost-effective choice for a simple, low-traffic application, though it may lack advanced features like server-side rendering.
Delivery Model
The application is delivered as a Software as a Service (SaaS) model. Users access the system via a web interface, with all backend processing handled in the cloud. This model was chosen because:

It eliminates the need for users to manage infrastructure.
It allows for easy scaling based on demand.
It provides a pay-as-you-go cost structure, aligning with the system's cost-efficiency goals.

Security Considerations
Data Security
The system implements multiple layers of security:

Authentication: Amazon Cognito ensures only authenticated users can access the API Gateway.
API Gateway: Secured with a Cognito authorizer, validating IdToken for each request.
Amazon S3: Images are stored with private access, using temporary signed URLs for uploads and downloads.
Amazon DynamoDB: Accessed only by Lambda functions and EC2 instances with IAM roles, following the principle of least privilege.

Security Measures

Cognito User Pool: Manages user authentication and authorization.
IAM Roles: Lambda functions and EC2 instances use roles with minimal permissions.
Encryption: S3 and DynamoDB are configured with server-side encryption (SSE).

Vulnerabilities

The system lacks end-to-end encryption for image data in transit. This could be addressed by enforcing HTTPS for all communications.

Cost Analysis
Up-Front Costs

EC2 Instances: $0 (covered by AWS free tier or lab credits).
S3 Storage: $0 (minimal storage for development).

Ongoing Costs

Lambda: $0.20 per 1 million requests (free tier: 1 million requests/month).
S3: $0.023 per GB/month (first 5GB free).
DynamoDB: $0.25 per million reads/writes (free tier: 25 WCUs/RCUs).
EC2: $0.0116 per hour for t2.micro (free tier: 750 hours/month).

Additional Costs

SNS: $0.50 per million notifications (minimal for alerts).
CloudWatch: $0.30 per metric/month (minimal for SQS monitoring).

Alternative Approaches

Using AWS Fargate instead of EC2 for image processing could reduce management overhead but increase costs.
Using a managed database like RDS could simplify data management but is more expensive than DynamoDB.

Future Evolution
Potential features for future development include:

Real-Time Processing: Using AWS Kinesis for real-time image processing.
Advanced Analytics: Integrating Amazon Rekognition for more detailed image analysis.
Multi-Region Deployment: Using Route 53 and CloudFront for global availability and reduced latency.

