from dotenv import load_dotenv
import json
import boto3
from botocore.exceptions import ClientError

load_dotenv()

def lambda_handler(event, context):
    body = json.loads(event['body'])

    password = body['password']
    email = body['email']

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'User registered successfully.'
        })
    }