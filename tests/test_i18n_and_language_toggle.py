import pytest
import json
from app.i18n import t, get_all_translations, load_translations
from main import app


def test_i18n_module_loading():
    """Test that translation dictionaries are properly loaded from JSON files."""
    translations = load_translations(force_reload=True)
    assert "en" in translations
    assert "tl" in translations
    assert translations["en"]["navigation"]["app_title"] == "CocoScan"
    assert translations["tl"]["navigation"]["app_title"] == "CocoScan"
    assert translations["en"]["dashboard"]["page_title"] == "Farmer Dashboard"
    assert translations["tl"]["dashboard"]["page_title"] == "Dashboard ng Magsasaka"


def test_i18n_translation_lookup_and_fallback():
    """Test key resolution in English, Tagalog, and missing key fallback."""
    # English lookup
    assert t("navigation.menu_dashboard", lang="en") == "Dashboard"
    # Tagalog lookup
    assert t("navigation.menu_dashboard", lang="tl") == "Dashboard"
    assert t("navigation.menu_scan_pest", lang="tl") == "Mag-scan ng Peste"
    assert t("navigation.menu_drafts", lang="tl") == "Mga Draft"
    assert t("navigation.menu_my_reports", lang="tl") == "Aking mga Ulat"

    # Language label translations
    assert t("navigation.lang_preference", lang="en") == "Language"
    assert t("navigation.lang_preference", lang="tl") == "Wika"

    # Scan page upload instruction translations
    assert t("scanner.drop_zone_title", lang="en") == "Scan or upload your coconut leaf image"
    assert t("scanner.drop_zone_title", lang="tl") == "I-scan o i-upload ang dahon ng niyog"
    assert t("scan_page.drop_zone_title", lang="en") == "Scan or upload your coconut leaf image"
    assert t("scan_page.drop_zone_title", lang="tl") == "I-scan o i-upload ang dahon ng niyog"

    # Status translations
    assert t("workflow_statuses.under_review", lang="en") == "Under Review"
    assert t("workflow_statuses.under_review", lang="tl") == "Kasalukuyang Sinusuri"
    assert t("workflow_statuses.resolved", lang="tl") == "Nalutas Na"

    # Tooltip translations
    assert "dead leaves" in t("pest_knowledge_base.tooltips.sanitation", lang="en").lower()
    assert "hakbang" in t("pest_knowledge_base.tooltips.sanitation", lang="tl").lower()

    # Initial safe recommendations translations
    brontispa_rec = "Inspect central spear leaves and unopened fronds weekly for early feeding streaks or browning edges."
    assert "Suriin" in t(f"pest_knowledge_base.recommendations.initial_items.{brontispa_rec}", lang="tl")
    assert t(f"pest_knowledge_base.recommendations.initial_items.{brontispa_rec}", lang="en") == brontispa_rec

    rhino_rec = "Inspect palm crowns and spear leaves regularly for characteristic V-shaped cuts or entry boreholes."
    assert "V-shaped" in t(f"pest_knowledge_base.recommendations.initial_items.{rhino_rec}", lang="tl")

    # Fallback to English when key missing in Tagalog (or unknown lang)
    assert t("dashboard.page_title", lang="invalid_lang") == "Farmer Dashboard"
    # Default fallback when missing in both
    assert t("non_existent_section.non_existent_key", lang="tl", default="Fallback Text") == "Fallback Text"


