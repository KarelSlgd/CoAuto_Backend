import unittest
from unittest.mock import patch
import json
import pymysql
import base64
from car.insert_data_car.app import lambda_handler, insert_into_car
from car.insert_data_car.connection import get_connection, handle_response, headers_cors, get_secret, \
    handle_response_success, get_jwt_claims
from botocore.exceptions import ClientError


class TestInsertCar(unittest.TestCase):
    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    @patch('car.insert_data_car.app.insert_into_car')
    def test_lambda_handler_missing_token(self, mock_insert, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {}
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_once_with('Missing token.', 'Faltan parámetros.', 401)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    @patch('car.insert_data_car.app.insert_into_car')
    def test_lambda_handler_missing_parameters(self, mock_insert, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({})
        }
        context = {}

        mock_get_jwt_claims.return_value = {'cognito:groups': ['AdminGroup']}

        lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(None, 'Faltan parámetros.', 400)

    # Test for connection.py

    @patch('car.insert_data_car.connection.boto3.session.Session.client')
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

    @patch('car.insert_data_car.connection.pymysql.connect')
    @patch('car.insert_data_car.connection.get_secret')
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

    @patch('car.insert_data_car.connection.pymysql.connect')
    @patch('car.insert_data_car.connection.get_secret')
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

    @patch('car.insert_data_car.connection.boto3.session.Session.client')
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

    def test_valid_token(self):
        # creando un token válido
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
        signature = "b'123abc'"
        token = f"{base64.b64encode(json.dumps(header).encode()).decode()}.{base64.b64encode(json.dumps(payload).encode()).decode()}.{signature}"

        claims = get_jwt_claims(token)
        self.assertEqual(claims, payload)

    def test_invalid_token(self):
        # creando un token inválido
        token = "invalid.token"

        with self.assertRaises(ValueError) as context:
            get_jwt_claims(token)

        self.assertEqual(str(context.exception), "Token inválido")

    def test_non_string_token(self):
        # creando un token inválido
        token = 12345

        with self.assertRaises(AttributeError):
            get_jwt_claims(token)
