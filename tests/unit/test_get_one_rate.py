from unittest.mock import patch, MagicMock
from rate.get_one_data_rate import app
import unittest
import json


class TestRate(unittest.TestCase):

    @patch("rate.get_one_data_rate.app.execute_query")
    @patch("rate.get_one_data_rate.app.connect_to_db")
    @patch("rate.get_one_data_rate.app.close_connection")
    def test_lambda_handler_data(self, mock_close_connection, mock_connect_to_db, mock_execute_query):
        mock_connection = MagicMock()
        mock_connect_to_db.return_value = mock_connection

        mock_execute_query.return_value = [
            (2, 2, "Es el mejor!", "Hola", "Hola", "Victor", "flores")
        ]

        mock_body = {
            "body": json.dumps({
                "id_auto": 2
            })
        }

        result = app.lambda_handler(mock_body, None)
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn("data", body)
        self.assertTrue(body["data"])
        mock_close_connection.assert_called_once()

    @patch("rate.get_one_data_rate.app.connect_to_db")
    def test_lambda_handler_missing_id_rate(self, mock_connect_to_db,):
        mock_connection = MagicMock()
        mock_connect_to_db.return_value = mock_connection
        mock_body = {
            "body": json.dumps({
                "id": 2
            })
        }
        result = app.lambda_handler(mock_body, None)
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertIn('Missing id_auto parameter.', body['message'])

    @patch("rate.get_one_data_rate.app.execute_query")
    @patch("rate.get_one_data_rate.app.connect_to_db")
    @patch("rate.get_one_data_rate.app.close_connection")
    def test_lambda_handler_internal_error(self, mock_connect_to_db, mock_close_connection, mock_execute_query):
        mock_connection = MagicMock()
        mock_connect_to_db.return_value = mock_connection
        mock_execute_query.side_effect = Exception('Query execution failed.')

        mock_body = {
            "body": json.dumps({
                "id_auto": 2
            })
        }

        response = app.lambda_handler(mock_body, None)
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('An error occurred', body['message'])
        self.assertIn("Query execution failed.", body['message'])
        mock_close_connection.assert_called_once()

