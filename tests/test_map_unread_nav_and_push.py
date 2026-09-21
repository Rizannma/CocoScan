import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app import push_service


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'test-user-123'
            sess['user_role'] = 'farmer'
            sess['user_email'] = 'farmer@test.com'
        yield client


def test_map_picker_default_san_pablo_no_marker():
    """Verify that farmer_scan.html defaults map view to San Pablo without pre-placing a marker."""
    with open('templates/farmer_scan.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Verify San Pablo center coordinates are present
    assert 'DEFAULT_SAN_PABLO_LAT' in content
    assert 'DEFAULT_SAN_PABLO_LNG' in content

    # Verify no marker is created when there is no preselected location
    assert 'hasPreselectedLoc' in content
    assert 'Tap on map to place pin' in content

    # Verify click handler creates marker interactively
    assert "uploadMapInstance.on('click'" in content
    assert 'createUploadMapPinIcon' in content


def test_unread_badge_logic_in_templates():
    """Verify that farmer_reports.html calculates unread status dynamically and marks as read upon open."""
    with open('templates/farmer_reports.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Ensure hardcoded status comparison is removed
    assert "item.status === 'Recommendation Issued'" not in content

    # Verify dynamic unread computation
    assert 'read_chats_' in content
    assert 'read_status_' in content
    assert 'unreadChatsCount' in content
    assert '/api/reports/' in content
    assert '/mark-read' in content


def test_report_mark_read_endpoint(client):
    """Verify that /api/reports/<id>/mark-read endpoint responds successfully."""
    response = client.post('/api/reports/999/mark-read', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['report_id'] == 999
    assert 'last_read_at' in data


def test_modal_z_index_and_bottom_nav_padding():
    """Verify that modal overlay is above bottom nav (z-index 100000 > 9999) and modal has bottom padding."""
    with open('templates/components/report_modal.html', 'r', encoding='utf-8') as f:
        modal_content = f.read()

    with open('templates/components/farmer_bottom_nav.html', 'r', encoding='utf-8') as f:
        nav_content = f.read()

    # Bottom nav has z-index 9999
    assert 'z-index: 9999;' in nav_content

    # Modal overlay has z-index 100000 (above nav)
    assert 'z-index: 100000;' in modal_content

    # Modal sheet sliding card has generous bottom padding for safe area and action buttons
    assert 'calc(48px + env(safe-area-inset-bottom, 24px))' in modal_content

    # Main content layout has safe padding
    assert 'padding-bottom: calc(108px' in nav_content or 'padding-bottom: calc(120px' in nav_content or 'padding-bottom: calc(112px' in nav_content


def test_push_service_public_key_and_subscription():
    """Verify VAPID public key generation and subscription handling."""
    pub_key = push_service.get_public_key()
    assert isinstance(pub_key, str)
    assert len(pub_key) == 87  # Standard 87-character base64url uncompressed EC key

    sub_payload = {
        'endpoint': 'https://fcm.googleapis.com/fcm/send/test-sub-token-12345',
        'keys': {
            'p256dh': 'BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9Q0A4APqOMZXbOU6VDDHXapQ53smTqdQhkkoEGCGvSu3iA',
            'auth': 'tBHItJI5svbpez7KI4CCXg'
        }
    }

    saved = push_service.save_subscription('test-user-123', sub_payload)
    assert saved is True

    subs = push_service.get_user_subscriptions('test-user-123')
    assert len(subs) >= 1
    assert subs[0]['endpoint'] == sub_payload['endpoint']

    # Remove subscription
    push_service.remove_subscription(sub_payload['endpoint'])
    subs_after = push_service.get_user_subscriptions('test-user-123')
    assert len(subs_after) == 0


def test_push_api_endpoints(client):
    """Verify /api/push/public-key and /api/push/subscribe endpoints."""
    # Test GET public-key
    resp_key = client.get('/api/push/public-key')
    assert resp_key.status_code == 200
    key_data = resp_key.get_json()
    assert key_data['success'] is True
    assert 'publicKey' in key_data
    assert len(key_data['publicKey']) == 87

    # Test POST subscribe
    sub_payload = {
        'subscription': {
            'endpoint': 'https://fcm.googleapis.com/fcm/send/client-test-endpoint',
            'keys': {
                'p256dh': 'BCmtest_p256dh_key_data_sample_value_string',
                'auth': 'test_auth_secret'
            }
        },
        'user_id': 'test-user-123'
    }
    resp_sub = client.post('/api/push/subscribe', json=sub_payload)
    assert resp_sub.status_code == 200
    sub_data = resp_sub.get_json()
    assert sub_data['success'] is True

    # Clean up
    push_service.remove_subscription('https://fcm.googleapis.com/fcm/send/client-test-endpoint')


def test_service_worker_push_and_click_handlers():
    """Verify static/sw.js includes push and notificationclick event listeners with deep-linking."""
    with open('static/sw.js', 'r', encoding='utf-8') as f:
        sw_content = f.read()

    assert "self.addEventListener('push'" in sw_content
    assert "self.addEventListener('notificationclick'" in sw_content
    assert '/farmer/reports' in sw_content
    assert 'clients.openWindow' in sw_content


def test_farmer_dashboard_notification_bell_and_consent_modals(client):
    """Verify notification bell is placed at greeting level, with notification center and push consent modals."""
    resp = client.get('/farmer/dashboard')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Notification bell button exists on the greeting row
    assert 'farmer-notification-btn' in html
    assert 'farmer-notification-bell-icon' in html
    assert 'farmer-notification-badge' in html

    # Notification center modal exists with clear all and mute controls
    assert 'farmer-notification-center-modal' in html
    assert 'notif-mute-toggle-btn' in html
    assert 'notif-clear-all-btn' in html
    assert 'farmer-notifications-list' in html

    # Push notification permission/consent modal exists
    assert 'farmer-push-consent-modal' in html
    assert 'confirmEnablePushNotifications' in html
    assert 'dismissPushConsent' in html


def test_push_public_key_endpoint(client):
    """Verify that /api/push/public-key returns 200 and a public key."""
    resp = client.get('/api/push/public-key')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'publicKey' in data


def test_update_report_workflow_filters_unknown_columns(monkeypatch):
    """Verify _update_report_workflow strips unknown columns and serializes complex data."""
    import main
    from unittest.mock import MagicMock

    captured_payload = {}

    class MockTable:
        def update(self, payload):
            nonlocal captured_payload
            captured_payload = payload
            return self

        def eq(self, col, val):
            return self

        def execute(self):
            return MagicMock(data=[{'id': 1}], error=None)

        def select(self, *args, **kwargs):
            return self

    monkeypatch.setattr(main.supabase, 'table', lambda tbl: MockTable())
    
    main._update_report_workflow(
        report_id=1,
        status='Under Review',
        extra_updates={
            'unknown_column_xyz': 'should_be_stripped',
            'last_read_at': 'should_be_stripped',
            'expert_recommendations': ['spray water'],
            'reviewed_by_id': 'invalid-uuid-string',
        }
    )

    assert 'unknown_column_xyz' not in captured_payload
    assert 'last_read_at' not in captured_payload
    assert captured_payload['expert_recommendations'] == '["spray water"]'
    assert captured_payload['reviewed_by_id'] is None
    assert captured_payload['status'] == 'Under Review'


def test_role_based_push_subscriptions_and_dispatch(monkeypatch):
    """Verify push subscriptions persist with roles and can be queried and targeted by role."""
    from app import push_service
    from unittest.mock import MagicMock

    lgu_sub = {
        'endpoint': 'https://fcm.googleapis.com/fcm/send/lgu-device-token-999',
        'keys': {
            'p256dh': 'BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9Q0A4APqOMZXbOU6VDDHXapQ53smTqdQhkkoEGCGvSu3iA',
            'auth': 'tBHItJI5svbpez7KI4CCXg'
        }
    }
    agri_sub = {
        'endpoint': 'https://fcm.googleapis.com/fcm/send/agri-device-token-888',
        'keys': {
            'p256dh': 'BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9Q0A4APqOMZXbOU6VDDHXapQ53smTqdQhkkoEGCGvSu3iA',
            'auth': 'tBHItJI5svbpez7KI4CCXg'
        }
    }

    push_service.save_subscription('lgu-user-1', lgu_sub, role='lgu')
    push_service.save_subscription('agri-user-1', agri_sub, role='agri_expert')

    # Query by role
    lgu_subs = push_service.get_role_subscriptions('lgu')
    agri_subs = push_service.get_role_subscriptions('agri_expert')

    assert any(s['endpoint'] == lgu_sub['endpoint'] for s in lgu_subs)
    assert not any(s['endpoint'] == agri_sub['endpoint'] for s in lgu_subs)

    assert any(s['endpoint'] == agri_sub['endpoint'] for s in agri_subs)
    assert not any(s['endpoint'] == lgu_sub['endpoint'] for s in agri_subs)

    # Mock webpush to verify dispatch
    dispatched_endpoints = []
    def mock_webpush(subscription_info, data, **kwargs):
        dispatched_endpoints.append(subscription_info['endpoint'])

    monkeypatch.setattr(push_service, 'webpush', mock_webpush)
    monkeypatch.setattr(push_service, '_vapid_private_pem', 'fake-private-key')

    # Dispatch to LGU
    res_lgu = push_service.send_push_to_role('lgu', title='New Scan', body='Farmer submitted new report')
    assert res_lgu['sent'] >= 1
    assert lgu_sub['endpoint'] in dispatched_endpoints

    # Dispatch to Agri Expert
    dispatched_endpoints.clear()
    res_agri = push_service.send_push_to_role('agri_expert', title='Farmer Feedback', body='Farmer requested visit')
    assert res_agri['sent'] >= 1
    assert agri_sub['endpoint'] in dispatched_endpoints

    # Clean up
    push_service.remove_subscription(lgu_sub['endpoint'])
    push_service.remove_subscription(agri_sub['endpoint'])


def test_ios_pwa_guidance_modal_rendered(client):
    """Verify iOS PWA push guidance modal is rendered in the page for Safari users."""
    resp = client.get('/farmer/dashboard')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'ios-push-guidance-modal' in html
    assert 'Enable Notifications on iOS' in html
    assert 'Add to Home Screen' in html



