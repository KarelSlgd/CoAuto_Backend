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
        return handle_response(None, 'Cuerpo de la solicitud inválido.', 400)

    previous_password = body.get('previous_password')
    new_password = body.get('new_password')
    token = body.get('access_token')

    if not previous_password or not new_password or not token:
        return handle_response(None, 'Faltan parámetros en la solicitud.', 400)

    try:
        response = change(previous_password, new_password, token)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al cambiar la contraseña.', 500)


def change(previous_password, new_password, token):
    client = boto3.client('cognito-idp')
    try:
        response = client.change_password(
            PreviousPassword=previous_password,
            ProposedPassword=new_password,
            AccessToken=token
        )

    except client.exceptions.ForbiddenException as e:
        return handle_response(e,
                               'AWS WAF no permite tu solicitud basado en un ACL web asociado a tu grupo de usuarios.',
                               403)

    except client.exceptions.InternalErrorException as e:
        return handle_response(e, 'Amazon Cognito encontró un error interno.', 500)

    except client.exceptions.InvalidParameterException as e:
        return handle_response(e, 'Amazon Cognito encontró un parámetro inválido.', 400)

    except client.exceptions.InvalidPasswordException as e:
        return handle_response(e, 'Amazon Cognito encontró una contraseña inválida.', 400)

    except client.exceptions.LimitExceededException as e:
        return handle_response(e, 'Se ha excedido el límite para un recurso solicitado de AWS.', 429)

    except client.exceptions.NotAuthorizedException as e:
        return handle_response(e, 'No estás autorizado.', 401)

    except client.exceptions.PasswordResetRequiredException as e:
        return handle_response(e, 'Se requiere un restablecimiento de contraseña.', 412)

    except client.exceptions.ResourceNotFoundException as e:
        return handle_response(e, 'Amazon Cognito no puede encontrar el recurso solicitado.', 404)

    except client.exceptions.TooManyRequestsException as e:
        return handle_response(e, 'Has realizado demasiadas solicitudes para una operación dada.', 429)

    except client.exceptions.UserNotConfirmedException as e:
        return handle_response(e, 'El usuario no fue confirmado exitosamente.', 412)

    except client.exceptions.UserNotFoundException as e:
        return handle_response(e, 'El usuario no fue encontrado.', 404)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al cambiar la contraseña.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Contraseña cambiada correctamente.',
            'response': response
        })
    }


def handle_response(error, message, status_code):
    return {
        'statusCode': status_code,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': status_code,
            'message': message,
            'error': str(error)
        })
    }
