import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeUserQuery:
    def __init__(self, database):
        self.database = database
        self.user_id = None
        self.updates = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, field, value):
        if field == 'id':
            self.user_id = value
        return self

    def update(self, values):
        self.updates = values
        return self

    def execute(self):
        user = self.database.users.get(self.user_id)
        if user is None:
            return FakeResponse([])
        if self.updates:
            user.update(self.updates)
        return FakeResponse([dict(user)])


class FakeSupabase:
    def __init__(self, users):
        self.users = users

    def table(self, table_name):
        if table_name != 'users':
            raise AssertionError(f'Unexpected table: {table_name}')
        return FakeUserQuery(self)


class AdminUserManagementActionTests(unittest.TestCase):
    def setUp(self):
        main.app.config.update(TESTING=True, SECRET_KEY='test-admin-actions')
        self.client = main.app.test_client()
        self.users = {
            'admin-1': {
                'id': 'admin-1', 'email': 'admin@example.com', 'role': 'admin',
                'status': 'Approved', 'first_name': 'System', 'last_name': 'Admin',
            },
            'user-1': {
                'id': 'user-1', 'email': 'farmer@example.com', 'role': 'farmer',
                'status': 'Approved', 'first_name': 'Mina', 'last_name': 'Santos',
            },
        }
        self.database = FakeSupabase(self.users)
        self.supabase_patch = patch.object(main, 'supabase', self.database)
        self.supabase_patch.start()
        self.addCleanup(self.supabase_patch.stop)
        with self.client.session_transaction() as session:
            session['user_id'] = 'admin-1'
            session['user_email'] = 'admin@example.com'
            session['user_role'] = 'admin'
            session['user_name'] = 'System Admin'

    @patch('main.security_service.log_audit')
    def test_admin_can_change_user_role_and_audit_it(self, mock_audit):
        response = self.client.post('/admin/update-user-role', json={
            'user_id': 'user-1', 'role': 'lgu',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.users['user-1']['role'], 'lgu')
        self.assertEqual(response.get_json()['role'], 'lgu')
        self.assertEqual(mock_audit.call_args.args[2], 'USER_ROLE_UPDATED')

    def test_invalid_role_change_returns_validation_error(self):
        response = self.client.post('/admin/update-user-role', json={
            'user_id': 'user-1', 'role': 'admin',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('valid user role', response.get_json()['message'])

    @patch('main.security_service.log_audit')
    @patch('main.send_status_email', return_value=True)
    def test_revoke_updates_status_and_records_audit(self, mock_email, mock_audit):
        mock_email.side_effect = lambda *_args: self.assertEqual(self.users['user-1']['status'], 'Revoked') or True
        response = self.client.post('/admin/update-user-status', json={
            'user_id': 'user-1', 'action': 'revoke',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.users['user-1']['status'], 'Revoked')
        self.assertEqual(mock_audit.call_args.args[2], 'ACCESS_REVOKED')

    @patch('main.send_status_email', return_value=True)
    def test_restore_updates_revoked_user_to_approved(self, mock_email):
        self.users['user-1']['status'] = 'Revoked'
        response = self.client.post('/admin/update-user-status', json={
            'user_id': 'user-1', 'action': 'restore',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.users['user-1']['status'], 'Approved')
        self.assertEqual(response.get_json()['target_status'], 'Approved')
        mock_email.assert_called_once_with('farmer@example.com', 'Mina Santos', 'Approved')

    @patch('main.security_service.log_audit')
    def test_revoked_user_active_session_is_denied(self, _mock_audit):
        self.users['user-1']['status'] = 'Revoked'
        with self.client.session_transaction() as session:
            session['user_id'] = 'user-1'
            session['user_email'] = 'farmer@example.com'
            session['user_role'] = 'farmer'

        response = self.client.get('/farmer/dashboard')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

    def test_role_change_refreshes_existing_session_permissions(self):
        self.users['user-1']['role'] = 'lgu'
        with self.client.session_transaction() as session:
            session['user_id'] = 'user-1'
            session['user_email'] = 'farmer@example.com'
            session['user_role'] = 'farmer'

        response = self.client.get('/farmer/dashboard')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/lgu/dashboard', response.location)


if __name__ == '__main__':
    unittest.main()