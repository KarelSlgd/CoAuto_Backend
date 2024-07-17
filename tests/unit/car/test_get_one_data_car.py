import unittest
from unittest.mock import patch, MagicMock
import json
from car.get_one_data_car.app import lambda_handler
from car.get_one_data_car.connection import get_connection, get_secret, handle_response, headers_cors, execute_query, close_connection
from botocore.exceptions import ClientError


class TestGetOneCar(unittest.TestCase):

    @patch('car.get_one_data_car.app.get_connection')
    @patch('car.get_one_data_car.app.close_connection')
    @patch('car.get_one_data_car.app.handle_response')
    def test_lambda_handler_successful(self, mock_handle_response, mock_close_connection, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model X', 'Brand Y', 2020, 50000, 'SUV', 'Gasoline', 4, 'V8', 150, 70, 180, 'Description of car', 'Available')
            ],
            [
                ('http://image.url/1.jpg',),
                ('http://image.url/2.jpg',)
            ]
        ]

        event = {
            'queryStringParameters': {
                'id_auto': '1'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Informacion del auto obtenida correctamente.',
                'data': [
                    {
                        'id_auto': 1,
                        'model': 'Model X',
                        'brand': 'Brand Y',
                        'year': 2020,
                        'price': 50000,
                        'type': 'SUV',
                        'fuel': 'Gasoline',
                        'doors': 4,
                        'engine': 'V8',
                        'height': 150,
                        'width': 70,
                        'length': 180,
                        'description': 'Description of car',
                        'status': 'Available',
                        'images': [
                            'http://image.url/1.jpg',
                            'http://image.url/2.jpg'
                        ]
                    }
                ]
            })
        }

        self.assertEqual(response, expected_response)

    @patch('car.get_one_data_car.app.get_connection')
    @patch('car.get_one_data_car.app.close_connection')
    @patch('car.get_one_data_car.app.handle_response')
    def test_lambda_handler_body_id_auto(self, mock_handle_response, mock_close_connection, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model X', 'Brand Y', 2020, 50000, 'SUV', 'Gasoline', 4, 'V8', 150, 70, 180, 'Description of car',
                 'Available')
            ],
            [
                ('http://image.url/1.jpg',),
                ('http://image.url/2.jpg',)
            ]
        ]

        event = {
            'body': json.dumps({'id_auto': '1'})
        }
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Informacion del auto obtenida correctamente.',
                'data': [
                    {
                        'id_auto': 1,
                        'model': 'Model X',
                        'brand': 'Brand Y',
                        'year': 2020,
                        'price': 50000,
                        'type': 'SUV',
                        'fuel': 'Gasoline',
                        'doors': 4,
                        'engine': 'V8',
                        'height': 150,
                        'width': 70,
                        'length': 180,
                        'description': 'Description of car',
                        'status': 'Available',
                        'images': [
                            'http://image.url/1.jpg',
                            'http://image.url/2.jpg'
                        ]
                    }
                ]
            })
        }

        self.assertEqual(response, expected_response)

    @patch('car.get_one_data_car.app.get_connection')
    @patch('car.get_one_data_car.app.close_connection')
    @patch('car.get_one_data_car.app.handle_response')
    def test_lambda_handler_missing_id_auto(self, mock_handle_response, mock_close_connection, mock_get_connection):
        event = {
            'queryStringParameters': {}
        }
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(None, 'Falta un parametro.', 400)

    @patch('car.get_one_data_car.app.get_connection')
    @patch('car.get_one_data_car.app.close_connection')
    @patch('car.get_one_data_car.app.handle_response')
    def test_lambda_handler_query_execution_error(self, mock_handle_response, mock_close_connection,
                                                  mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception('Query execution error')

        event = {
            'queryStringParameters': {
                'id_auto': '1'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(mock_cursor.execute.side_effect,
                                                     'Ocurrió un error al obtener la reseña.', 500)

    # Test for connection.py

    @patch('car.get_one_data_car.connection.boto3.session.Session')
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

    @patch('car.get_one_data_car.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.get_one_data_car.connection.pymysql.connect')
    @patch('car.get_one_data_car.connection.get_secret')
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

    @patch('car.get_one_data_car.connection.pymysql.connect')
    @patch('car.get_one_data_car.connection.get_secret')
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

    @patch('car.get_one_data_car.connection.execute_query')
    def test_execute_query_successful(self, mock_execute_query):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [('row1',), ('row2',)]

        query = "SELECT * FROM test_table"

        result = execute_query(mock_connection, query)

        mock_cursor.execute.assert_called_once_with(query)
        mock_cursor.fetchall.assert_called_once()
        self.assertEqual(result, [('row1',), ('row2',)])

    @patch('car.get_one_data_car.connection.execute_query')
    def test_execute_query_exception(self, mock_execute_query):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Query execution error")

        query = "SELECT * FROM test_table"

        result = execute_query(mock_connection, query)

        mock_cursor.execute.assert_called_once_with(query)
        self.assertIsNone(result)

    @patch('car.get_one_data_car.connection.close_connection')
    def test_close_connection_successful(self, mock_close_connection):
        mock_connection = MagicMock()

        close_connection(mock_connection)

        mock_connection.close.assert_called_once()

    @patch('car.get_one_data_car.connection.close_connection')
    def test_close_connection_none(self, mock_close_connection):
        close_connection(None)
        self.assertEqual(mock_close_connection.call_count, 0)