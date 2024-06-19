import unittest
from unittest.mock import patch, MagicMock
import json

from user.get_data_user import app


class TestLambdaHandler(unittest.TestCase):
    @patch.dict("os.environ", {"RDS_HOST": "local", "DB_USERNAME": "root", "DB_PASSWORD": "superroot", "DB_NAME": "coauto"})
    @patch('pymysql.connect')
    def test_lambda_handler_success(self, mock_connect):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            (1, 'test@example.com', 'Test User', 'image_url', 'Admin', 'Active')
        ]

        response = app.lambda_handler({}, {})

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'get users')
        self.assertEqual(body['data'], [{
            'id_user': 1,
            'email': 'test@example.com',
            'nameUser': 'Test User',
            'profile_image': 'image_url',
            'nameRole': 'Admin',
            'status': 'Active'
        }])

        mock_connection.close.assert_called_once()

    @patch.dict("os.environ", {"RDS_HOST": "local", "DB_USERNAME": "root", "DB_PASSWORD": "superroot", "DB_NAME": "coauto"})
    @patch('pymysql.connect')
    def test_lambda_handler_exception(self, mock_connect):
        mock_connect.side_effect = Exception('Database connection error')

        response = app.lambda_handler({}, {})

        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'An error occurred: Database connection error')
