import json
import boto3
from database import get_secret, calculate_secret_hash, handle_response
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
    confirmation_code = body.get('confirmation_code')

    try:
        secret = get_secret()
        response = confirmation_registration(email, confirmation_code, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al confirmar el registro.', 500)


def confirmation_registration(email, confirmation_code, secret):
    client = boto3.client('cognito-idp')
    try:
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        client.confirm_sign_up(
            ClientId=secret['COGNITO_CLIENT_ID'],
            Username=email,
            ConfirmationCode=confirmation_code,
            SecretHash=secret_hash,
        )

    except client.exceptions.AliasExistsException as e:
        return handle_response(e, 'El alias ya existe.', 409)
    except client.exceptions.CodeMismatchException as e:
        return handle_response(e, 'El código proporcionado no coincide.', 401)
    except client.exceptions.ExpiredCodeException as e:
        return handle_response(e, 'El código ha expirado.', 410)
    except client.exceptions.ForbiddenException as e:
        return handle_response(e, 'Solicitud no permitida por AWS WAF.', 403)
    except client.exceptions.InternalErrorException as e:
        return handle_response(e, 'Error interno del servidor.', 500)
    except client.exceptions.InvalidLambdaResponseException as e:
        return handle_response(e, 'Respuesta inválida de AWS Lambda.', 502)
    except client.exceptions.InvalidParameterException as e:
        return handle_response(e, 'Parámetro inválido.', 400)
    except client.exceptions.LimitExceededException as e:
        return handle_response(e, 'Límite excedido para el recurso solicitado.', 429)
    except client.exceptions.NotAuthorizedException as e:
        return handle_response(e, 'Usuario no autorizado.', 403)
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
    except client.exceptions.UserNotFoundException as e:
        return handle_response(e, 'Usuario no encontrado.', 404)
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al confirmar el registro.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Registro confirmado correctamente.',
        })
    }
