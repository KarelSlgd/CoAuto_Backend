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

    if not email:
        return handle_response(None, 'Faltan parámetros en la solicitud.', 400)

    try:
        secret = get_secret()
        response = forgot_pass(email, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al solicitar el cambio de contraseña.', 500)


def forgot_pass(email, secret):
    client = boto3.client('cognito-idp')
    try:
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        response = client.forgot_password(
            ClientId=secret['COGNITO_CLIENT_ID'],
            Username=email,
            SecretHash=secret_hash
        )

    except client.exceptions.CodeDeliveryFailureException as e:
        return handle_response(e, 'Fallo en la entrega del código de verificación.', 500)

    except client.exceptions.ForbiddenException as e:
        return handle_response(e, 'Solicitud no permitida por AWS WAF.', 403)

    except client.exceptions.InternalErrorException as e:
        return handle_response(e, 'Error interno en Amazon Cognito.', 500)

    except client.exceptions.InvalidEmailRoleAccessPolicyException as e:
        return handle_response(e, 'Amazon Cognito no tiene permitido usar tu identidad de correo electrónico.', 403)

    except client.exceptions.InvalidLambdaResponseException as e:
        return handle_response(e, 'Respuesta inválida de AWS Lambda.', 502)

    except client.exceptions.InvalidParameterException as e:
        return handle_response(e, 'Parámetro inválido proporcionado.', 400)

    except client.exceptions.InvalidSmsRoleAccessPolicyException as e:
        return handle_response(e,
                               'El rol proporcionado para la configuración de SMS no tiene permiso para publicar usando Amazon SNS.',
                               403)

    except client.exceptions.InvalidSmsRoleTrustRelationshipException as e:
        return handle_response(e,
                               'La relación de confianza no es válida para el rol proporcionado para la configuración de SMS.',
                               403)

    except client.exceptions.LimitExceededException as e:
        return handle_response(e, 'Se ha excedido el límite para el recurso solicitado.', 429)

    except client.exceptions.NotAuthorizedException as e:
        return handle_response(e, 'No está autorizado para realizar esta acción.', 401)

    except client.exceptions.ResourceNotFoundException as e:
        return handle_response(e, 'Recurso no encontrado en Amazon Cognito.', 404)

    except client.exceptions.TooManyRequestsException as e:
        return handle_response(e, 'Se han realizado demasiadas solicitudes para esta operación.', 429)

    except client.exceptions.UnexpectedLambdaException as e:
        return handle_response(e, 'Excepción inesperada con AWS Lambda.', 502)

    except client.exceptions.UserLambdaValidationException as e:
        return handle_response(e, 'Excepción de validación del usuario con el servicio AWS Lambda.', 400)

    except client.exceptions.UserNotFoundException as e:
        return handle_response(e, 'Usuario no encontrado.', 404)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al solicitar el cambio de contraseña.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Solicitud de cambio de contraseña enviada correctamente.',
            'response': response
        })
    }
