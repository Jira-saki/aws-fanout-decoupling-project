🛍️ Black Friday Order Processing System

A high-scale order processing system simulation for Black Friday events using AWS Serverless Architecture.

This project demonstrates the use of the Fan-out Pattern and Decoupling to build a resilient system capable of handling high traffic loads without crashing, leveraging the power of S3, SNS, and SQS via Python Boto3.

🏗️ Architecture Diagram

The system operates on an Event-Driven model: immediately upon an order file being uploaded to S3, the system distributes tasks (Fan-out) to various queues for asynchronous processing.

graph TD
    User((User)) -->|1. Upload Invoice| S3[("Amazon S3\n(Invoices Bucket)")]

    S3 -->|2. Trigger Event| SNS[("Amazon SNS Topic\n(NewOrderEvents)")]
    
    subgraph "Fan-out Pattern"
    SNS -->|Push| SQS_Ship[("AWS SQS\n(ShippingQueue)")]
    SNS -->|Push| SQS_Analytics[("AWS SQS\n(AnalyticsQueue)")]
    end
    
    subgraph "Fault Tolerance"
    SQS_Ship -.->|Failed 3x| DLQ[("Dead Letter Queue\n(ShippingDLQ)")]
    end

    style S3 fill:#2ecc71,stroke:#333,stroke-width:2px
    style SNS fill:#e67e22,stroke:#333,stroke-width:2px
    style SQS_Ship fill:#9b59b6,stroke:#333,stroke-width:2px
    style DLQ fill:#e74c3c,stroke:#333,stroke-width:2px

🚀 Key Features

Fan-out Pattern: Utilizing SNS to broadcast a single dataset to multiple destinations (SQS) simultaneously.

Decoupling: Using SQS as a buffer to prevent downstream systems (Consumers) from being overwhelmed during traffic spikes.

Fault Tolerance: Configuring Dead Letter Queues (DLQ) and Redrive Policies to capture problematic messages (Bugs/Corrupted Data).

Infrastructure as Code (IaC): Leveraging Boto3 to provision the entire infrastructure using Python scripts.

📋 Prerequisites

Python 3.x

AWS CLI (Installed and Configured)

aws configure

# Input your Access Key / Secret Key / Region (us-east-1 recommended)

IAM Permissions: The user running the script must have the following permissions:

AmazonS3FullAccess

AmazonSNSFullAccess

AmazonSQSFullAccess

🛠️ How to Run

1. Install Dependencies

pip install boto3

2. Provision Infrastructure

Run the main script to create the S3 Bucket, SNS Topic, SQS Queue, and attach all necessary Policies.

python 1_setup_infra.py

Output: You will receive the SQS Queue URL and the S3 Bucket name ready for use.

3. Test the System

Go to the AWS Console and navigate to S3.

Upload any file (e.g., test.json) to the bucket black-friday-orders-2025-xx.

Navigate to the SQS Console and check ShippingQueue.

Click Send and receive messages -> Poll for messages.

You will see a new message arrive! (The content will be the Event notification from S3).

📂 Project Structure

1_setup_infra.py: The main script for provisioning AWS Resources and configuring Permissions (Policies).

(Optional) producer.py: Script to simulate uploading files to S3.

(Optional) consumer.py: Script to simulate a Worker polling tasks from SQS.

🧹 Cleanup

To avoid unexpected charges, remember to remove resources after testing:

S3: Delete all files inside the bucket, then delete the bucket itself.

SQS: Delete the ShippingQueue and ShippingQueueDLQ.

SNS: Delete the NewOrderEvents Topic.

Created for AWS Cloud Engineer Journey 🚀
