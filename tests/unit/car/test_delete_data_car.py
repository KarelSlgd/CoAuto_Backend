import json
import unittest
from unittest.mock import patch
from json import JSONDecodeError
from botocore.exceptions import ClientError
import base64
import pymysql

from car.delete_data_car.app import lambda_handler, delete_car
from car.delete_data_car.connection import get_connection, handle_response, handle_response_success, get_jwt_claims, get_secret, headers_cors


class TestDeleteCar(unittest.TestCase):

    @patch('car.delete_data_car.app.get_jwt_claims')
    @patch('car.delete_data_car.app.handle_response')
    def test_missing_token(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {}
        }
        lambda_handler(event, None)
        mock_handle_response.assert_called_with('Missing token.', 'Faltan parámetros.', 401)

    @patch('car.delete_data_car.app.get_jwt_claims')
    @patch('car.delete_data_car.app.handle_response')
    def test_invalid_role(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'some_token'}
        }
        mock_get_jwt_claims.return_value = {'cognito:groups': ['ClientUserGroup']}
        lambda_handler(event, None)
        mock_handle_response.assert_called_with('Acceso denegado. El rol no puede ser cliente.', 'Acceso denegado.',
                                                401)

    @patch('car.delete_data_car.app.get_jwt_claims')
    @patch('car.delete_data_car.app.handle_response')
    def test_missing_parameters(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'some_token'},
            'body': json.dumps({})
        }
        lambda_handler(event, None)
        mock_handle_response.assert_called_with(None, 'Faltan parámetros.', 400)

    @patch('car.delete_data_car.app.delete_car')
    @patch('car.delete_data_car.app.get_jwt_claims')
    @patch('car.delete_data_car.app.handle_response')
    def test_delete_car_called(self, mock_handle_response, mock_get_jwt_claims, mock_delete_car):
        event = {
            'headers': {'Authorization': 'some_token'},
            'body': json.dumps({'id_auto': 1, 'id_status': 2})
        }
        mock_get_jwt_claims.return_value = {'cognito:groups': ['ValidUserGroup']}
        mock_delete_car.return_value = 'some_response'

        result = lambda_handler(event, None)
        mock_delete_car.assert_called_with(1, 2)
        self.assertEqual(result, 'some_response')

    @patch('car.delete_data_car.app.get_connection')
    @patch('car.delete_data_car.app.handle_response_success')
    @patch('car.delete_data_car.app.handle_response')
    def test_delete_car_valid_status(self, mock_handle_response, mock_handle_response_success, mock_get_connection):
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {'id_status': 1}

        delete_car(1, 1)
        mock_cursor.execute.assert_any_call("SELECT * FROM status WHERE id_status=%s AND name='to_auto'", (1,))
        mock_cursor.execute.assert_any_call("UPDATE auto SET id_status=%s WHERE id_auto=%s", (1, 1))
        mock_connection.commit.assert_called_once()
        mock_handle_response_success.assert_called_with(200, 'Auto actualizado correctamente.', None)

    @patch('car.delete_data_car.app.get_connection')
    @patch('car.delete_data_car.app.handle_response')
    def test_delete_car_invalid_status(self, mock_handle_response, mock_get_connection):
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = None

        delete_car(1, 1)
        mock_cursor.execute.assert_called_with("SELECT * FROM status WHERE id_status=%s AND name='to_auto'", (1,))
        mock_handle_response.assert_called_with(None, 'El status no es válido para autos.', 400)

    @patch('car.delete_data_car.app.get_jwt_claims')
    @patch('car.delete_data_car.app.handle_response')
    def test_lambda_handler_exception(self, mock_handle_response, mock_get_jwt_claims):
        exception = Exception('Error de prueba')
        mock_get_jwt_claims.side_effect = exception

        event = {
            'headers': {
                'Authorization': 'token_de_prueba'
            }
        }

        lambda_handler(event, {})

        mock_handle_response.assert_called_once_with(exception, 'Error al decodificar token.', 401)

    @patch('json.loads')
    @patch('car.delete_data_car.app.get_jwt_claims')
    @patch('car.delete_data_car.app.handle_response')
    def test_lambda_handler_json_exception(self, mock_handle_response, mock_get_jwt_claims, mock_json_loads):
        mock_json_loads.side_effect = JSONDecodeError('Expecting value', 'doc', 0)

        event = {
            'headers': {
                'Authorization': 'token_de_prueba'
            },
            'body': 'invalid_json'
        }

        lambda_handler(event, {})

        args, _ = mock_handle_response.call_args

        self.assertIsInstance(args[0], JSONDecodeError)
        self.assertEqual(args[1], 'Parametros inválidos')
        self.assertEqual(args[2], 400)

    # test cases for connection.py
    @patch('car.delete_data_car.connection.boto3.session.Session.client')
    def test_get_secret(self, mock_boto_client):
        mock_client = mock_boto_client.return_value
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'HOST': 'test_host',
                'USERNAME': 'test_user',
                'PASSWORD': 'test_password',
                'DB_NAME': 'test_db'
            })
        }

        secret = get_secret()
        self.assertEqual(secret['HOST'], 'test_host')
        self.assertEqual(secret['USERNAME'], 'test_user')
        self.assertEqual(secret['PASSWORD'], 'test_password')
        self.assertEqual(secret['DB_NAME'], 'test_db')

    @patch('car.delete_data_car.connection.pymysql.connect')
    @patch('car.delete_data_car.connection.get_secret')
    def test_get_connection(self, mock_get_secret, mock_pymysql_connect):
        mock_get_secret.return_value = {
            'HOST': 'test_host',
            'USERNAME': 'test_user',
            'PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }

        mock_connection = mock_pymysql_connect.return_value

        connection = get_connection()
        mock_pymysql_connect.assert_called_once_with(
            host='test_host',
            user='test_user',
            password='test_password',
            database='test_db'
        )
        self.assertEqual(connection, mock_connection)

    def test_handle_response(self):
        response = handle_response('TestError', 'TestMessage', 400)
        expected_response = {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 400,
                'message': 'TestMessage',
                'error': 'TestError'
            })
        }
        self.assertEqual(response, expected_response)

    def test_handle_response_success(self):
        response = handle_response_success(200, 'TestMessage', {'key': 'value'})
        expected_response = {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 200,
                'message': 'TestMessage',
                'data': {'key': 'value'}
            })
        }
        self.assertEqual(response, expected_response)

    def test_get_jwt_claims(self):
        token = 'header.' + base64.b64encode(json.dumps({'user': 'test_user'}).encode()).decode().rstrip(
            '=') + '.signature'
        claims = get_jwt_claims(token)
        self.assertEqual(claims['user'], 'test_user')

    @patch('car.delete_data_car.connection.pymysql.connect')
    @patch('car.delete_data_car.connection.get_secret')
    def test_get_connection_exception(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'test_host',
            'USERNAME': 'test_user',
            'PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }
        mock_connect.side_effect = pymysql.MySQLError("Connection error")

        with self.assertRaises(pymysql.MySQLError):
            get_connection()

    @patch('car.delete_data_car.connection.boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )

        with self.assertRaises(ClientError):
            get_secret()

    def test_get_jwt_claims_value_error(self):
        invalid_token = "invalid.token.part.trge"

        with self.assertRaises(ValueError) as context:
            get_jwt_claims(invalid_token)

        self.assertEqual(str(context.exception), "Token inválido")

