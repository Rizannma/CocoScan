import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


def test_lgu_dashboard_has_notification_bell_and_modal(client, monkeypatch):
    """Verify that LGU dashboard renders the notification bell, counter badge, and drawer modals."""
    import main

    def mock_table(table_name):
        tbl = MagicMock()
        tbl.select.return_value = tbl
        tbl.eq.return_value = tbl
        tbl.order.return_value = tbl
        if table_name == 'users':
            tbl.execute.return_value = MagicMock(data=[{'first_name': 'LGU', 'last_name': 'Officer'}])
        elif table_name == 'reports':
            tbl.execute.return_value = MagicMock(data=[
                {
                    'id': 101,
                    'pest_type': 'Coconut Scale Insect',
                    'status': 'Under Review',
                    'barangay': 'San Gabriel',
                    'municipality': 'San Pablo City',
                    'created_at': '2026-09-20T10:00:00Z',
                    'updated_at': '2026-09-20T10:00:00Z',
                    'visit_chats': [{'count': 0}]
                }
            ])
        return tbl

    monkeypatch.setattr(main, 'supabase', MagicMock(table=mock_table))

    with client.session_transaction() as sess:
        sess['user_id'] = 'test-lgu-user'
        sess['user_role'] = 'lgu'
        sess['user_email'] = 'lgu@laguna.gov.ph'

    resp = client.get('/lgu/dashboard')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Verify notification bell button, icon, and badge exist
    assert 'farmer-notification-btn' in html
    assert 'farmer-notification-bell-icon' in html
    assert 'farmer-notification-badge' in html

    # Verify notification drawer modal and push consent modal are present
    assert 'farmer-notification-center-modal' in html
    assert 'farmer-push-consent-modal' in html
    assert 'notif-mute-toggle-btn' in html
    assert 'notif-clear-all-btn' in html


def test_agri_dashboard_has_notification_bell_and_modal(client, monkeypatch):
    """Verify that Agriculturist dashboard renders the notification bell, counter badge, and drawer modals."""
    import main

    def mock_table(table_name):
        tbl = MagicMock()
        tbl.select.return_value = tbl
        tbl.eq.return_value = tbl
        tbl.order.return_value = tbl
        if table_name == 'users':
            tbl.execute.return_value = MagicMock(data=[{'first_name': 'Maria', 'last_name': 'Santos'}])
        elif table_name == 'reports':
            tbl.execute.return_value = MagicMock(data=[
                {
                    'id': 202,
                    'pest_type': 'Rhinoceros Beetle',
                    'status': 'Under Review',
                    'barangay': 'Santa Maria',
                    'municipality': 'San Pablo City',
                    'created_at': '2026-09-20T11:00:00Z',
                    'updated_at': '2026-09-20T11:00:00Z',
                    'visit_chats': [{'count': 2}]
                }
            ])
        return tbl

    monkeypatch.setattr(main, 'supabase', MagicMock(table=mock_table))

    with client.session_transaction() as sess:
        sess['user_id'] = 'test-agri-user'
        sess['user_role'] = 'agri_expert'
        sess['user_email'] = 'agri@laguna.gov.ph'

    resp = client.get('/agriculturist/dashboard')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Verify notification bell button, icon, and badge exist
    assert 'farmer-notification-btn' in html
    assert 'farmer-notification-bell-icon' in html
    assert 'farmer-notification-badge' in html

    # Verify notification drawer modal and push consent modal are present
    assert 'farmer-notification-center-modal' in html
    assert 'farmer-push-consent-modal' in html
    assert 'notif-mute-toggle-btn' in html
    assert 'notif-clear-all-btn' in html


