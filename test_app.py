import unittest

from app import app


class SaveChildrensLivesAppTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'demo-token'

    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Together We Can Save More Children', response.get_data(as_text=True))

    def test_login_demo_user_and_dashboard(self):
        response = self.client.post(
            '/login',
            data={
                'email': 'patient@demo.local',
                'password': 'Patient@123',
                'role': 'Patient',
                'csrf_token': 'demo-token'
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Patient', response.get_data(as_text=True))

    def test_find_children_page(self):
        response = self.client.get('/find-children')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Search Children', response.get_data(as_text=True))

    def test_campaign_detail_page(self):
        response = self.client.get('/campaign/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hope Assistant', response.get_data(as_text=True))

    def test_ai_verification_page_for_patient(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['role'] = 'Patient'
        response = self.client.get('/ai-verification')
        self.assertEqual(response.status_code, 200)
        self.assertIn('AI Preliminary Verification', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
