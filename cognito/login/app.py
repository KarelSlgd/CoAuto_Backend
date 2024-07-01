import json
import boto3
from database import get_secret, calculate_secret_hash

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

    except client.exceptions.CodeDeliveryFailureException as code_delivery_failure:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Code delivery failure: {str(code_delivery_failure)}')

        }

    except client.exceptions.ForbiddenException as forbidden:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Forbidden: {str(forbidden)}')
        }

    except client.exceptions.InternalErrorException as internal_error:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'Internal error: {str(internal_error)}')
        }

    except client.exceptions.InvalidEmailRoleAccessPolicyException as invalid_email_role_access_policy:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Invalid email role access policy: {str(invalid_email_role_access_policy)}')
        }

    except client.exceptions.InvalidLambdaResponseException as invalid_lambda_response:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Invalid lambda response: {str(invalid_lambda_response)}')
        }

    except client.exceptions.InvalidParameterException as invalid_parameter:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Invalid parameter: {str(invalid_parameter)}')
        }

    except client.exceptions.InvalidPasswordException as invalid_password:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Invalid password: {str(invalid_password)}')
        }

    except client.exceptions.InvalidSmsRoleAccessPolicyException as invalid_sms_role_access_policy:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Invalid SMS role access policy: {str(invalid_sms_role_access_policy)}')
        }

    except client.exceptions.InvalidSmsRoleTrustRelationshipException as invalid_sms_role_trust_relationship:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Invalid SMS role trust relationship: {str(invalid_sms_role_trust_relationship)}')
        }

    except client.exceptions.LimitExceededException as limit_exceeded:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Limit exceeded: {str(limit_exceeded)}')
        }

    except client.exceptions.NotAuthorizedException as no_authorization:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Not authorized: {str(no_authorization)}')
        }

    except client.exceptions.ResourceNotFoundException as resource_not_found:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Resource not found: {str(resource_not_found)}')
        }

    except client.exceptions.TooManyRequestsException as too_many_requests:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Too many requests: {str(too_many_requests)}')
        }

    except client.exceptions.UnexpectedLambdaException as unexpected_lambda:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Unexpected lambda exception: {str(unexpected_lambda)}')

        }

    except client.exceptions.UserLambdaValidationException as user_lambda_validation:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'User lambda validation exception: {str(user_lambda_validation)}')

        }

    except client.exceptions.UsernameExistsException as username_exists:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps(f'Username exists: {str(username_exists)}')
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }
