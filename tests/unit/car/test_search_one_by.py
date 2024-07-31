import unittest
from unittest.mock import patch
import json
import pymysql
from car.search_one_by.app import handle_response, lambda_handler
from botocore.exceptions import ClientError
from car.search_one_by.connection import headers_cors, get_secret, get_connection, handle_response_success


class TestSearchOneBy(unittest.TestCase):
    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.handle_response_success')
    def test_lambda_handler_missing_parameters(self, mock_handle_response_success, mock_handle_response, mock_get_connection):
        event = {
            'queryStringParameters': None,
            'body': json.dumps({})
        }

        expected_response = {
            'statusCode': 400,
            'body': json.dumps({'message': 'Faltan parámetros.'})
        }

        mock_handle_response.return_value = expected_response

        response = lambda_handler(event, None)

        self.assertEqual(response, expected_response)
        mock_handle_response.assert_called_once_with(None, 'Faltan parámetros.', 400)

    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.handle_response_success')
    def test_lambda_handler_invalid_attribute_type(self, mock_handle_response_success, mock_handle_response, mock_get_connection):
        event = {
            'queryStringParameters': {
                'type': 'invalid_type',
                'value': 'some_value'
            }
        }

        expected_response = {
            'statusCode': 400,
            'body': json.dumps({'message': 'Tipo de atributo no válido.'})
        }

        mock_handle_response.return_value = expected_response

        response = lambda_handler(event, None)

        self.assertEqual(response, expected_response)
        mock_handle_response.assert_called_once_with(None, 'Tipo de atributo no válido.', 400)

    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.handle_response_success')
    def test_lambda_handler_successful_query(self, mock_handle_response_success, mock_handle_response, mock_get_connection):
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model X', 'Brand Y', 2020, 15000, 'SUV', 'Gasoline', 4, 'V8', 1.5, 2.0, 3.0, 'A nice car', 'Available')
            ],
            [
                ('http://example.com/image1.jpg',),
                ('http://example.com/image2.jpg',)
            ]
        ]

        event = {
            'queryStringParameters': {
                'type': 'marca',
                'value': 'Brand Y'
            }
        }

        expected_response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Consulta exitosa.',
                'data': [
                    {
                        'id_auto': 1,
                        'model': 'Model X',
                        'brand': 'Brand Y',
                        'year': 2020,
                        'price': 15000,
                        'type': 'SUV',
                        'fuel': 'Gasoline',
                        'doors': 4,
                        'engine': 'V8',
                        'height': 1.5,
                        'width': 2.0,
                        'length': 3.0,
                        'description': 'A nice car',
                        'status': 'Available',
                        'images': ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']
                    }
                ]
            })
        }

        mock_handle_response_success.return_value = expected_response

        response = lambda_handler(event, None)

        self.assertEqual(response, expected_response)
        mock_handle_response_success.assert_called_once_with(200, 'Consulta exitosa.', json.loads(expected_response['body'])['data'])

    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.handle_response_success')
    def test_lambda_handler_database_error(self, mock_handle_response_success, mock_handle_response,
                                           mock_get_connection):
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.execute.side_effect = Exception("Database error")

        event = {
            'queryStringParameters': {
                'type': 'marca',
                'value': 'Brand Y'
            }
        }

        expected_response = {
            'statusCode': 500,
            'body': json.dumps({'message': 'Ocurrió un error al obtener la información del auto.'})
        }

        mock_handle_response.return_value = expected_response

        response = lambda_handler(event, None)

        self.assertEqual(response, expected_response)
        mock_handle_response.assert_called_once()
        called_args, called_kwargs = mock_handle_response.call_args
        self.assertIsInstance(called_args[0], Exception)
        self.assertEqual(called_args[1], 'Ocurrió un error al obtener la información del auto.')
        self.assertEqual(called_args[2], 500)

    # Test for connection.py

    @patch('car.search_one_by.connection.boto3.session.Session.client')
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

    @patch('car.search_one_by.connection.pymysql.connect')
    @patch('car.search_one_by.connection.get_secret')
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

    @patch('car.search_one_by.connection.pymysql.connect')
    @patch('car.search_one_by.connection.get_secret')
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

    @patch('car.search_one_by.connection.boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )

        with self.assertRaises(ClientError):
            get_secret()
