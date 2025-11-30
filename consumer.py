import boto3
import json
import time

# --- CONFIGURATION ---
QUEUE_NAME = 'ShippingQueue'
# ---------------------

sqs = boto3.client('sqs')

def get_queue_url():
    # Helper function to get URL by name
    return sqs.get_queue_url(QueueName=QUEUE_NAME)['QueueUrl']

def process_messages():
    queue_url = get_queue_url()
    print(f"👷 Worker listening on: {QUEUE_NAME}...")
    print(f"🔗 URL: {queue_url}")
    
    while True:
        # Long Polling (รอ 10 วิ)
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=10
        )
        
        if 'Messages' in response:
            print(f"⚡ Received {len(response['Messages'])} messages!")
            
            for msg in response['Messages']:
                # แกะกล่อง 2 ชั้น: SQS Body -> SNS Message -> S3 Event
                body = json.loads(msg['Body'])
                sns_msg = json.loads(body['Message'])
                
                # ข้อมูลจริงๆ ของ S3 อยู่ใน 'Records'
                if 'Records' in sns_msg:
                    for record in sns_msg['Records']:
                        file_name = record['s3']['object']['key']
                        size = record['s3']['object']['size']
                        print(f"   📦 Processing Order File: {file_name} (Size: {size} bytes)")
                
                # จำลองการทำงานเสร็จ -> ลบออกจากคิว
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg['ReceiptHandle']
                )
                print("   ✅ Done & Deleted")
        else:
            print("💤 No orders... waiting...")

if __name__ == '__main__':
    try:
        process_messages()
    except KeyboardInterrupt:
        print("\n🛑 Worker stopped.")