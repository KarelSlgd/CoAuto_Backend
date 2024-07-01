import json
import boto3
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Invalid request body.'
        }

    previous_password = body.get('previous_password')
    new_password = body.get('new_password')
    token = body.get('access_token')

    try:
        response = change(previous_password, new_password, token)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def change(previous_password, new_password, token):
    try:
        client = boto3.client('cognito-idp')
        response = client.change_password(
            PreviousPassword=previous_password,
            ProposedPassword=new_password,
            AccessToken=token
        )

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps(response)
    }
