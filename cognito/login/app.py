import json
import boto3
from database import get_secret, calculate_secret_hash
from botocore.exceptions import ClientError

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

    email = body.get('email')
    password = body.get('password')

    try:
        secret = get_secret()
        response = login_auth(email, password, secret)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def login_auth(email, password, secret):
    client = boto3.client('cognito-idp')
    try:
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)

        response = client.initiate_auth(
            ClientId=secret['COGNITO_CLIENT_ID'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            },
        )
        user_groups = client.admin_list_groups_for_user(
            Username=email,
            UserPoolId=secret['COGNITO_USER_POOL_ID']
        )
        role = None
        if user_groups['Groups']:
            role = user_groups['Groups'][0]['GroupName']
        return {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({'response': response['AuthenticationResult'], 'role': role})
        }

    except client.exceptions.NotAuthorizedException as not_authorized:
        return {
            'statusCode': 408,
            'headers': headers_cors,
            'body': json.dumps({'message': 'Not authorized', 'error': str(not_authorized)})
        }
    except client.exceptions.UserNotConfirmedException as user_not_confirmed:
        return {
            'statusCode': 408,
            'headers': headers_cors,
            'body': json.dumps({'message': 'User not confirmed', 'error': str(user_not_confirmed)})
        }
    except client.exceptions.PasswordResetRequiredException as password_reset_required:
        return {
            'statusCode': 408,
            'headers': headers_cors,
            'body': json.dumps({'message': 'Password reset required', 'error': str(password_reset_required)})
        }
    except client.exceptions.UserNotFoundException as user_not_found:
        return {
            'statusCode': 408,
            'headers': headers_cors,
            'body': json.dumps({'message': 'User not found', 'error': str(user_not_found)})
        }
    except client.exceptions.TooManyRequestsException as too_many_requests:
        return {
            'statusCode': 408,
            'headers': headers_cors,
            'body': json.dumps({'message': 'Too many requests', 'error': str(too_many_requests)})
        }
    except client.exceptions.InvalidParameterException as invalid_parameter:
        return {
            'statusCode': 408,
            'headers': headers_cors,
            'body': json.dumps({'message': 'Invalid parameter', 'error': str(invalid_parameter)})
        }
    except client.exceptions.InternalErrorException as internal_error:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps({'message': 'Internal error', 'error': str(internal_error)})
        }
    except ClientError as client_error:
        error_code = client_error.response['Error']['Code']
        if error_code in ('ForbiddenException', 'InvalidLambdaResponseException', 'InvalidSmsRoleAccessPolicyException',
                          'InvalidSmsRoleTrustRelationshipException', 'InvalidUserPoolConfigurationException',
                          'ResourceNotFoundException', 'UnexpectedLambdaException', 'UserLambdaValidationException'):
            return {
                'statusCode': 408,
                'headers': headers_cors,
                'body': json.dumps({'message': 'Invalid request', 'error': str(client_error)})
            }
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps({'message': 'An unknown error occurred', 'error': str(client_error)})
        }
    except Exception as ex:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps({'message': 'An unknown error occurred', 'error': str(ex)})
        }
