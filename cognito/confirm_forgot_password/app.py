import json
import boto3
try:
    from database import get_secret, calculate_secret_hash, handle_response
except ImportError:
    from .database import get_secret, calculate_secret_hash, handle_response

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return handle_response(None, 'Cuerpo de la solicitud inválido.', 400)

    email = body.get('email')
    code = body.get('code')
    password = body.get('password')

    if not email or not code or not password:
        return handle_response(None, 'Faltan parámetros en la solicitud.', 400)

    try:
        secret = get_secret()
        response = confirm_password(email, code, password, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al confirmar la contraseña.', 500)


def confirm_password(email, code, password, secret):
    client = boto3.client('cognito-idp')
    try:
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        response = client.confirm_forgot_password(
            ClientId=secret['COGNITO_CLIENT_ID'],
            Username=email,
            ConfirmationCode=code,
            Password=password,
            SecretHash=secret_hash
        )

    except client.exceptions.CodeMismatchException as e:
        return handle_response(e, 'El código proporcionado no coincide.', 400)

    except client.exceptions.ExpiredCodeException as e:
        return handle_response(e, 'El código ha expirado.', 400)

    except client.exceptions.ForbiddenException as e:
        return handle_response(e, 'Solicitud no permitida por AWS WAF.', 403)

    except client.exceptions.InternalErrorException as e:
        return handle_response(e, 'Error interno en Amazon Cognito.', 500)

    except client.exceptions.InvalidLambdaResponseException as e:
        return handle_response(e, 'Respuesta inválida de AWS Lambda.', 502)

    except client.exceptions.InvalidParameterException as e:
        return handle_response(e, 'Parámetro inválido.', 400)

    except client.exceptions.InvalidPasswordException as e:
        return handle_response(e, 'Contraseña inválida.', 400)

    except client.exceptions.LimitExceededException as e:
        return handle_response(e, 'Se excedió el límite para el recurso solicitado.', 429)

    except client.exceptions.NotAuthorizedException as e:
        return handle_response(e, 'No autorizado.', 401)

    except client.exceptions.ResourceNotFoundException as e:
        return handle_response(e, 'Recurso no encontrado.', 404)

    except client.exceptions.TooManyFailedAttemptsException as e:
        return handle_response(e, 'Demasiados intentos fallidos.', 429)

    except client.exceptions.TooManyRequestsException as e:
        return handle_response(e, 'Demasiadas solicitudes.', 429)

    except client.exceptions.UnexpectedLambdaException as e:
        return handle_response(e, 'Excepción inesperada con AWS Lambda.', 502)

    except client.exceptions.UserLambdaValidationException as e:
        return handle_response(e, 'Excepción de validación de usuario con AWS Lambda.', 400)

    except client.exceptions.UserNotConfirmedException as e:
        return handle_response(e, 'Usuario no confirmado.', 400)

    except client.exceptions.UserNotFoundException as e:
        return handle_response(e, 'Usuario no encontrado.', 404)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al confirmar la contraseña.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Contraseña confirmada correctamente.',
            'response': response
        })
    }
