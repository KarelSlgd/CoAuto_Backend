import json
import boto3
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}

cognito_client = boto3.client('cognito-idp')


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Invalid request body.'
        }

    photo = body.get('photo')
    access_token = body.get('access_token')

    if not photo or not access_token:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Missing parameters.'
        }

    response = update_photo(photo, access_token)

    return response


def update_photo(photo, access_token):
    try:
        cognito_client.update_user_attributes(
            AccessToken=access_token,
            UserAttributes=[
                {'Name': 'picture', 'Value': photo}
            ]
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': f'Failed to update user in Cognito: {str(e)}'
        }

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': 'User updated successfully.'
    }
