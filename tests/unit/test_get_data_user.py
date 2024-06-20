import unittest
import json

from unittest.mock import patch, MagicMock
from user.get_data_user.connection import get_connection
from user.get_data_user import app


class TestDatabaseConnection(unittest.TestCase):

    @patch('user.get_data_user.connection.get_secret')
    @patch('pymysql.connect')
    def test_get_connection_success(self, mock_connect, mock_get_secret):
        mock_get_secret.return_value = {
            'host': 'localhost',
            'username': 'test_user',
            'password': 'test_pass',
            'dbname': 'test_db'
        }

        mock_connect.return_value = MagicMock()

        connection = get_connection()
        self.assertIsNotNone(connection)
        mock_get_secret.assert_called_once_with()
        mock_connect.assert_called_once_with(
            host='localhost',
            user='test_user',
            password='test_pass',
            database='test_db'
        )

    @patch('user.get_data_user.connection.get_secret')
    def test_get_connection_failure(self, mock_get_secret):
        mock_get_secret.return_value = {
            'host': 'localhost',
            'username': 'test_user',
            'password': 'test_pass',
            'dbname': 'test_db'
        }

        with patch('user.get_data_user.connection.get_connection', side_effect=Exception('Connection error')):
            response = get_connection()
            self.assertEqual(response['statusCode'], 500)
            self.assertIn('Failed to connect to database', response['body'])

    @patch('user.get_data_user.app.get_connection')
    def test_lambda_handler_success(self, mock_get_connection):
        # Mocking the database connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        sample_data = [
            {
                'id_user': 1,
                'id_cognito': 'cognito123',
                'email': 'test@example.com',
                'nameUser': 'John',
                'lastname': 'Doe',
                'nameRole': 'Admin',
                'value': 'Active'
            },
        ]
        mock_cursor.fetchall.return_value = sample_data

        expected_users = [
            {
                'idUser': 1,
                'idCognito': 'cognito123',
                'email': 'test@example.com',
                'name': 'John',
                'lastname': 'Doe',
                'role': 'Admin',
                'status': 'Active'
            },
        ]

        event = {}
        context = {}

        response = app.lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'get users')
        self.assertEqual(body['data'], expected_users)

    @patch('user.get_data_user.app.get_connection')
    def test_lambda_handler_failure(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.side_effect = Exception('Database error')

        event = {}
        context = {}

        response = app.lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('An error occurred: Database error', body['message'])

        mock_connection.close.assert_called_once()