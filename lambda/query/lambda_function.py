import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Samples')

def lambda_handler(event, context):
    sample_id = event.get('pathParameters', {}).get('sampleId')

    if not sample_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing sampleId'})
        }

    response = table.get_item(Key={'sampleId': sample_id})
    item = response.get('Item')

    if not item:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Sample {sample_id} not found'})
        }

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(item)
    }
