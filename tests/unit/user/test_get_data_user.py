from user.get_data_user import app
import unittest
from unittest.mock import patch, MagicMock
import json

from botocore.exceptions import ClientError

from user.get_data_user.connection import get_connection, get_secret, handle_response
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


class TestGetUser(unittest.TestCase):

    @patch('user.get_data_user.app.get_connection')
    @patch('user.get_data_user.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_get_connection):
        # Mockear la conexión y los resultados de la consulta
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simular resultados de la consulta
        mock_cursor.fetchall.return_value = [
            (1, 'cognito_1', 'email1@example.com', 'John', 'Doe', 'Admin', 'Active', 'image1.jpg'),
            (2, 'cognito_2', 'email2@example.com', 'Jane', 'Smith', 'User', 'Inactive', 'image2.jpg')
        ]

        # Ejecutar la función
        response = app.lambda_handler({}, {})

        # Verificar el código de estado y la estructura de la respuesta
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['statusCode'], 200)
        self.assertEqual(body['message'], 'Usuarios obtenidos correctamente')
        self.assertEqual(len(body['data']), 2)
        self.assertEqual(body['data'][0]['name'], 'John')

    @patch('user.get_data_user.app.get_connection')
    @patch('user.get_data_user.app.handle_response')
    def test_lambda_handler_query_failure(self, mock_handle_response, mock_get_connection):
        # Mockear la conexión y forzar una excepción
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception('Database error')

        # Simular respuesta de handle_response
        mock_handle_response.return_value = {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error al obtener usuarios"
            }),
        }

        # Ejecutar la función
        response = app.lambda_handler({}, {})

        # Verificar el código de estado y la estructura de la respuesta
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Error al obtener usuarios')


    @patch('user.get_data_user.connection.boto3.session.Session')
    def test_get_secret(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'HOST': 'localhost',
                'USERNAME': 'user',
                'PASSWORD': 'pass',
                'DB_NAME': 'database'
            })
        }

        secret = get_secret()

        self.assertEqual(secret['HOST'], 'localhost')
        self.assertEqual(secret['USERNAME'], 'user')
        self.assertEqual(secret['PASSWORD'], 'pass')
        self.assertEqual(secret['DB_NAME'], 'database')
        mock_client.get_secret_value.assert_called_with(SecretId='COAUTO')

    @patch('user.get_data_user.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('user.get_data_user.connection.pymysql.connect')
    @patch('user.get_data_user.connection.get_secret')
    def test_get_connection(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }
        connection = MagicMock()
        mock_connect.return_value = connection

        result = get_connection()

        self.assertEqual(result, connection)
        mock_connect.assert_called_with(
            host='localhost',
            user='user',
            password='pass',
            database='database'
        )

    @patch('user.get_data_user.connection.pymysql.connect')
    @patch('user.get_data_user.connection.get_secret')
    def test_get_connection_error(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }
        mock_connect.side_effect = Exception('Connection error')

        with self.assertRaises(Exception) as context:
            get_connection()

        self.assertTrue('Connection error' in str(context.exception))

    def test_handle_response(self):
        error = Exception('Test Error')
        message = 'Test Message'
        status_code = 400

        response = handle_response(error, message, status_code)

        expected_response = {
            'statusCode': status_code,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': status_code,
                'message': message,
                'error': str(error)
            })
        }

        self.assertEqual(response, expected_response)
