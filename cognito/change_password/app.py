import json
import boto3


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': 'Invalid request body.'
        }

    previous_password = body.get('previous_password')
    new_password = body.get('new_password')
    token = body.get('token')

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
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