def test_language_preference_api():
    """Test POST /api/user/language-preference endpoint."""
    client = app.test_client()

    # Test setting to Tagalog
    response = client.post(
        "/api/user/language-preference",
        data=json.dumps({"language": "tl"}),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["language"] == "tl"

    # Verify cookie is set
    cookies = response.headers.get_all("Set-Cookie")
    cookie_str = "".join(cookies)
    assert "cocoscan_lang=tl" in cookie_str

    # Test setting to English
    response_en = client.post(
        "/api/user/language-preference",
        data=json.dumps({"language": "en"}),
        content_type="application/json"
    )
    assert response_en.status_code == 200
    data_en = response_en.get_json()
    assert data_en["status"] == "success"
    assert data_en["language"] == "en"


def test_template_rendering_with_language_switch():
    """Test that farmer pages render with the active language strings."""
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["user_id"] = "offline_farmer"
        sess["user_role"] = "farmer"
        sess["user_email"] = "farmer@test.com"
        sess["user_name"] = "Juan Dela Cruz"
        sess["lang"] = "tl"

    # Request dashboard in Tagalog
    response = client.get("/farmer/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Dashboard ng Magsasaka" in html
    assert "Mag-scan ng Peste" in html
    assert "Mga Draft" in html
    assert "Aking mga Ulat" in html
    assert "Wika" in html
    assert 'lang="tl"' in html

    # Switch session to English
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    response_en = client.get("/farmer/dashboard")
    assert response_en.status_code == 200
    html_en = response_en.get_data(as_text=True)
    assert "Farmer Dashboard" in html_en
    assert "Scan Pest" in html_en
    assert "Drafts" in html_en
    assert "My Reports" in html_en
    assert "Language" in html_en
    assert 'lang="en"' in html_en


def test_farmer_drafts_and_scan_rendering():
    """Test farmer drafts and scan templates with localization."""
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["user_id"] = "offline_farmer"
        sess["user_role"] = "farmer"
        sess["user_email"] = "farmer@test.com"
        sess["lang"] = "tl"

    # Test drafts page
    resp_drafts = client.get("/farmer/drafts")
    assert resp_drafts.status_code == 200
    html_drafts = resp_drafts.get_data(as_text=True)
    assert "Mga Naka-save na Draft" in html_drafts or "Saved Drafts" in html_drafts
    assert 'lang="tl"' in html_drafts

    # Test scan page in Tagalog
    resp_scan = client.get("/farmer/scan")
    assert resp_scan.status_code == 200
    html_scan = resp_scan.get_data(as_text=True)
    assert "I-scan o i-upload ang dahon ng niyog" in html_scan
    assert "Wika" in html_scan
    assert 'lang="tl"' in html_scan
    assert 'id="hidden-upload-input" accept="image/*" style="display: none;"' in html_scan

    # Test scan page in English
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    resp_scan_en = client.get("/farmer/scan")
    assert resp_scan_en.status_code == 200
    html_scan_en = resp_scan_en.get_data(as_text=True)
    assert "Scan or upload your coconut leaf image" in html_scan_en
    assert "Camera captures live GPS, while uploaded photos use manual or map pin input." in html_scan_en
    assert "Language" in html_scan_en
    assert 'lang="en"' in html_scan_en
    assert 'id="hidden-upload-input" accept="image/*" style="display: none;"' in html_scan_en


def test_farmer_dashboard_and_weather_translations():
    """Test dashboard greetings and weather widget indicators in English and Tagalog."""
    # Greetings
    assert t("dashboard.greeting_morning", lang="en", name="Juan") == "Good Morning, Juan!"
    assert t("dashboard.greeting_morning", lang="tl", name="Juan") == "Magandang Umaga, Juan!"
    assert t("dashboard.greeting_afternoon", lang="en", name="Juan") == "Good Afternoon, Juan!"
    assert t("dashboard.greeting_afternoon", lang="tl", name="Juan") == "Magandang Hapon, Juan!"
    assert t("dashboard.greeting_evening", lang="en", name="Juan") == "Good Evening, Juan!"
    assert t("dashboard.greeting_evening", lang="tl", name="Juan") == "Magandang Gabi, Juan!"
    assert t("dashboard.greeting_welcome", lang="en", name="Juan") == "Welcome back, Juan!"
    assert t("dashboard.greeting_welcome", lang="tl", name="Juan") == "Maligayang pagbabalik, Juan!"

    # Weather widget risk levels and stat labels
    assert t("weather_widget.risk_high_level", lang="en") == "High Risk"
    assert t("weather_widget.risk_high_level", lang="tl") == "Mataas na Panganib"
    assert t("weather_widget.risk_moderate_level", lang="en") == "Moderate Risk"
    assert t("weather_widget.risk_moderate_level", lang="tl") == "Katamtamang Panganib"
    assert t("weather_widget.risk_low_level", lang="en") == "Low Risk"
    assert t("weather_widget.risk_low_level", lang="tl") == "Mababang Panganib"

    assert t("weather_widget.stat_temperature", lang="en") == "Temperature"
    assert t("weather_widget.stat_temperature", lang="tl") == "Temperatura"
    assert t("weather_widget.stat_humidity", lang="en") == "Humidity"
    assert t("weather_widget.stat_humidity", lang="tl") == "Halumigmig"
    assert t("weather_widget.stat_rainfall", lang="en") == "Rainfall"
    assert t("weather_widget.stat_rainfall", lang="tl") == "Pag-ulan"
    assert t("weather_widget.stat_wind", lang="en") == "Wind"
    assert t("weather_widget.stat_wind", lang="tl") == "Hangin"


def test_farmer_scan_elements_translations():
    """Test scanner headings, buttons, tips, and ensure Recent History Logs remains in English."""
    assert t("scanner.page_title", lang="en") == "Detect Pest"
    assert t("scanner.page_title", lang="tl") == "Tukuyin ang Peste"
    assert t("scanner.page_subtitle", lang="en") == "Powered by Image Recognition"
    assert t("scanner.page_subtitle", lang="tl") == "Pinapagana ng Image Recognition"

    assert t("scanner.btn_use_camera", lang="en") == "Use Camera"
    assert t("scanner.btn_use_camera", lang="tl") == "Gamitin ang Kamera"
    assert t("scanner.btn_upload_photo", lang="en") == "Upload Photo"
    assert t("scanner.btn_upload_photo", lang="tl") == "Mag-upload ng Larawan"

    # Tips for best results
    assert t("scanner.tips_title", lang="en") == "Tips for Best Results"
    assert "Tip" in t("scanner.tips_title", lang="tl") or "Gabay" in t("scanner.tips_title", lang="tl")
    assert "lighting" in t("scanner.tips_item1", lang="en").lower()
    assert "liwanag" in t("scanner.tips_item1", lang="tl").lower()
    assert "affected leaf" in t("scanner.tips_item2", lang="en").lower()
    assert "dahon" in t("scanner.tips_item2", lang="tl").lower()
    assert "full leaf" in t("scanner.tips_item3", lang="en").lower()
    assert "buong dahon" in t("scanner.tips_item3", lang="tl").lower()
    assert "blurry" in t("scanner.tips_item4", lang="en").lower()
    assert "malalabo" in t("scanner.tips_item4", lang="tl").lower()

    # Recent History Logs translated to Tagalog
    assert t("scanner.history_logs_title", lang="en") == "Recent History Logs"
    assert t("scanner.history_logs_title", lang="tl") == "Mga Kamakailang Tala ng Scan"


def test_weather_widget_no_duplicate_risk_prefixing():
    """Verify backend and formatting logic do not duplicate risk indicators."""
    from main import calculate_environmental_risk, _format_risk_text

    # Test _format_risk_text handles clean strings and already-prefixed strings cleanly
    formatted_en = _format_risk_text("Moderate Risk", "Standard environmental monitoring active.")
    assert formatted_en == "<strong>Moderate Risk</strong>: Standard environmental monitoring active."

    duplicate_input = "Katamtamang Panganib: Aktibo ang pagsubaybay sa lagay ng kapaligiran."
    formatted_tl = _format_risk_text("Katamtamang Panganib", duplicate_input)
    assert formatted_tl == "<strong>Katamtamang Panganib</strong>: Aktibo ang pagsubaybay sa lagay ng kapaligiran."
    assert "Katamtamang Panganib: Katamtamang Panganib" not in formatted_tl

    # Test calculate_environmental_risk output in both languages
    risk_en = calculate_environmental_risk(28, 60, 0, lang="en")
    assert "Low Risk" in risk_en["text"]
    assert risk_en["text"].count("Low Risk") == 1

    risk_tl = calculate_environmental_risk(28, 60, 0, lang="tl")
    assert "Mababang Panganib" in risk_tl["text"]
    assert risk_tl["text"].count("Mababang Panganib") == 1


def test_initial_recommendations_translations():
    """Verify default recommendation checklist items are translated into Tagalog."""
    recos_en = t("recommendations.initial_items", lang="en")
    recos_tl = t("recommendations.initial_items", lang="tl")
    assert isinstance(recos_tl, dict)
    assert isinstance(recos_en, dict)

    # Brontispa recommendations
    assert recos_tl["Prune and safely dispose of infested leaves"] == "Putulin at ligtas na sunugin o ibaon ang mga apektadong dahon"
    assert recos_tl["Maintain field sanitation and monitor infestation levels"] == "Panatilihin ang kalinisan ng sakahan at subaybayan ang dami ng peste"
    assert recos_tl["Release earwigs and Tetrastichus parasitoids for natural control"] == "Magpakawala ng earwigs at Tetrastichus parasitoids para sa natural na pagpuksa"
    assert recos_tl["Spray white Muscardine fungus"] == "Mag-spray ng white Muscardine fungus"
    assert recos_tl["Use approved pesticide early morning for severe infestations"] == "Gumamit ng aprubadong pamatay-peste sa madaling araw kapag labis na ang pamemeste"

    # Rhinoceros Beetle recommendations
    assert recos_tl["Improve farm sanitation and remove breeding sites"] == "Pabutihin ang kalinisan ng sakahan at alisin ang mga pinamumugaran"
    assert recos_tl["Install pheromone traps and green Muscardine fungus log traps"] == "Magkabit ng mga pheromone trap at green Muscardine fungus log trap"
    assert recos_tl["Apply biological treatment or use light traps at night"] == "Maglapat ng biological treatment o gumamit ng light trap sa gabi"
    assert recos_tl["Monitor weekly and consult an agricultural technician for severe cases"] == "Subaybayan linggu-linggo at sumangguni sa agricultural technician kapag malala ang kaso"

    # Healthy Leaf recommendations
    assert recos_tl["Continue regular monitoring"] == "Ipagpatuloy ang regular na pagsubaybay"
    assert recos_tl["Maintain current sanitation practices"] == "Panatilihin ang kasalukuyang gawi sa kalinisan"


def test_saved_drafts_and_my_reports_translations():
    """Test drafts and reports titles, subtitles, empty states, and filter controls."""
    # Drafts
    assert t("drafts.page_title", lang="en") == "Saved Drafts"
    assert t("drafts.page_title", lang="tl") == "Mga Naka-save na Draft"
    assert "Resume, submit, or remove" in t("drafts.page_subtitle", lang="en")
    assert "Ipagpatuloy, ipasa, o tanggalin" in t("drafts.page_subtitle", lang="tl")
    assert t("drafts.empty_title", lang="en") == "No Saved Drafts"
    assert t("drafts.empty_title", lang="tl") == "Walang Naka-save na Draft"
    assert "You don't have any draft scans saved yet" in t("drafts.empty_desc", lang="en") or "You don’t have any draft scans saved yet" in t("drafts.empty_desc", lang="en")
    assert "Wala ka pang naka-save na draft scan" in t("drafts.empty_desc", lang="tl")

    # My Reports
    assert t("reports.page_title", lang="en") == "My Reports"
    assert t("reports.page_title", lang="tl") == "Aking mga Ulat"
    assert t("reports.page_subtitle", lang="en") == "Overall submitted reports"
    assert t("reports.page_subtitle", lang="tl") == "Pangkalahatang mga naipasa na ulat"
    assert t("reports.filter_all", lang="en") == "All"
    assert t("reports.filter_all", lang="tl") == "Lahat"
    assert t("reports.filter_status", lang="en") == "Status ▾"
    assert t("reports.filter_status", lang="tl") == "Katayuan ▾"
    assert t("reports.filter_pest", lang="en") == "Pest ▾"
    assert t("reports.filter_pest", lang="tl") == "Peste ▾"
    assert t("reports.clear_filters", lang="en") == "Clear Filters"
    assert t("reports.clear_filters", lang="tl") == "Burahin ang mga Filter"


def test_report_modal_detail_fields_translations():
    """Test all internal report modal fields and resolution details in English and Tagalog."""
    from main import _format_confirmed_schedule_label

    # Initial recommendations
    assert t("modal.initial_reco_title", lang="en") == "Initial Recommendations"
    assert "Rekomendasyon" in t("modal.initial_reco_title", lang="tl")
    assert t("modal.initial_reco_subtext", lang="en") == "Tap the question mark icon for more details."
    assert "question mark" in t("modal.initial_reco_subtext", lang="tl")
    assert t("modal.initial_reco_empty", lang="en") == "No initial recommendations available."
    assert "rekomendasyon" in t("modal.initial_reco_empty", lang="tl").lower()

    # Farmer notes
    assert t("modal.farmer_notes_title", lang="en") == "Farmer Notes"
    assert t("modal.farmer_notes_title", lang="tl") == "Mga Tala ng Magsasaka"
    assert t("modal.notes_empty", lang="en") == "No notes logged."
    assert "tala" in t("modal.notes_empty", lang="tl").lower()

    # Additional images
    assert t("modal.additional_images_title", lang="en") == "Additional Images"
    assert t("modal.additional_images_title", lang="tl") == "Mga Karagdagang Larawan"
    assert t("modal.additional_images_empty", lang="en") == "No additional images uploaded."
    assert t("modal.additional_images_empty", lang="tl") == "Walang karagdagang larawang na-upload."
    assert "larawan" in t("modal.additional_images_empty", lang="tl").lower()

    # Expert assessment
    assert t("modal.expert_assessment_title", lang="en") == "Expert Assessment"
    assert t("modal.expert_assessment_title", lang="tl") == "Pagsusuri ng Eksperto"
    assert t("modal.expert_assessment_empty", lang="en") == "No expert assessment available yet."
    assert t("modal.expert_assessment_empty", lang="tl") == "Wala pang available na pagsusuri mula sa eksperto."
    assert "eksperto" in t("modal.expert_assessment_empty", lang="tl").lower()
    assert t("modal.expert_assessment_prompt", lang="en") == "Submit report for expert assessment"
    assert "eksperto" in t("modal.expert_assessment_prompt", lang="tl").lower()
    assert t("modal.expert_assessment_issued", lang="en") == "Expert assessment issued."
    assert "eksperto" in t("modal.expert_assessment_issued", lang="tl").lower()

    # Visit request discussion & Reschedule
    assert t("modal.discussion_toggle_title", lang="en") == "Visit Request Discussion"
    assert t("modal.discussion_toggle_title", lang="tl") == "Talakayan sa Kahilingan sa Pagbisita"
    assert t("modal.discussion_empty", lang="en") == "No discussion messages yet."
    assert "mensahe" in t("modal.discussion_empty", lang="tl").lower()
    assert t("modal.discussion_closed", lang="en") == "The scheduling discussion has been closed."
    assert t("modal.discussion_closed", lang="tl") == "Isinara na ang talakayan sa pag-iskedyul."
    assert t("modal.btn_request_reschedule", lang="en") == "Request Reschedule"
    assert t("modal.btn_request_reschedule", lang="tl") == "Humiling ng Bagong Iskedyul"

    assert t("modal.reschedule_modal_title", lang="en") == "Request Reschedule"
    assert "Iskedyul" in t("modal.reschedule_modal_title", lang="tl")
    assert t("modal.reschedule_reason_label", lang="en") == "Reason"
    assert t("modal.reschedule_reason_label", lang="tl") == "Dahilan"
    assert t("modal.reschedule_opt_emergency", lang="en") == "Emergency"
    assert "Emergency" in t("modal.reschedule_opt_emergency", lang="tl")
    assert t("modal.reschedule_opt_weather", lang="en") == "Bad weather"
    assert "panahon" in t("modal.reschedule_opt_weather", lang="tl").lower()
    assert t("modal.reschedule_btn_submit", lang="en") == "Submit Request"
    assert "Ipasa" in t("modal.reschedule_btn_submit", lang="tl")

    assert t("modal.resolution_details_title", lang="en") == "Resolution Details"
    assert t("modal.resolution_details_title", lang="tl") == "Mga Detalye ng Paglutas"
    assert t("modal.resolution_expert_assessment_label", lang="en") == "Expert Assessment Given:"
    assert t("modal.resolution_expert_assessment_label", lang="tl") == "Ibinigay na Pagsusuri ng Eksperto:"
    assert t("modal.report_summary_resolution_title", lang="en") == "Report Summary Resolution"
    assert t("modal.report_summary_resolution_title", lang="tl") == "Resolusyon ng Buod ng Ulat"
    assert t("modal.schedule_new_confirmed", lang="en") == "New Schedule Confirmed"
    assert t("modal.schedule_new_confirmed", lang="tl") == "Kumpirmado ang Bagong Iskedyul"

    # Confirmed schedule label formatting
    assert _format_confirmed_schedule_label("2026-07-27", "08:00:00", "10:00:00", lang="en") == "Confirmed: July 27, 2026, from 8:00 AM to 10:00 AM"
    assert _format_confirmed_schedule_label("2026-07-27", "08:00:00", "10:00:00", lang="tl") == "Kumpirmado: Hulyo 27, 2026, mula 8:00 AM hanggang 10:00 AM"

    assert t("modal.label_outcome", lang="en") == "Outcome"
    assert t("modal.label_outcome", lang="tl") in ["Kinahinatnan", "Kinalabasan"]
    assert "resolved by following expert assessment" in t("modal.resolution_outcome_text", lang="en").lower()
    assert "eksperto" in t("modal.resolution_outcome_text", lang="tl").lower()
    assert t("modal.resolution_resolved_on", lang="en") == "Resolved On:"
    assert t("modal.resolution_resolved_on", lang="tl") == "Nalutas Noong:"


