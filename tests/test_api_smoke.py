import unittest
from app import app


class TestApiSmoke(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_health_check(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("status", data)

    def test_swagger_ui_endpoint(self):
        response = self.client.get("/docs/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"swagger", response.data.lower())

    def test_swagger_json_spec(self):
        response = self.client.get("/swagger.json")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("openapi"), "3.0.3")
        self.assertIn("paths", data)

    def test_swagger_redirect(self):
        response = self.client.get("/swagger")
        self.assertEqual(response.status_code, 302)

    def test_404_error_handler(self):
        response = self.client.get("/api/invalid-route-smoke-test")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("message", data)

    def test_login_validation_error(self):
        response = self.client.post("/api/auth/login", json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data.get("success"))


if __name__ == "__main__":
    unittest.main()
