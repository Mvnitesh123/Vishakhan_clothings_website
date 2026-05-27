import json
from django.test import TestCase, Client
from django.urls import reverse

class RateLimitAndValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product_url = reverse('sample-products')
        self.signup_url = reverse('sample-signup')

    def test_product_validation_success(self):
        """Test successful GET request with valid parameters."""
        response = self.client.get(self.product_url, {'category': 'shirts', 'min_price': '10', 'sort_by': 'price_asc'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

    def test_product_validation_failure(self):
        """Test GET request with invalid parameters."""
        # min_price must be >= 0, sort_by must match pattern
        response = self.client.get(self.product_url, {'min_price': '-5', 'sort_by': 'invalid_sort'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid query parameters')

    def test_signup_validation_success(self):
        """Test successful POST request with valid JSON body."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePassword123'
        }
        response = self.client.post(self.signup_url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_signup_validation_failure_missing_fields(self):
        """Test POST request with missing fields."""
        payload = {
            'username': 'testuser'
        }
        response = self.client.post(self.signup_url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('email', str(data['details']))
        self.assertIn('password', str(data['details']))

    def test_signup_validation_failure_bad_password(self):
        """Test POST request with invalid password (no digit)."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'NoDigitPassword'
        }
        response = self.client.post(self.signup_url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('password', str(data['details']))

    def test_malformed_json(self):
        """Test sending malformed JSON payload."""
        response = self.client.post(self.signup_url, data="{'invalid': json", content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Malformed JSON payload.')

    def test_rate_limiting(self):
        """Test that rate limiting triggers after limits are exceeded."""
        # login_rate_limit is 5/m. Let's send 6 requests.
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePassword123'
        }
        
        # Send 5 valid requests
        for _ in range(5):
            response = self.client.post(self.signup_url, data=json.dumps(payload), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            
        # The 6th request should be rate limited (429)
        response = self.client.post(self.signup_url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Too Many Requests')
        self.assertIn('Retry-After', response.headers)
