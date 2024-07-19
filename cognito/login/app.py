import json
import boto3
try:
    from database import get_secret, calculate_secret_hash, handle_response
except ImportError:
    from .database import get_secret, calculate_secret_hash, handle_response

from botocore.exceptions import ClientError

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError) as e:
        return handle_response(e, 'Cuerpo de la solicitud inválido.', 400)

    email = body.get('email')
    password = body.get('password')

    if not email or not password:
        return handle_response(None, 'Faltan parámetros en la solicitud.', 400)

    try:
        secret = get_secret()
        response = login_auth(email, password, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error', 500)


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
            'body': json.dumps({
                'statusCode': 200,
                'response': response['AuthenticationResult'],
                'role': role
            })
        }

    except client.exceptions.NotAuthorizedException as e:
        return handle_response(e, 'No autorizado', 401)

    except client.exceptions.UserNotConfirmedException as e:
        return handle_response(e, 'Usuario no confirmado', 412)

    except client.exceptions.PasswordResetRequiredException as e:
        return handle_response(e, 'Se requiere restablecimiento de contraseña', 428)

    except client.exceptions.UserNotFoundException as e:
        return handle_response(e, 'Usuario no encontrado', 404)

    except client.exceptions.TooManyRequestsException as e:
        return handle_response(e, 'Demasiadas solicitudes', 429)

    except client.exceptions.InvalidParameterException as e:
        return handle_response(e, 'Parámetro inválido', 400)

    except client.exceptions.InternalErrorException as e:
        return handle_response(e, 'Error interno', 500)

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ('ForbiddenException', 'InvalidLambdaResponseException', 'InvalidSmsRoleAccessPolicyException',
                          'InvalidSmsRoleTrustRelationshipException', 'InvalidUserPoolConfigurationException',
                          'ResourceNotFoundException', 'UnexpectedLambdaException', 'UserLambdaValidationException'):
            return handle_response(e, 'Solicitud inválida', 400)
        return handle_response(e, 'Ocurrió un error desconocido', 500)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error', 500)

