import unittest
from unittest.mock import patch
import json
import pymysql
from car.get_one_data_car.app import lambda_handler
from car.get_one_data_car.connection import get_connection, get_secret, handle_response, headers_cors, handle_response_success
from botocore.exceptions import ClientError
mock_body = {
    'body': json.dumps({'id_auto': 1})
}

mock_body_no_id = {
    'body': json.dumps({'id_auto': None})
}

mock_query_string_params = {
    'queryStringParameters': {'id_auto': '1'}
}

mock_query_string_params_no_id = {
    'queryStringParameters': None
}


class TestGetOneCar(unittest.TestCase):
    @patch('car.get_one_data_car.app.get_connection')
    @patch('car.get_one_data_car.app.handle_response')
    @patch('car.get_one_data_car.app.handle_response_success')
    def test_lambda_handler_no_id_auto(self, mock_handle_response_success, mock_handle_response, mock_get_connection):
        event = mock_body_no_id
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(None, 'Falta un parametro.', 400)

    @patch('car.get_one_data_car.app.get_connection')
    @patch('car.get_one_data_car.app.handle_response')
    @patch('car.get_one_data_car.app.handle_response_success')
    def test_lambda_handler_with_id_auto(self, mock_handle_response_success, mock_handle_response, mock_get_connection):
        event = mock_query_string_params
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model X', 'Brand Y', 2020, 50000, 'SUV', 'Gasoline', 4, 'V6', 1.5, 2.0, 4.5, 'Good car',
                 'Available')
            ],
            [
                ('http://image1.com',), ('http://image2.com',)
            ]
        ]

        lambda_handler(event, context)

        expected_car = {
            'id_auto': 1,
            'model': 'Model X',
            'brand': 'Brand Y',
            'year': 2020,
            'price': 50000,
            'type': 'SUV',
            'fuel': 'Gasoline',
            'doors': 4,
            'engine': 'V6',
            'height': 1.5,
            'width': 2.0,
            'length': 4.5,
            'description': 'Good car',
            'status': 'Available',
            'images': ['http://image1.com', 'http://image2.com']
        }

        mock_handle_response_success.assert_called_once_with(200, 'Informacion del auto obtenida correctamente.',
                                                             [expected_car])

    @patch('car.get_one_data_car.app.get_connection')
    @patch('car.get_one_data_car.app.handle_response')
    @patch('car.get_one_data_car.app.handle_response_success')
    def test_lambda_handler_exception(self, mock_handle_response_success, mock_handle_response, mock_get_connection):
        event = mock_query_string_params
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.execute.side_effect = Exception('DB Error')

        lambda_handler(event, context)

        mock_handle_response.assert_called_once()
        args, kwargs = mock_handle_response.call_args
        self.assertEqual(args[1], 'Ocurrió un error al obtener la información del auto.')
        self.assertEqual(args[2], 500)

    # Test for connection.py

    @patch('car.get_one_data_car.connection.boto3.session.Session.client')
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

    @patch('car.get_one_data_car.connection.pymysql.connect')
    @patch('car.get_one_data_car.connection.get_secret')
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

    @patch('car.get_one_data_car.connection.pymysql.connect')
    @patch('car.get_one_data_car.connection.get_secret')
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

    @patch('car.get_one_data_car.connection.boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )

        with self.assertRaises(ClientError):
            get_secret()
