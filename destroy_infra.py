import boto3
import sys
from botocore.exceptions import ClientError

# REFINEMENT 1: Removed hardcoded BUCKET_NAME with undefined 'unique_id'
# Now bucket name will be provided as command line parameter for safety
SNS_TOPIC_NAME = 'NewOrderEvents'
SQS_QUEUE_NAME = 'ShippingQueue'
SQS_DLQ_NAME = 'ShippingQueueDLQ'

# REFINEMENT 2: Added region validation with fallback
# Initialize clients (will use default region from aws configure)
session = boto3.session.Session()
region = session.region_name
if not region:
    print("⚠️ No AWS region configured, using us-east-1 as default")
    region = 'us-east-1'

s3 = boto3.client('s3')
sns = boto3.client('sns')
sqs = boto3.client('sqs')   
sts = boto3.client('sts')

def get_account_id():
    # REFINEMENT 3: Changed to raise exception instead of returning None
    # This prevents silent failures in SNS topic ARN construction
    try:
        identity = sts.get_caller_identity()
        return identity['Account']
    except ClientError as e:
        print(f"❌ AWS error getting account ID: {e}")
        raise Exception("Cannot proceed without account ID")

def delete_s3_bucket(bucket_name):
    # REFINEMENT 4: Added bucket_name parameter instead of using global variable
    # This makes the function safer and more explicit
    print(f"🗑️ Deleting S3 Bucket: {bucket_name}...")
    try:
        # Delete all objects in the bucket first
        bucket = boto3.resource('s3').Bucket(bucket_name)
        bucket.objects.all().delete()
        # Now delete the bucket
        s3.delete_bucket(Bucket=bucket_name)
        print(f"   ✅ S3 Bucket deleted: {bucket_name}")
    except ClientError as e:
        print(f"❌ AWS error deleting S3 bucket: {e}")

def delete_sqs_queue():
    # REFINEMENT 5: Fixed f-string formatting (was missing 'f' prefix)
    # REFINEMENT 6: Fixed indentation consistency (was mixing spaces/tabs)
    print(f"🗑️ Deleting SQS Queue: {SQS_QUEUE_NAME}...")
    try:
        url = sqs.get_queue_url(QueueName=SQS_QUEUE_NAME)['QueueUrl']
        sqs.delete_queue(QueueUrl=url)
        print("   ✅ Queue deleted.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            print("   ⚠️ Queue does not exist, skipping.")
        else:
            print(f"❌ AWS error deleting SQS queue: {e}")

def delete_sqs_dlq():
    # REFINEMENT 7: Fixed f-string formatting (was missing 'f' prefix)
    # REFINEMENT 8: Fixed indentation consistency
    print(f"🗑️ Deleting SQS DLQ: {SQS_DLQ_NAME}...")
    try:
        url = sqs.get_queue_url(QueueName=SQS_DLQ_NAME)['QueueUrl']
        sqs.delete_queue(QueueUrl=url)
        print("   ✅ DLQ deleted.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            print("   ⚠️ DLQ does not exist, skipping.")
        else:
            print(f"❌ AWS error deleting SQS DLQ: {e}")

def delete_sns_topic():
    # REFINEMENT 9: Added proper error handling for account_id validation
    # REFINEMENT 10: Added try-catch around get_account_id() call
    print(f"🗑️ Deleting SNS Topic: {SNS_TOPIC_NAME}...")
    try:
        # Construct ARN manually to avoid listing all topics
        account_id = get_account_id()
        if not account_id:
            print("❌ Cannot delete SNS topic without account ID")
            return
        
        topic_arn = f"arn:aws:sns:{region}:{account_id}:{SNS_TOPIC_NAME}"
        sns.delete_topic(TopicArn=topic_arn)
        print("   ✅ Topic deleted.")
    except ClientError as e:
        print(f"❌ AWS error deleting SNS topic: {e}")
    except Exception as e:
        print(f"❌ Error deleting SNS topic: {e}")

def destroy(bucket_name=None):
    # REFINEMENT 11: Implemented Option 1 - Command line parameter for bucket name
    # REFINEMENT 12: Added input validation and usage instructions
    # REFINEMENT 13: Added safety warning before deletion
    # REFINEMENT 14: Added return status (True/False) for success/failure
    if not bucket_name:
        print("❌ Please provide bucket name:")
        print("Usage: python destroy_infra.py <bucket-name>")
        print("Example: python destroy_infra.py black-friday-orders-a1b2c3d4")
        return False
    
    print(f"🗑️ Destroying infrastructure for bucket: {bucket_name}")
    print("⚠️ This will permanently delete all resources!")
    
    try:
        delete_sqs_queue()
        delete_sqs_dlq()
        delete_sns_topic()
        delete_s3_bucket(bucket_name)
        print("✅ Infrastructure destruction complete.")
        return True
    except Exception as e:
        print(f"❌ Infrastructure destruction failed: {e}")
        return False

if __name__ == "__main__":
    # REFINEMENT 15: Added command line argument parsing
    # REFINEMENT 16: Proper handling of missing arguments
    if len(sys.argv) > 1:
        bucket_name = sys.argv[1]
        destroy(bucket_name)
    else:
        destroy()