from unittest.mock import patch
from get_one_data_rate import app
import unittest
import json

mock_body = {
    "body": json.dumps({
        "id_auto": 2
    })
}

mock_path = {
    "pathParameters": {
        "id_auto": 2
    }
}


class TestRate(unittest.TestCase):
    @patch.dict("os.environ", {"REGION_NAME": "mexico", "DATA_BASE": "database", "SECRET_NAME": "secret"})
    @patch("get_one_data_rate.app.lambda_handler")
    def test_lambda_handler(self, mock_lambda_handler):
        mock_lambda_handler.return_value = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Rates retrieved successfully.',
                'data': [{"id_rate": 2, "value": 2, "comment": "Es el mejor!", "id_auto": 3, "id_user": 2}]
            })
        }
        result = app.lambda_handler(mock_body, None)
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn("data", body)
        self.assertTrue(body["data"])
        print(body["data"])

    @patch.dict("os.environ", {"REGION_NAME": "mexico", "DATA_BASE": "database", "SECRET_NAME": "secret"})
    @patch("get_one_data_rate.app.lambda_handler")
    def test_lambda_handler_missing_id_rate(self, mock_lambda_handler):
        mock_body_missing_id_auto = {
            "body": json.dumps({})
        }
        mock_lambda_handler.return_value = {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Missing id_auto parameter.'
            })
        }
        result = app.lambda_handler(mock_body_missing_id_auto, None)
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertIn('message', body)
        self.assertEqual(body['message'], 'Missing id_auto parameter.')
        print(body['message'])

    #Este aun no jala xd
    @patch.dict("os.environ", {"REGION_NAME": "mexico", "DATA_BASE": "database", "SECRET_NAME": "secret"})
    @patch("get_one_data_rate.app.lambda_handler")
    def test_lambda_handler_internal_error(self, mock_connect):
        mock_connect.side_effect = Exception('Query execution failed.')
        result = app.lambda_handler(mock_body, None)
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertIn("error", body)
        self.assertEqual(body["error"], "An error occurred while processing the request.")
