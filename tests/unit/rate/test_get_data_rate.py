import os
from unittest.mock import patch, MagicMock
from rate.get_data_rate import app
import unittest
import json


class TestRate(unittest.TestCase):

    @patch('rate.get_data_rate.app.execute_query')
    @patch('rate.get_data_rate.app.connect_to_db')
    @patch('rate.get_data_rate.app.close_connection')
    def test_lambda_handler(self, mock_close_connection, mock_connect_to_db, mock_execute_query):
        mock_connection = MagicMock()
        mock_connect_to_db.return_value = mock_connection

        mock_execute_query.return_value = [
            (1, 5, 'Great car!', 'Model S', 'Tesla', 'John', 'Doe'),
            (2, 5, 'Great car!', 'Model S', 'Tesla', 'John', 'Doe')
        ]

        result = app.lambda_handler(None, None)
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn("data", body)
        self.assertTrue(body["data"])
        self.assertEqual(body['message'], 'get rate')
        mock_close_connection.assert_called_once()

    @patch("rate.get_one_data_rate.app.execute_query")
    @patch("rate.get_one_data_rate.app.connect_to_db")
    def test_lambda_handler_missing_data(self, mock_connect_to_db, mock_execute_query):
        mock_connection = MagicMock()
        mock_connect_to_db.return_value = mock_connection
        mock_execute_query.side_effect = Exception('Query execution failed.')

        response = app.lambda_handler(None, None)
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('No data found.', body['message'])

    #No jala
    @patch("rate.get_one_data_rate.app.connect_to_db")
    @patch("rate.get_one_data_rate.app.execute_query")
    @patch("rate.get_one_data_rate.app.close_connection")
    def test_lambda_handler_internal_error(self, mock_connect_to_db, mock_close_connection, mock_execute_query):
        mock_connect_to_db.return_value = 'mock_connection'
        mock_execute_query.return_value = [{'id_rate': 1, 'value': 10, 'comment': 'Good', 'model': 'Sedan', 'brand': 'Toyota', 'name': 'John', 'lastname': 'Doe'}]
        mock_close_connection.side_effect = Exception('Failed to close connection')

        response = app.lambda_handler(None, None)
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('An error occurred while executing the query' in body['message'])
        mock_close_connection.assert_called_once()
