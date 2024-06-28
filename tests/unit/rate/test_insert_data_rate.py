from unittest.mock import patch, MagicMock
from rate.insert_data_rate import app
import unittest
import json


class TestRate(unittest.TestCase):
    @patch('rate.insert_data_rate.app.execute_query')
    @patch('rate.insert_data_rate.app.connect_to_db')
    @patch('rate.insert_data_rate.app.close_connection')
    def test_lambda_handler(self, mock_close_connection, mock_connect_to_db, mock_execute_query):
        mock_connection = MagicMock()
        mock_connect_to_db.return_value = mock_connection

        mock_execute_query.return_value = [
            {'value': '5','comment': 'Great car!','id_auto': '1','id_user': '1'}
        ]

        result = app.lambda_handler(None, None)
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn("data", body)
        self.assertTrue(body["data"])
        self.assertEqual(body['message'], 'get rate')
        mock_close_connection.assert_called_once()

    @patch('rate.get_data_rate.app.execute_query')
    @patch('rate.get_data_rate.app.connect_to_db')
    def test_lambda_handler_invalite_body(self, mock_connect_to_db, mock_execute_query):
        mock_connection = MagicMock()
        mock_connect_to_db.return_value = mock_connection

        mock_execute_query.return_value = [
            (5, 'Great car!', 1, 1)
        ]

        result = app.lambda_handler(None, None)
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertEqual(body['message'], 'Invalid request body.')

    @patch('rate.get_data_rate.app.execute_query')
    @patch('rate.get_data_rate.app.connect_to_db')
    @patch('rate.get_data_rate.app.close_connection')
    def test_lambda_handler_erro_500(self, mock_close_connection, mock_connect_to_db, mock_execute_query):
        mock_connection = MagicMock()
        mock_connect_to_db.return_value = mock_connection

        mock_execute_query.return_value = {
            'body': json.dumps({
                'value': '5',
                'comment': 'Great car!',
                'id_auto': '1',
                'id_user': '1'
            })
        }

        result = app.lambda_handler(None, None)
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertEqual(body['message'], 'An error occurred: string index out of range')
        mock_close_connection.assert_called_once()
