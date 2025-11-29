import boto3
import json
import uuid
from botocore.exceptions import ClientError

# Initialize clients (will use default region from aws configure)
session = boto3.session.Session()
region = session.region_name
s3 = boto3.client('s3')
sns = boto3.client('sns')
sqs = boto3.client('sqs')
# Generate a unique ID to avoid name collisions
unique_id = str(uuid.uuid4())[:8]
BUCKET_NAME = f'black-friday-orders-{unique_id}'
SNS_TOPIC_NAME = 'NewOrderEvents'
SQS_QUEUE_NAME = 'ShippingQueue'
SQS_DLQ_NAME = 'ShippingQueueDLQ'

def setup():
    try:
        print("Setting up infrastructure...")

        # 1.Create SNS topic
        topic = sns.create_topic(Name=SNS_TOPIC_NAME)
        topic_arn = topic['TopicArn']
        print(f"SNS Topic created: {topic_arn}")

        # 2.1 Create SQS Dead Letter Queue (DLQ)
        dlq = sqs.create_queue(QueueName=SQS_DLQ_NAME)
        dlq_arn = sqs.get_queue_attributes(
            QueueUrl=dlq['QueueUrl'],
            AttributeNames=['QueueArn']
        )['Attributes']['QueueArn']
        print(f"SQS DLQ created: {dlq_arn}")

        # 2.2 Create Main Queue with DLQ binding (Redrive Policy)
        redrive_policy = {
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': 3  # After 3 failed attempts, send to DLQ
        }

        queue = sqs.create_queue(
            QueueName=SQS_QUEUE_NAME,
            # After 3 failed attempts, redirect to Dead Letter Queue
            Attributes={
                'RedrivePolicy': json.dumps(redrive_policy)
            }
        )
        queue_url = queue['QueueUrl']
        queue_arn = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )['Attributes']['QueueArn']
        print(f"SQS Queue created: {queue_url}")

        # 3. Allow SNS to send messages to SQS (Policy Configuration)
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "sns.amazonaws.com"},
                    "Action": "sqs:SendMessage",
                    "Resource": queue_arn,
                    "Condition": {
                        "ArnEquals": {"aws:SourceArn": topic_arn}
                    }
                }
            ]
        }
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={
                'Policy': json.dumps(policy_document)
            }
        )
        print("SQS Policy updated to allow SNS publishing.")
        
        # 4. Subscribe SQS to SNS topic
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol='sqs',
            Endpoint=queue_arn,
            ReturnSubscriptionArn=True
        )
        print("✅ Subscribed SQS to SNS")

        # 5. Allow S3 to publish to SNS (SNS Access Policy)
        # Grant S3 service permission to publish messages to this SNS topic
        # Only allow S3 events from our specific bucket (security condition)
        sns_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "s3.amazonaws.com"},
                    "Action": "SNS:Publish",
                    "Resource": topic_arn,
                    "Condition": {
                        "ArnLike": {"aws:SourceArn": f"arn:aws:s3:::{BUCKET_NAME}"}
                    }
                }
            ]
        }
        sns.set_topic_attributes(
            TopicArn=topic_arn,
            AttributeName='Policy',
            AttributeValue=json.dumps(sns_policy_document)
        )
        print("SNS Topic Policy updated to allow S3 publishing.")

        # 6. Create S3 Bucket and configure Event Notification
        if region and region != 'us-east-1':
            s3.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': region} # ap-northeast-03
            )
        else:
            s3.create_bucket(Bucket=BUCKET_NAME)
        
        print(f"S3 Bucket created: {BUCKET_NAME}")
        s3.put_bucket_notification_configuration(
            Bucket=BUCKET_NAME,
            NotificationConfiguration={
                'TopicConfigurations': [
                    {
                        'TopicArn': topic_arn,
                        'Events': ['s3:ObjectCreated:*']
                    }
                ]
            }
        )
        print(f"✅ S3 Bucket Created & Notification Configured: {BUCKET_NAME}")
        print("Infrastructure setup complete. 🎉")
        return True
    
    except ClientError as e:
        print(f"❌ AWS error during infrastructure setup: {e}")
        print("Infrastructure setup FAILED")
        return False   # stop execution on AWS errors
    except Exception as e:
        print(f"An error occurred: {e}")
        return False   # stop execution on general errors
    

if __name__ == "__main__":
    setup()