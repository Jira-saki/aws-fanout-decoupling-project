import boto3
import json
import uuid

# --- CONFIGURATION (ต้องแก้ให้ตรงกับ Output เมื่อกี้) ---
BUCKET_NAME = 'black-friday-orders-a565664d'  # <--- เอาชื่อถังที่คุณได้ มาใส่ตรงนี้!
# ----------------------------------------------------

s3 = boto3.client('s3')

def upload_orders(count=5):
    print(f"🚀 Uploading {count} orders to S3: {BUCKET_NAME}...")
    
    for i in range(count):
        order_id = str(uuid.uuid4())
        order_data = {
            'order_id': order_id,
            'customer': f'Customer-{i}',
            'amount': 100 * (i + 1),
            'status': 'confirmed'
        }
        
        file_name = f"order-{order_id}.json"
        
        # Upload directly from memory (ไม่ต้องสร้างไฟล์จริงลงเครื่อง)
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=json.dumps(order_data),
            ContentType='application/json'
        )
        print(f"   📤 Uploaded: {file_name}")

if __name__ == '__main__':
    upload_orders(5) # ลองยิงสัก 5 ออเดอร์