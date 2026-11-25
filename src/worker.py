import boto3
import json
import time
import os

from urllib.parse import unquote_plus

REGION = os.getenv("AWS_REGION", "eu-central-1")

s3 = boto3.client("s3", region_name=REGION)
sqs = boto3.client("sqs", region_name=REGION)

BUCKET_NAME = os.environ["BUCKET_NAME"]

QUEUE_URL = os.environ["QUEUE_URL"]

PROCESSING_DELAY = int(os.getenv("PROCESSING_DELAY", "10"))

def receive_job():
    response = sqs.receive_message(
        QueueUrl = QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20,
        VisibilityTimeout=120
    )

    messages = response.get("Messages", [])

    return messages[0] if messages else None

def extract_s3_locations(message):
    body = json.loads(message["Body"])

    if body.get("Event") == "s3:TestEvent":
        return []

    locations = []

    for record in body["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        locations.append((bucket, key))

    return locations

def read_raw_data(bucket, key):
    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    content = response["Body"].read()

    return json.loads(content)

def transform_data(transactions):
    processed = []

    for transaction in transactions:
        enriched = transaction.copy()

        enriched["total_amount"] = round(
            transaction["quantity"] * transaction["unit_price"],
            2
        )

        processed.append(enriched)

    return processed

def write_processed_data(bucket, key, transactions):
    output_key = key.replace("raw/", "processed/", 1)

    s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=json.dumps(transactions),
        ContentType="application/json"
    )

    return output_key

def delete_job(message):
    sqs.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=message["ReceiptHandle"]
    )

def main():
    print("Worker started", flush=True)

    while True:
        try:
            message = receive_job()

            if message is None:
                continue

            locations = extract_s3_locations(message)

            for bucket, key in locations:
                print(f"Processing: {key}", flush=True)

                transactions = read_raw_data(bucket, key)
                processed = transform_data(transactions)

                time.sleep(PROCESSING_DELAY)

                output_key = write_processed_data(
                    bucket, key, processed
                )

                print(f"Completed: {output_key}", flush=True)

            delete_job(message)

        except Exception as error:
            print(f"Worker error: {error}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
