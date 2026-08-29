import json
import boto3
import os
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sns = boto3.client('sns')
table = dynamodb.Table('Samples')

BUCKET = os.environ['DATA_BUCKET']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
RETENTION_YEARS = {
    'Block': 15,
    'Slide': 10
}

def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    retired_ids = []

    response = table.scan(
        FilterExpression='#s = :active',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':active': 'Active'}
    )
    items = response.get('Items', [])

    for item in items:
        sample_id = item['sampleId']
        sample_type = item['sampleType']
        upload_date = datetime.fromisoformat(item['uploadDate'])

        retention_limit_years = RETENTION_YEARS.get(sample_type, 10)
        age_years = (now - upload_date).days / 365.25

        if age_years >= retention_limit_years:
            file_location = item.get('fileLocation', '')

            if file_location.startswith('s3://'):
                key = file_location.replace(f's3://{BUCKET}/', '')
                try:
                    s3.delete_object(Bucket=BUCKET, Key=key)
                except Exception as e:
                    print(f"Could not delete S3 object for {sample_id}: {e}")

            table.update_item(
                Key={'sampleId': sample_id},
                UpdateExpression='SET #s = :deleted, deletedDate = :dd, deletionReason = :reason REMOVE fileLocation, storageClass',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={
                    ':deleted': 'Deleted',
                    ':dd': now.isoformat(),
                    ':reason': 'Retention period expired'
                }
            )
            retired_ids.append(sample_id)
            print(f"Retired {sample_id}, age {age_years:.1f} years")

    if retired_ids:
        message = f"Retention check retired {len(retired_ids)} sample(s):\n" + "\n".join(retired_ids)
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='NHS Sample Archive: retention deletions',
            Message=message
        )

    return {
        'statusCode': 200,
        'body': json.dumps(f'Retention check complete. {len(retired_ids)} samples retired.')
    }
