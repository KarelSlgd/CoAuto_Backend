import json
import boto3
from database import get_secret, calculate_secret_hash, handle_response
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
        return handle_response(None, 'Cuerpo de la solicitud inválido.', 400)

    email = body.get('email')

    try:
        secret = get_secret()
        response = resend_code(email, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al solicitar el reenvío del código de confirmación.', 500)


def resend_code(email, secret):
    client = boto3.client('cognito-idp')
    try:
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        client.resend_confirmation_code(
            ClientId=secret['COGNITO_CLIENT_ID'],
            SecretHash=secret_hash,
            Username=email
        )

    except client.exceptions.CodeDeliveryFailureException as e:
        return handle_response(e, 'Error al enviar el código de verificación.', 400)

    except client.exceptions.ForbiddenException as e:
        return handle_response(e, 'Solicitud no permitida por AWS WAF.', 403)

    except client.exceptions.InternalErrorException as e:
        return handle_response(e, 'Error interno en Amazon Cognito.', 500)

    except client.exceptions.InvalidEmailRoleAccessPolicyException as e:
        return handle_response(e, 'Amazon Cognito no tiene permiso para usar su identidad de correo electrónico.', 400)

    except client.exceptions.InvalidLambdaResponseException as e:
        return handle_response(e, 'Respuesta inválida de AWS Lambda.', 400)

    except client.exceptions.InvalidParameterException as e:
        return handle_response(e, 'Parámetro inválido en la solicitud.', 400)

    except client.exceptions.InvalidSmsRoleAccessPolicyException as e:
        return handle_response(e, 'Rol no tiene permiso para publicar usando Amazon SNS.', 400)

    except client.exceptions.InvalidSmsRoleTrustRelationshipException as e:
        return handle_response(e,
                               'Relación de confianza inválida para el rol proporcionado para la configuración de SMS.',
                               400)

    except client.exceptions.LimitExceededException as e:
        return handle_response(e, 'Límite de recursos de AWS excedido.', 429)

    except client.exceptions.NotAuthorizedException as e:
        return handle_response(e, 'Usuario no autorizado.', 401)

    except client.exceptions.ResourceNotFoundException as e:
        return handle_response(e, 'Recurso no encontrado en Amazon Cognito.', 404)

    except client.exceptions.TooManyRequestsException as e:
        return handle_response(e, 'Demasiadas solicitudes en un período corto.', 429)

    except client.exceptions.UnexpectedLambdaException as e:
        return handle_response(e, 'Excepción inesperada con AWS Lambda.', 400)

    except client.exceptions.UserLambdaValidationException as e:
        return handle_response(e, 'Excepción de validación de usuario con AWS Lambda.', 400)

    except client.exceptions.UserNotFoundException as e:
        return handle_response(e, 'Usuario no encontrado.', 404)

    except ClientError as e:
        return handle_response(e, 'Error inesperado en el cliente de AWS.', 500)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al solicitar el reenvío del código de confirmación.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Código de confirmación reenviado correctamente.'
        })
    }
