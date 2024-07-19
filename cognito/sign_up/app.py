import json
import boto3
try:
    from database import get_secret, calculate_secret_hash, get_connection, handle_response
except ImportError:
    from .database import get_secret, calculate_secret_hash, get_connection, handle_response

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

    password = body.get('password')
    email = body.get('email')
    name = body.get('name')
    lastname = body.get('lastname')

    if not password or not email or not name or not lastname:
        return handle_response(None, 'Faltan parámetros.', 400)

    if len(name) > 50:
        return handle_response(None, 'El nombre no puede exceder los 50 caracteres.', 400)

    if len(lastname) > 100:
        return handle_response(None, 'El apellido no puede exceder los 100 caracteres.', 400)

    try:
        secret = get_secret()
        response = register_user(email, password, name, lastname, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al registrar el usuario.', 500)


def register_user(email, password, name, lastname, secret):
    client = boto3.client('cognito-idp')
    try:
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        response = client.sign_up(
            ClientId=secret['COGNITO_CLIENT_ID'],
            SecretHash=secret_hash,
            Username=email,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                }
            ]
        )
        client.admin_add_user_to_group(
            UserPoolId=secret['COGNITO_USER_POOL_ID'],
            Username=email,
            GroupName=secret['COGNITO_GROUP_NAME']
        )

    except client.exceptions.CodeDeliveryFailureException as e:
        return handle_response(e, 'Error en la entrega del código de verificación.', 400)

    except client.exceptions.ForbiddenException as e:
        return handle_response(e, 'Solicitud no permitida por AWS WAF.', 403)

    except client.exceptions.InternalErrorException as e:
        return handle_response(e, 'Error interno en Amazon Cognito.', 500)

    except client.exceptions.InvalidEmailRoleAccessPolicyException as e:
        return handle_response(e, 'No se permite usar la identidad de correo electrónico.', 403)

    except client.exceptions.InvalidLambdaResponseException as e:
        return handle_response(e, 'Respuesta inválida de AWS Lambda.', 400)

    except client.exceptions.InvalidParameterException as e:
        return handle_response(e, 'Parámetro inválido en la solicitud.', 400)

    except client.exceptions.InvalidPasswordException as e:
        return handle_response(e, 'Contraseña inválida.', 400)

    except client.exceptions.InvalidSmsRoleAccessPolicyException as e:
        return handle_response(e, 'El rol de SMS no tiene permiso para publicar usando Amazon SNS.', 403)

    except client.exceptions.InvalidSmsRoleTrustRelationshipException as e:
        return handle_response(e, 'Relación de confianza no válida para el rol de SMS.', 403)

    except client.exceptions.LimitExceededException as e:
        return handle_response(e, 'Se ha excedido el límite para el recurso solicitado.', 429)

    except client.exceptions.NotAuthorizedException as e:
        return handle_response(e, 'Usuario no autorizado.', 401)

    except client.exceptions.ResourceNotFoundException as e:
        return handle_response(e, 'Recurso no encontrado.', 404)

    except client.exceptions.TooManyRequestsException as e:
        return handle_response(e, 'Demasiadas solicitudes para la operación.', 429)

    except client.exceptions.UnexpectedLambdaException as e:
        return handle_response(e, 'Excepción inesperada con AWS Lambda.', 500)

    except client.exceptions.UserLambdaValidationException as e:
        return handle_response(e, 'Excepción de validación del usuario con AWS Lambda.', 400)

    except client.exceptions.UsernameExistsException as e:
        return handle_response(e, 'El nombre de usuario ya existe en el grupo de usuarios.', 409)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error.', 500)

    insert_into_user(email, response['UserSub'], name, lastname)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Se ha enviado un correo de confirmación.',
            'response': response['UserSub']
        })
    }


def insert_into_user(email, id_cognito, name, lastname):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO user (email, id_cognito, name, lastname, id_role, id_status) VALUES (%s, %s, %s, %s, 2, 1)"
            cursor.execute(insert_query, (email, id_cognito, name, lastname))
            connection.commit()

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al registrar el usuario.', 500)

    finally:
        connection.close()