def test_admin_dashboard_has_no_notification_bell_or_modal(client, monkeypatch):
    """Verify that Admin dashboard does NOT render the notification bell, counter badge, or drawer modals."""
    import main

    def mock_table(table_name):
        tbl = MagicMock()
        tbl.select.return_value = tbl
        tbl.execute.return_value = MagicMock(data=[])
        return tbl

    monkeypatch.setattr(main, 'supabase', MagicMock(table=mock_table))

    with client.session_transaction() as sess:
        sess['user_id'] = 'test-admin-user'
        sess['user_role'] = 'admin'
        sess['user_email'] = 'admin@cocoscan.local'

    resp = client.get('/admin/dashboard')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Verify notification bell button, icon, and badge are NOT present
    assert 'farmer-notification-btn' not in html
    assert 'farmer-notification-bell-icon' not in html
    assert 'farmer-notification-badge' not in html

    # Verify notification drawer modal and push consent modal are NOT present
    assert 'farmer-notification-center-modal' not in html
    assert 'farmer-push-consent-modal' not in html


def test_api_notifications_admin_returns_empty(client):
    """Verify that /api/notifications returns empty list for admin sessions."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-admin-user'
        sess['user_role'] = 'admin'

    resp = client.get('/api/notifications')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['role'] == 'admin'
    assert data['notifications'] == []


def test_api_notifications_unauthenticated(client):
    """Verify that /api/notifications returns 401 when not logged in."""
    resp = client.get('/api/notifications')
    assert resp.status_code == 401
    data = resp.get_json()
    assert data['success'] is False


def test_api_notifications_agri_expert(client, monkeypatch):
    """Verify that /api/notifications returns role-tailored alerts for agriculturists."""
    import main

    reports_fixture = [
        {
            'id': 301,
            'pest_detected': 'Brontispa Longissima',
            'status': 'Awaiting Confirmed Schedule',
            'visit_reschedule_reason': 'Heavy rain flooded access road',
            'barangay': 'San Marcos',
            'municipality': 'San Pablo City',
            'created_at': '2026-09-20T08:00:00Z',
            'updated_at': '2026-09-20T09:30:00Z',
            'visit_chats': [{'count': 3}]
        },
        {
            'id': 302,
            'pest_detected': 'Coconut Scale Insect',
            'status': 'Under Review',
            'treatment_feedback': 'Need on-site visit',
            'barangay': 'San Buenaventura',
            'municipality': 'San Pablo City',
            'created_at': '2026-09-20T07:00:00Z',
            'updated_at': '2026-09-20T07:00:00Z',
            'visit_chats': [{'count': 0}]
        }
    ]

    def mock_table(table_name):
        tbl = MagicMock()
        tbl.select.return_value = tbl
        tbl.eq.return_value = tbl
        tbl.order.return_value = tbl
        tbl.limit.return_value = tbl
        tbl.execute.return_value = MagicMock(data=reports_fixture)
        return tbl

    monkeypatch.setattr(main, 'supabase', MagicMock(table=mock_table))

    with client.session_transaction() as sess:
        sess['user_id'] = 'test-agri-user'
        sess['user_role'] = 'agri_expert'

    resp = client.get('/api/notifications')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['role'] == 'agri_expert'
    assert len(data['notifications']) >= 2

    # Check reschedule alert
    resched_alert = next((n for n in data['notifications'] if n.get('type') == 'reschedule'), None)
    assert resched_alert is not None
    assert 'Reschedule Requested' in resched_alert['title']
    assert resched_alert['url'] == '/agriculturist/pending'

    # Check visit request alert
    visit_alert = next((n for n in data['notifications'] if n.get('type') == 'visit_request'), None)
    assert visit_alert is not None
    assert 'Visit Requested' in visit_alert['title']


def test_api_notifications_lgu(client, monkeypatch):
    """Verify that /api/notifications returns role-tailored alerts for LGU officers."""
    import main

    reports_fixture = [
        {
            'id': 401,
            'pest_type': 'Coconut Scale Insect',
            'status': 'Under Review',
            'barangay': 'Concepcion',
            'municipality': 'San Pablo City',
            'created_at': '2026-09-20T12:00:00Z',
            'updated_at': '2026-09-20T12:00:00Z',
            'visit_chats': [{'count': 0}]
        },
        {
            'id': 402,
            'pest_type': 'Rhinoceros Beetle',
            'status': 'Resolved',
            'barangay': 'Del Remedio',
            'municipality': 'San Pablo City',
            'created_at': '2026-09-19T08:00:00Z',
            'updated_at': '2026-09-20T14:00:00Z',
            'visit_chats': [{'count': 1}]
        }
    ]

    def mock_table(table_name):
        tbl = MagicMock()
        tbl.select.return_value = tbl
        tbl.eq.return_value = tbl
        tbl.order.return_value = tbl
        tbl.limit.return_value = tbl
        tbl.execute.return_value = MagicMock(data=reports_fixture)
        return tbl

    monkeypatch.setattr(main, 'supabase', MagicMock(table=mock_table))

    with client.session_transaction() as sess:
        sess['user_id'] = 'test-lgu-user'
        sess['user_role'] = 'lgu'

    resp = client.get('/api/notifications')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['role'] == 'lgu'
    assert len(data['notifications']) >= 2

    # Should link to /overview/reports
    for notif in data['notifications']:
        assert notif['url'] == '/overview/reports'


def test_language_strictly_en_for_officer_roles(client):
    """Verify that _get_current_language() strictly returns 'en' for staff/officer roles even if cookie is 'tl'."""
    import main
    from flask import session

    for officer_role in ['agri_expert', 'lgu', 'admin']:
        with app.test_request_context('/', headers={'Cookie': 'cocoscan_lang=tl'}):
            session['user_role'] = officer_role
            assert main._get_current_language() == 'en'


def test_language_strictly_en_for_staff_routes(client):
    """Verify that _get_current_language() strictly returns 'en' on any staff route even without session."""
    import main

    for staff_path in ['/agri/dashboard', '/lgu/dashboard', '/admin/dashboard', '/overview/reports', '/reports/overview', '/reports/view/101']:
        with app.test_request_context(staff_path, headers={'Cookie': 'cocoscan_lang=tl'}):
            assert main._get_current_language() == 'en'


def test_language_allowed_tl_for_farmer(client):
    """Verify that _get_current_language() allows 'tl' for farmers when cookie is 'tl'."""
    import main
    from flask import session

    with app.test_request_context('/farmer/dashboard', headers={'Cookie': 'cocoscan_lang=tl'}):
        session['user_role'] = 'farmer'
        assert main._get_current_language() == 'tl'


def test_farmer_notifications_in_tagalog(client, monkeypatch):
    """Verify that /api/notifications returns Tagalog content for farmers when language is 'tl'."""
    import main

    reports_fixture = [
        {
            'id': 501,
            'pest_detected': 'Brontispa Longissima',
            'status': 'Resolved',
            'created_at': '2026-09-21T08:00:00Z',
            'updated_at': '2026-09-21T09:00:00Z',
            'visit_chats': [{'count': 2}]
        }
    ]

    def mock_table(table_name):
        tbl = MagicMock()
        tbl.select.return_value = tbl
        tbl.eq.return_value = tbl
        tbl.order.return_value = tbl
        tbl.limit.return_value = tbl
        tbl.execute.return_value = MagicMock(data=reports_fixture)
        return tbl

    monkeypatch.setattr(main, 'supabase', MagicMock(table=mock_table))

    client.set_cookie('cocoscan_lang', 'tl')
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-farmer-user'
        sess['user_role'] = 'farmer'
        sess['lang'] = 'tl'

    resp = client.get('/api/notifications')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['role'] == 'farmer'

    # Check that Tagalog tags and titles are returned
    reco_notif = next((n for n in data['notifications'] if 'farmer_reco_' in n['id']), None)
    assert reco_notif is not None
    assert reco_notif['tag'] == 'Naresolba'
    assert 'Naresolbang Ulat' in reco_notif['title']

    chat_notif = next((n for n in data['notifications'] if 'farmer_chat_' in n['id']), None)
    assert chat_notif is not None
    assert chat_notif['tag'] == 'Usapan'
    assert 'Bagong Mensahe' in chat_notif['title']


