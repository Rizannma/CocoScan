import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main


def test_report_transition_map_rejects_backward_transition():
    with pytest.raises(ValueError):
        main._assert_report_transition("Assessment Issued", "Under Review")


def test_report_transition_map_allows_follow_up_reopen():
    main._assert_report_transition("Resolved", "Under Review")


def test_report_details_denies_another_farmer_report():
    main.app.config["TESTING"] = True
    with main.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = "farmer-a"
            session["user_role"] = "farmer"
        report = {"id": 20, "user_id": "farmer-b", "reviewed_by_id": None, "status": "Under Review"}
        query = MagicMock()
        query.select.return_value = query
        query.eq.return_value = query
        query.execute.return_value = MagicMock(data=[report])
        with patch.object(main.supabase, "table", return_value=query):
            response = client.get("/api/reports/20")
    assert response.status_code == 403
