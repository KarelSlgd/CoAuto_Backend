import unittest
from unittest.mock import patch
import json
import pymysql
from car.get_one_car.app import lambda_handler
from car.get_one_car.connection import get_connection, handle_response, get_secret, handle_response_success, headers_cors
from botocore.exceptions import ClientError


class TestGetOneCar(unittest.TestCase):
    @patch('car.get_one_car.app.get_connection')
    @patch('car.get_one_car.app.handle_response')
    @patch('car.get_one_car.app.handle_response_success')
    def test_lambda_handler_missing_id_auto(self, mock_handle_response_success, mock_handle_response, mock_get_connection):
        event = {
            'queryStringParameters': None,
            'body': json.dumps({})
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'Falta un parametro.', 400)

    @patch('car.get_one_car.app.get_connection')
    @patch('car.get_one_car.app.handle_response')
    @patch('car.get_one_car.app.handle_response_success')
    def test_lambda_handler_valid_id_auto(self, mock_handle_response_success, mock_handle_response, mock_get_connection):
        event = {
            'queryStringParameters': {'id_auto': '1'},
            'body': None
        }
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.execute.side_effect = [
            None,  # para la consulta de autos
            None,  # para la consulta de imagenes
            None  # para la consulta de calificaciones
        ]
        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model X', 'Brand Y', 2020, 50000, 'Sedan', 'Gasoline', 4, 'V8', 150, 200, 450, 'A great car',
                 'Available')
            ],  # resultado para la consulta de autos
            [
                ('http://example.com/image1.jpg',)
            ],  # resultado para la consulta de imagenes
            [
                (4,), (5,)
            ]  # resultado para la consulta de calificaciones
        ]

        lambda_handler(event, context)

        expected_response_data = [
            {
                'id_auto': 1,
                'model': 'Model X',
                'brand': 'Brand Y',
                'year': 2020,
                'price': '$50,000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': 4,
                'engine': 'V8',
                'height': 150,
                'width': 200,
                'length': 450,
                'description': 'A great car',
                'status': 'Available',
                'images': ['http://example.com/image1.jpg'],
                'average_rating': 4.5
            }
        ]

        mock_handle_response_success.assert_called_with(200, 'Informacion del auto obtenida correctamente.',
                                                        expected_response_data)

    @patch('car.get_one_car.app.get_connection')
    @patch('car.get_one_car.app.handle_response')
    def test_lambda_handler_query_exception(self, mock_handle_response, mock_get_connection):
        event = {
            'queryStringParameters': {'id_auto': '1'},
            'body': None
        }
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.execute.side_effect = Exception('Query failed')

        lambda_handler(event, context)

        args, kwargs = mock_handle_response.call_args
        exception_instance = args[0]
        self.assertIsInstance(exception_instance, Exception)
        self.assertEqual(str(exception_instance), 'Query failed')
        self.assertEqual(args[1], 'Ocurrió un error al obtener la información del auto.')
        self.assertEqual(args[2], 500)

    @patch('car.get_one_car.app.get_connection')
    def test_lambda_handler_no_results(self, mock_get_connection):
        event = {
            'queryStringParameters': {'id_auto': '1'},
            'body': None
        }
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.execute.side_effect = [
            None,  # For the first query
            None,  # For the images query
            None  # For the rate query
        ]
        mock_cursor.fetchall.side_effect = [
            [],  # No results for the first query
            [],  # No images
            []  # No ratings
        ]

        response = lambda_handler(event, context)

        expected_response_data = []

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Informacion del auto obtenida correctamente.', response['body'])
        self.assertEqual(json.loads(response['body'])['data'], expected_response_data)

    # Test for connection.py

    @patch('car.get_one_car.connection.boto3.session.Session.client')
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

    @patch('car.get_one_car.connection.pymysql.connect')
    @patch('car.get_one_car.connection.get_secret')
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

    @patch('car.get_one_car.connection.pymysql.connect')
    @patch('car.get_one_car.connection.get_secret')
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

    @patch('car.get_one_car.connection.boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )

        with self.assertRaises(ClientError):
            get_secret()
