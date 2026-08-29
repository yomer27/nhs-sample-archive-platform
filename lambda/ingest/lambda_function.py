import json
import boto3
import urllib.parse
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Samples')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])

        if key.endswith('/'):
            continue

        parts = key.split('/')
        if len(parts) != 3:
            print(f"Skipping unexpected key format: {key}")
            continue

        archive_prefix, type_folder, filename = parts
        sample_id = filename.replace('.json', '')

        sample_type = 'Block' if type_folder == 'blocks' else 'Slide'

        id_parts = sample_id.split('-')
        sending_hospital = id_parts[1] if len(id_parts) > 1 else 'UNKNOWN'
        archive_site = 'Highgate Archive' if archive_prefix == 'highgate' else 'Kingswood Archive'

        item = {
            'sampleId': sample_id,
            'sampleType': sample_type,
            'sendingHospital': sending_hospital,
            'archiveSite': archive_site,
            'uploadDate': datetime.now(timezone.utc).isoformat(),
            'fileLocation': f's3://{bucket}/{key}',
            'storageClass': 'STANDARD',
            'status': 'Active'
        }

        table.put_item(Item=item)
        print(f"Wrote metadata for {sample_id}")

    return {
        'statusCode': 200,
        'body': json.dumps('Ingest complete')
    }
