/**
 * CocoScan Internationalization (i18n) Client Module
 * Supports seamless instant translation switching, offline persistence,
 * session synchronization, and DOM binding.
 */
(function (global) {
  "use strict";

  const TRANSLATIONS = {
    en: {
  "_meta": {
    "role": "Farmer",
    "source_language": "en",
    "target_language": "tl",
    "description": "Extracted hardcoded UI labels, button texts, error messages, and status updates for the Farmer role across CocoScan views, templates, JavaScript scripts, and backend endpoints."
  },
  "navigation": {
    "app_title": "CocoScan",
    "app_subtitle": "Coconut Pest Detection",
    "menu_section_main": "Main Menu",
    "menu_dashboard": "Dashboard",
    "menu_scan_pest": "Scan Pest",
    "menu_drafts": "Drafts",
    "menu_my_reports": "My Reports",
    "menu_profile": "Profile",
    "menu_settings": "Settings",
    "user_role_farmer": "Farmer",
    "profile_modal_title": "Farmer Profile & Settings",
    "profile_role_farmer": "Registered Farmer",
    "profile_sec_identity": "Farmer Details",
    "profile_sec_preferences": "Quick Settings",
    "profile_sec_status": "Device & Sync Status",
    "profile_lang_label": "Language / Wika",
    "profile_status_online": "Online & Synchronized",
    "profile_status_offline": "Offline Mode (Local Storage)",
    "profile_drafts_count": "Saved Field Drafts",
    "profile_btn_refresh": "Refresh App Data",
    "profile_btn_logout": "Log Out Account",
    "profile_logout_confirm": "Are you sure you want to log out of CocoScan?",
    "profile_btn_close": "Close",
    "btn_logout": "Logout",
    "btn_go_back": "Go Back",
    "switch_lang_title": "Language: English (Click to switch to Tagalog)",
    "lang_toggle_en": "EN",
    "lang_toggle_tl": "TL",
    "lang_preference": "Language"
  },
  "pwa_and_offline": {
    "pwa_install_title": "Install CocoScan App",
    "pwa_install_subtitle": "Add to Home Screen for fast, offline-ready access",
    "pwa_install_btn": "Install",
    "pwa_dismiss_btn": "Dismiss",
    "offline_portal_badge": "CocoScan Offline Mode Active",
    "offline_portal_title": "You're Offline",
    "offline_portal_desc": "Your network connection is unavailable right now. Thanks to CocoScan PWA, you can still perform leaf scans in the field and view locally saved drafts without an internet connection.",
    "offline_portal_btn_scanner": "Open Field Scanner",
    "offline_portal_btn_drafts": "View Saved Offline Drafts",
    "offline_portal_btn_dashboard": "Return to Farmer Dashboard",
    "offline_portal_btn_retry": "Retry Connection",
    "offline_portal_btn_switch": "Switch Account",
    "offline_portal_checking": "Checking connection...",
    "offline_portal_restored": "Connection restored!",
    "offline_portal_still_offline": "Still Offline",
    "offline_portal_footer": "Field scans will be automatically saved to your local storage until signal is restored."
  },
  "dashboard": {
    "page_title": "Farmer Dashboard",
    "page_subtitle": "Overview of your reported and detected pests",
    "greeting_morning": "Good Morning, {name}!",
    "greeting_afternoon": "Good Afternoon, {name}!",
    "greeting_evening": "Good Evening, {name}!",
    "greeting_welcome": "Welcome back, {name}!",
    "greeting_dashboard": "Dashboard",
    "banner_offline_title": "Offline Access Active",
    "banner_offline_desc": "You can perform field scans and save them to local drafts without an active internet connection.",
    "banner_offline_action": "Launch Scanner",
    "modal_offline_ready_badge": "Offline Mode Active",
    "modal_offline_ready_title": "Offline Access Ready",
    "modal_offline_ready_desc": "You are offline, but you can use CocoScan and it will be saved to the drafts and later, you can access it again.",
    "modal_offline_btn_scan": "Start Pest Scan",
    "modal_offline_btn_continue": "Continue to Dashboard",
    "metric_total_cases": "Total Reported Cases",
    "metric_total_subtext": "All Time Submitted",
    "metric_pending_cases": "Pending",
    "metric_pending_subtext": "Awaiting for Review",
    "metric_resolved_cases": "Resolved",
    "metric_resolved_subtext": "Expert Solutions",
    "quick_action_title": "Scan Now",
    "quick_action_desc": "Upload leaf images for automated anomaly checks.",
    "quick_action_btn": "Launch Scanner",
    "notif_center_title": "Notifications",
    "notif_btn_clear_all": "Clear All",
    "notif_btn_mute": "Mute",
    "notif_btn_unmute": "Unmute",
    "notif_empty_title": "No New Notifications",
    "notif_empty_desc": "All your coconut pest reports and visit schedules are up to date.",
    "notif_toast_muted": "Notifications muted",
    "notif_toast_unmuted": "Notifications unmuted",
    "notif_toast_cleared": "All notifications cleared",
    "notif_badge_updates": "{count} updates",
    "notif_badge_update_one": "1 update",
    "notif_badge_empty": "0 updates",
    "notif_tag_diagnosis": "Diagnosis",
    "notif_tag_resolved": "Resolved",
    "notif_tag_visit": "Visit",
    "notif_tag_chat": "Chat",
    "notif_title_reco": "Expert Assessment: {pest}",
    "notif_title_resolved": "Report Resolved: {pest}",
    "notif_desc_reco": "Expert management recommendations have been issued for your scan.",
    "notif_desc_resolved": "Treatment solution confirmed and report closed.",
    "notif_title_visit_confirmed": "Farm Visit Confirmed: #{id}",
    "notif_title_visit_scheduled": "Visit Scheduled: #{id}",
    "notif_desc_visit": "An agriculturist has confirmed a farm inspection schedule.",
    "notif_title_chat": "New Discussion Message: #{id}",
    "notif_desc_chat": "{count} message(s) on your visit scheduling thread.",
    "notif_action_view": "View Report",
    "notif_btn_dismiss": "Dismiss",
    "push_consent_title": "Enable Push Notifications?",
    "push_consent_desc": "Receive immediate alerts on your device for expert pest diagnoses, confirmed visit dates, and discussion updates.",
    "push_consent_btn_enable": "Yes, Enable Notifications",
    "push_consent_btn_mute": "Keep Muted / Not Now",
    "push_consent_feature_reco": "Expert diagnosis & treatment recommendations",
    "push_consent_feature_visit": "Farm visit schedules & appointment reminders",
    "push_consent_feature_chat": "Real-time responses to your questions"
  },
  "weather_widget": {
    "title": "Current Weather",
    "stat_temperature": "Temperature",
    "stat_humidity": "Humidity",
    "stat_rainfall": "Rainfall",
    "stat_wind": "Wind",
    "label_temperature": "Temperature",
    "label_humidity": "Humidity",
    "label_rainfall": "Rainfall",
    "label_wind": "Wind",
    "status_offline": "Offline",
    "alert_offline": "Unable to fetch real-time atmospheric updates. Please check your connection.",
    "risk_high_level": "High Risk",
    "risk_high": "High Risk",
    "risk_high_desc": "Accelerated breeding climate detected for both Brontispa and Rhinoceros Beetles. Inspect young fronds immediately.",
    "risk_high_text": "Accelerated breeding climate detected for both Brontispa and Rhinoceros Beetles. Inspect young fronds immediately.",
    "risk_moderate_level": "Moderate Risk",
    "risk_moderate": "Moderate Risk",
    "risk_moderate_rhino_text": "High moisture levels favor Rhinoceros Beetle breeding nests and localized larval development.",
    "risk_desc_moisture": "High moisture levels favor Rhinoceros Beetle breeding nests and localized larval development.",
    "risk_moderate_brontispa_text": "Warm, dry foliage layout accelerates early-stage Brontispa leaf-incubation cycles.",
    "risk_desc_dry": "Warm, dry foliage layout accelerates early-stage Brontispa leaf-incubation cycles.",
    "risk_moderate_general_text": "Environmental monitoring active.",
    "risk_desc_monitoring": "Environmental monitoring active.",
    "risk_low_level": "Low Risk",
    "risk_low": "Low Risk",
    "risk_low_desc": "Current climate conditions are within baseline stability parameters for pest development.",
    "risk_low_text": "Current climate conditions are within baseline stability parameters for pest development.",
    "risk_desc_stable": "Current climate conditions are within baseline stability parameters for pest development.",
    "risk_unavailable": "Risk assessment unavailable offline."
  },
  "scan_page": {
    "page_title": "Detect Pest",
    "page_subtitle": "Powered by Image Recognition",
    "drop_zone_title": "Scan or upload your coconut leaf image",
    "drop_zone_subtext": "Scan or upload your coconut leaf image",
    "drop_zone_subtitle": "Scan or upload your coconut leaf image",
    "btn_use_camera": "Use Camera",
    "btn_upload_photo": "Upload Photo",
    "gps_helper_text": "Camera captures live GPS, while uploaded photos use manual or map pin input.",
    "gps_help_text": "Camera captures live GPS, while uploaded photos use manual or map pin input.",
    "gps_unavailable_notice": "GPS unavailable on this device. Location marked as unavailable.",
    "tips_title": "Tips for Best Results",
    "tip_1": "Use good lighting conditions",
    "tips_item1": "Use good lighting conditions",
    "tip_2": "Focus on affected leaf areas",
    "tips_item2": "Focus on affected leaf areas",
    "tip_3": "Capture the full leaf if possible",
    "tips_item3": "Capture the full leaf if possible",
    "tip_4": "Avoid blurry images",
    "tips_item4": "Avoid blurry images",
    "history_logs_title": "Recent History Logs",
    "history_panel_title": "Recent History Logs",
    "history_empty_title": "No recent scan history",
    "history_empty_desc": "Your recent insect diagnostics will be tracked here once you execute a localized leaf scan operation.",
    "history_timestamp_unavailable": "Timestamp unavailable",
    "location_modal_title": "Set Tree Location",
    "location_modal_desc": "To ensure reporting accuracy for uploaded photos, please enter the farm location or tap the map to place a pin where this coconut tree is located.",
    "loc_modal_title": "Set Tree Location",
    "loc_modal_desc": "To ensure reporting accuracy for uploaded photos, please enter the farm location or tap the map to place a pin where this coconut tree is located.",
    "loc_label_farm": "Farm / Barangay Location",
    "loc_btn_use_gps": "Use Current GPS",
    "loc_input_placeholder": "San Nicolas, San Pablo City",
    "loc_map_pin_label": "Tap or Drag Pin on Map",
    "loc_detected_badge": "Detected location",
    "loc_btn_cancel": "Cancel",
    "loc_btn_confirm_scan": "Scan Now",
    "location_input_label": "Farm / Barangay Location",
    "location_btn_current_gps": "Use Current GPS",
    "location_placeholder": "San Nicolas, San Pablo City",
    "location_map_label": "Tap or Drag Pin on Map",
    "location_detected_badge": "Detected location",
    "btn_cancel": "Cancel",
    "btn_confirm_and_scan": "Scan Now",
    "offline_modal_title": "Saved to Local Drafts",
    "offline_modal_desc": "You are currently offline. Your photo has been securely saved to your local device drafts. When you regain internet connection, open the Drafts page to run AI pest detection and submit your report.",
    "offline_saved_title": "Saved to Local Drafts",
    "offline_saved_desc": "You are currently offline. Your photo has been securely saved to your local device drafts. When you regain internet connection, open the Drafts page to run AI pest detection and submit your report.",
    "offline_saved_btn_view_drafts": "View Saved Drafts",
    "offline_saved_btn_another": "Upload / Scan Another",
    "btn_view_saved_drafts": "View Saved Drafts",
    "btn_scan_another": "Upload / Scan Another",
    "loading_title": "Analyzing Image Spectrum...",
    "loading_subtitle": "Running inference rules",
    "mobile_access_required_title": "Mobile Access Required",
    "mobile_restriction_title": "Mobile Access Required",
    "mobile_access_required_desc": "You can view your dashboard on any device, but Scan Pest requires a mobile smartphone to utilize its camera for capturing real-time leaf images directly in the field.",
    "mobile_restriction_desc": "You can view your dashboard on any device, but Scan Pest requires a mobile smartphone to utilize its camera for capturing real-time leaf images directly in the field.",
    "alert_select_photo": "Please capture or select a coconut leaf photo before scanning.",
    "alert_validation_notice": "Image Validation Notice: ",
    "alert_gps_failed": "Could not retrieve device GPS location: ",
    "alert_location_required": "Please enter a location or pin the location on the map.",
    "alert_offline_save_prompt": "Could not connect to the AI Scanner. Would you like to save this photo as an offline draft to process later?",
    "alert_discard_session": "Are you sure you want to discard this field scan session? Data will be lost.",
    "alert_notes_required": "Please provide your farmer notes before submitting the report.",
    "alert_no_network_save_draft": "No network connection detected. Save this scan as a draft instead?",
    "alert_submit_success": "SUCCESS: Report for {pest} has been submitted successfully.",
    "alert_submit_failed_save_draft": "The report could not be synced right now. Save this scan as a draft instead?"
  },
  "drafts_page": {
    "page_title": "Saved Drafts",
    "page_subtitle": "Resume, submit, or remove your saved field scan reports.",
    "btn_refresh": "Refresh Layout",
    "empty_title": "No Saved Drafts",
    "empty_desc": "You don't have any draft scans saved yet. Go to Scan Pest page to begin your first report.",
    "offline_scan_title": "Offline Scan",
    "badge_pending_ai": "Pending AI",
    "badge_scanned": "Scanned",
    "label_captured": "Captured:",
    "label_saved": "Saved:",
    "label_gps": "GPS",
    "label_notes": "Notes",
    "label_no_notes": "No notes added",
    "no_notes": "No notes added",
    "btn_continue_edit": "Continue/Edit",
    "btn_scan": "Scan",
    "btn_delete_draft": "Delete Draft",
    "btn_save_changes": "Save Changes",
    "btn_saving_changes": "Saving Changes...",
    "alert_confirm_delete": "Are you sure you want to delete this saved draft?",
    "alert_draft_saved_online": "Draft saved successfully!",
    "alert_draft_saved_offline": "Saved as Offline Draft! When back online, open the Drafts page to run AI and submit.",
    "alert_connect_to_scan": "An internet connection is required to analyze pests with AI. Please reconnect to scan this draft.",
    "alert_scanning_in_progress": "Scanning in progress...",
    "alert_changes_saved": "Draft changes saved successfully.",
    "draft_not_found": "Draft not found.",
    "unable_load_draft": "Unable to load draft."
  },
  "reports_page": {
    "page_title": "My Reports",
    "page_subtitle": "Overall submitted reports",
    "banner_offline_title": "Offline Mode • Local Reports View",
    "banner_offline_desc": "Reports were synced and will load once an active internet connection has been established.",
    "banner_offline_badge": "Cached",
    "offline_banner_title": "Offline Mode • Local Reports View",
    "offline_banner_desc": "Reports were synced and will load once an active internet connection has been established.",
    "offline_cached_badge": "Cached",
    "filter_all": "All",
    "filter_status": "Status ▾",
    "filter_pest": "Pest ▾",
    "filter_all_statuses": "All Statuses",
    "filter_all_pests": "All Pests",
    "filter_calendar_title": "Filter by date",
    "filter_by_date": "Filter by date",
    "btn_clear_filters": "Clear Filters",
    "clear_filters": "Clear Filters",
    "btn_refresh": "Refresh Layout",
    "empty_title": "No Reports Found",
    "empty_desc": "We couldn't find any records matching your criteria. Try adjustments to your text search queries or structural filters.",
    "empty_offline_title": "Offline Reports Sync",
    "empty_offline_desc": "Reports were synced and will load once an active internet connection has been established.",
    "pagination_showing": "Showing {start}–{end} of {total}",
    "pagination_prev": "← Previous",
    "pagination_next": "Next →",
    "badge_unread": "{count} unread",
    "followup_title": "Follow Up Details",
    "followup_detected_pest": "Detected Pest:",
    "followup_confidence": "Confidence:",
    "followup_damage": "Damage:",
    "followup_orig_notes": "Original Notes:",
    "fup_modal_title": "Follow Up Details",
    "fup_detected_pest": "Detected Pest:",
    "fup_confidence": "Confidence:",
    "fup_damage": "Damage:",
    "fup_original_notes": "Original Notes:",
    "fup_upload_title": "Upload Follow Up Image",
    "fup_upload_desc": "Capture New Update Leaf Frame",
    "fup_btn_take_photo": "Take Photo",
    "fup_btn_upload_image": "Upload Image",
    "fup_progress_notes_title": "Progress Notes",
    "fup_progress_notes_placeholder": "Write your additional treatment notes here...",
    "fup_btn_submit": "Submit Follow Up",
    "fup_btn_submitting": "Submitting Follow Up...",
    "fup_success": "Follow-up submitted successfully.",
    "fup_failed": "Unable to submit the follow-up right now."
  },
  "report_modal": {
    "modal_title": "Report Summary",
    "summary_title": "Report Summary",
    "btn_print": "Print report",
    "btn_close": "Close",
    "label_status": "Status:",
    "status_label": "Status:",
    "label_confidence": "Confidence:",
    "confidence_label": "Confidence:",
    "label_farmer": "Farmer:",
    "farmer_label": "Farmer:",
    "label_location": "Location:",
    "location_label": "Location:",
    "label_scanned": "Scanned:",
    "scanned_label": "Scanned:",
    "label_reason": "Reason",
    "label_outcome": "Outcome",
    "notes_card_title": "Farmer Notes",
    "farmer_notes_title": "Farmer Notes",
    "notes_card_placeholder": "Describe what you observed on your coconut tree (e.g., yellowing leaves, damaged fruits, unusual insects, or other signs).",
    "farmer_notes_placeholder": "Describe what you observed on your coconut tree (e.g., yellowing leaves, damaged fruits, unusual insects, or other signs).",
    "notes_empty": "No notes logged.",
    "initial_reco_title": "Initial Recommendations",
    "verified_reco_title": "Recommendations",
    "initial_reco_desc": "These are general recommendations for the detected pest to help your initial decision on what to do.",
    "initial_reco_subtext": "Tap the question mark icon for more details.",
    "initial_reco_tooltip_prompt": "Tap the question mark icon for more details.",
    "initial_reco_empty": "No initial recommendations available.",
    "supporting_photos_title": "Supporting Photos (optional)",
    "supporting_photos_tap": "Add Extra Field Images",
    "supporting_photos_prompt": "Add Extra Field Images",
    "supporting_photos_subtext": "Tap to open your phone gallery directory",
    "supporting_photos_error": "You can upload a maximum of 3 supporting photos only.",
    "supporting_photos_max_error": "You can upload a maximum of 3 supporting photos only.",
    "additional_images_title": "Additional Images",
    "additional_images_empty": "No additional images uploaded.",
    "expert_assessment_title": "Expert Assessment",
    "expert_assessment_empty": "No expert assessment available yet.",
    "expert_assessment_prompt": "Submit report for expert assessment",
    "expert_assessment_issued": "Expert assessment issued.",
    "expert_issued_by": "Issued by {name}",
    "btn_submit_report": "Submit Report",
    "btn_submitting_report": "Submitting report…",
    "btn_cancel_report": "Cancel",
    "followup_card_title": "Follow-up",
    "followup_section_title": "Follow-up",
    "discussion_toggle_title": "Visit Request Discussion",
    "discussion_messages_count": "{count} messages",
    "discussion_message_singular": "message",
    "discussion_message_plural": "messages",
    "discussion_empty": "No discussion messages yet.",
    "discussion_placeholder": "Type a message to reply...",
    "discussion_btn_send": "Send",
    "discussion_tip_reschedule": "Tip: Click the 'Visit Request Discussion' button to chat and finalize a new date and time.",
    "discussion_closed": "The scheduling discussion has been closed.",
    "btn_request_reschedule": "Request Reschedule",
    "resolution_details_title": "Resolution Details",
    "report_summary_resolution_title": "Report Summary Resolution",
    "schedule_new_confirmed": "New Schedule Confirmed",
    "schedule_confirmed_prefix": "Confirmed:",
    "schedule_previous_prefix": "Previous Schedule:",
    "schedule_from": "from",
    "schedule_to": "to",
    "resolution_outcome_text": "Issue resolved by following expert assessment.",
    "resolution_resolved_on": "Resolved On:",
    "resolution_expert_assessment_label": "Expert Assessment Given:",
    "resolution_visit_completed_text": "The agriculturist has completed the visit and marked the issue as resolved.",
    "feedback_question": "Did the initial recommendation and expert assessment resolve your issue?",
    "feedback_subtext": "If not, you can request an on-site visit and continue the workflow.",
    "feedback_option_yes": "Yes",
    "feedback_yes": "Yes",
    "feedback_option_no": "No",
    "feedback_no": "No",
    "feedback_reason_label": "Reason for requesting a visit",
    "feedback_reason_placeholder": "Describe why you still need assistance...",
    "btn_confirm_resolved": "Confirm Resolved",
    "btn_request_visit": "Request Visit",
    "visit_requested_notice": "Your visit request was submitted successfully. The agriculturist will review your preferred schedules.",
    "reschedule_modal_title": "Request Reschedule",
    "reschedule_reason_label": "Reason",
    "reschedule_opt_emergency": "Emergency",
    "reschedule_opt_weather": "Bad weather",
    "reschedule_opt_conflict": "Personal conflict",
    "reschedule_opt_other": "Other",
    "reschedule_details_label": "Reason Details",
    "reschedule_details_placeholder": "Add more details...",
    "reschedule_btn_submit": "Submit Request",
    "reschedule_btn_submitting": "Submitting...",
    "reschedule_success": "Reschedule request submitted.",
    "alert_select_reason": "Please select a reason before submitting the reschedule request.",
    "alert_provide_details": "Please provide reason details for 'Other'.",
    "reschedule_offline_saved": "Offline Mode: Your reschedule request has been saved locally and will be automatically submitted once you regain connection.",
    "feedback_offline_saved": "Offline Mode: Your response has been saved locally and will be automatically submitted once your connection is restored.",
    "followup_offline_saved": "Offline Mode: Your follow-up notes have been saved locally and will be automatically submitted once you regain connection."
  },
  "pest_recommendations": {
    "tooltip_sanitation": "<strong>Step 1:</strong> Collect all dead leaves, rotting trunks, and fallen fruits.<br><strong>Step 2:</strong> Burn them or bury them deep away from healthy trees to destroy hidden pest breeding grounds.",
    "tooltip_pheromone": "<strong>Step 1:</strong> Hang the trap 1.5 to 2 meters high on a pole.<br><strong>Step 2:</strong> Place it at least 20-30 meters away from your healthy trees so it lures pests AWAY from your farm, not into it.",
    "tooltip_fungus": "Mix the recommended Green Muscardine fungus with water and spray directly onto compost pits, rotting logs, or traps where adult beetles lay eggs.",
    "tooltip_biological": "Introduce natural predators like earwigs or use organic biocontrol agents recommended by the local agriculture office.",
    "tooltip_light_trap": "Set up a bright light bulb over a basin of soapy water at night. Flying pests will be attracted to the light and drown in the water.",
    "tooltip_prune": "Use a clean, sharp bolo to cut off heavily infested fronds. Burn or bury the cut pieces immediately so pests don't spread to other leaves.",
    "tooltip_fertilizer": "Apply the recommended nitrogen or potassium fertilizers around the base of the tree (about 1 meter away from the trunk) to help the tree recover faster.",
    "tooltip_chemical": "<strong>WARNING:</strong> Only use chemicals as a final option. Wear gloves and a mask, follow the exact dosage on the bottle, and spray only on affected areas.<br><br><i>Note: If you are unsure about what chemical to use, ask the agriculturist by putting it in your Farmer Notes below before submitting.</i>",
    "tooltip_monitor": "Visit your farm every 3-5 days. Check the crown and young leaves of the affected trees for any new boreholes, chewed leaves, or pest droppings.",
    "tooltip_default": "Please follow this recommendation carefully. For exact measurements or detailed guidance, wait for the agriculturist's expert assessment."
  },
  "workflow_statuses": {
    "under_review": "Under Review",
    "assessment_issued": "Assessment Issued",
    "awaiting_confirmed_schedule": "Awaiting Confirmed Schedule",
    "visit_requested": "Visit Requested",
    "visit_scheduled": "Visit Scheduled",
    "visit_completed": "Visit Completed",
    "final_remarks_issued": "Final Remarks Issued",
    "resolved": "Resolved",
    "recommendation_issued": "Recommendation Issued",
    "ready_to_submit": "Ready to Submit",
    "offline_draft": "Offline Scan (Pending AI)",
    "draft": "Draft"
  },
  "pest_knowledge_base": {
    "pests": {
      "rhinoceros_beetle": "Rhinoceros Beetle",
      "brontispa": "Brontispa (Coconut Leaf Beetle)",
      "healthy_leaf": "Healthy Coconut Leaf",
      "unknown_pest": "Unknown Pest"
    },
    "risk_levels": {
      "high": "High",
      "medium": "Medium",
      "low": "Low"
    },
    "urgency_levels": {
      "high": "High",
      "medium": "Medium",
      "low": "Low"
    },
    "recommendations": {
      "initial_items": {
        "Prune and safely dispose of infested leaves": "Prune and safely dispose of infested leaves",
        "Maintain field sanitation and monitor infestation levels": "Maintain field sanitation and monitor infestation levels",
        "Release earwigs and Tetrastichus parasitoids for natural control": "Release earwigs and Tetrastichus parasitoids for natural control",
        "Spray white Muscardine fungus": "Spray white Muscardine fungus",
        "Use approved pesticide early morning for severe infestations": "Use approved pesticide early morning for severe infestations",
        "Improve farm sanitation and remove breeding sites": "Improve farm sanitation and remove breeding sites",
        "Install pheromone traps and green Muscardine fungus log traps": "Install pheromone traps and green Muscardine fungus log traps",
        "Apply biological treatment or use light traps at night": "Apply biological treatment or use light traps at night",
        "Monitor weekly and consult an agricultural technician for severe cases": "Monitor weekly and consult an agricultural technician for severe cases",
        "Continue regular monitoring": "Continue regular monitoring",
        "Maintain current sanitation practices": "Maintain current sanitation practices",
        "Inspect central spear leaves and unopened fronds weekly for early feeding streaks or browning edges.": "Inspect central spear leaves and unopened fronds weekly for early feeding streaks or browning edges.",
        "Maintain clean weed management and ensure adequate sunlight penetration and aeration around younger palms.": "Maintain clean weed management and ensure adequate sunlight penetration and aeration around younger palms.",
        "Carefully collect and safely compost or dispose of fallen, dried, or curled fronds to disrupt shelter sites.": "Carefully collect and safely compost or dispose of fallen, dried, or curled fronds to disrupt shelter sites.",
        "Preserve native beneficial predator populations (such as earwigs); avoid broad-spectrum chemical sprays.": "Preserve native beneficial predator populations (such as earwigs); avoid broad-spectrum chemical sprays.",
        "Improve general farm sanitation by clearing fallen decaying coconut logs, rotting wood, and compost heaps.": "Improve general farm sanitation by clearing fallen decaying coconut logs, rotting wood, and compost heaps.",
        "Inspect palm crowns and spear leaves regularly for characteristic V-shaped cuts or entry boreholes.": "Inspect palm crowns and spear leaves regularly for characteristic V-shaped cuts or entry boreholes.",
        "Install non-chemical perimeter light traps or organic pheromone monitoring traps to observe beetle activity.": "Install non-chemical perimeter light traps or organic pheromone monitoring traps to observe beetle activity.",
        "Avoid applying unverified chemical insecticides; await formal recommendations from your agricultural officer.": "Avoid applying unverified chemical insecticides; await formal recommendations from your agricultural officer.",
        "Maintain regular monthly orchard inspections to monitor tree crown vigor and spot any early pest arrivals.": "Maintain regular monthly orchard inspections to monitor tree crown vigor and spot any early pest arrivals.",
        "Ensure balanced soil fertilization and organic mulching to maintain natural tree resistance.": "Ensure balanced soil fertilization and organic mulching to maintain natural tree resistance.",
        "Keep palm bases clear of dense weeds and decaying organic litter.": "Keep palm bases clear of dense weeds and decaying organic litter.",
        "Record routine tree observation dates in your farm notebook or digital log.": "Record routine tree observation dates in your farm notebook or digital log.",
        "Ensure the camera is focused directly on a coconut leaf, frond, or crown section under daylight.": "Ensure the camera is focused directly on a coconut leaf, frond, or crown section under daylight.",
        "Hold the device steady and re-scan from approximately 1 to 2 feet away.": "Hold the device steady and re-scan from approximately 1 to 2 feet away.",
        "Avoid scanning non-plant objects, background scenery, or extremely blurry images.": "Avoid scanning non-plant objects, background scenery, or extremely blurry images."
      },
      "rhinoceros_beetle": [
        "Improve farm sanitation and remove breeding sites",
        "Install pheromone traps and green Muscardine fungus log traps",
        "Apply biological treatment or use light traps at night",
        "Monitor weekly and consult an agricultural technician for severe cases"
      ],
      "brontispa": [
        "Prune and safely dispose of infested leaves",
        "Maintain field sanitation and monitor infestation levels",
        "Release earwigs and Tetrastichus parasitoids for natural control",
        "Spray white Muscardine fungus",
        "Use approved pesticide early morning for severe infestations"
      ],
      "healthy_leaf": [
        "Continue regular monitoring",
        "Maintain current sanitation practices"
      ]
    },
    "risk_factors": {
      "rhinoceros_beetle": [
        "Decaying coconut wood nearby",
        "Unmanaged compost heaps",
        "High humidity with warm night temperatures",
        "History of previous infestation in nearby zones"
      ],
      "brontispa": [
        "Dense canopy without adequate airflow",
        "Young palms in nursery or early field stage",
        "Extended dry spells followed by sudden rain"
      ]
    },
    "tooltips": {
      "sanitation": "Step 1: Collect all dead leaves, rotting trunks, and fallen fruits. Step 2: Burn them or bury them deep away from healthy trees to destroy hidden pest breeding grounds.",
      "pheromone_trap": "Step 1: Hang the trap 1.5 to 2 meters high on a pole. Step 2: Place it at least 20-30 meters away from your healthy trees so it lures pests AWAY from your farm, not into it.",
      "muscardine_fungus": "Mix the recommended Green Muscardine fungus with water and spray directly onto compost pits, rotting logs, or traps where adult beetles lay eggs.",
      "biological_control": "Introduce natural predators like earwigs or use organic biocontrol agents recommended by the local agriculture office.",
      "light_trap": "Set up a bright light bulb over a basin of soapy water at night. Flying pests will be attracted to the light and drown in the water.",
      "pruning": "Use a clean, sharp bolo to cut off heavily infested fronds. Burn or bury the cut pieces immediately so pests don't spread to other leaves.",
      "fertilizer": "Apply the recommended nitrogen or potassium fertilizers around the base of the tree (about 1 meter away from the trunk) to help the tree recover faster.",
      "chemical_warning": "WARNING: Only use chemicals as a final option. Wear gloves and a mask, follow the exact dosage on the bottle, and spray only on affected areas.",
      "monitoring": "Visit your farm every 3-5 days. Check the crown and young leaves of the affected trees for any new boreholes, chewed leaves, or pest droppings.",
      "general": "Please follow this recommendation carefully. For exact measurements or detailed guidance, wait for the agriculturist's expert assessment."
    }
  },
  "backend_messages": {
    "report_submitted_success": "Your report was submitted and synchronized successfully!",
    "report_submitted_failure": "Unable to save report. Please try again.",
    "follow_up_success": "Your follow-up was submitted and the report was returned for review.",
    "follow_up_failure": "Unable to save follow-up.",
    "visit_reason_required": "Please provide a reason for requesting a visit.",
    "availability_shared": "Your available schedule options were shared with the agriculturist.",
    "availability_failure": "Unable to submit your availability.",
    "image_required": "No image uploaded",
    "image_invalid": "Invalid image file provided",
    "inference_failed": "AI model inference failed"
  }
},
    tl: {
  "_meta": {
    "role": "Farmer",
    "source_language": "en",
    "target_language": "tl",
    "description": "Tagalog translation dictionary for the Farmer role across CocoScan views, templates, JavaScript scripts, and backend endpoints."
  },
  "navigation": {
    "app_title": "CocoScan",
    "app_subtitle": "Pagtukoy sa Peste ng Niyog",
    "menu_section_main": "Pangunahing Menu",
    "menu_dashboard": "Dashboard",
    "menu_scan_pest": "Mag-scan ng Peste",
    "menu_drafts": "Mga Draft",
    "menu_my_reports": "Aking mga Ulat",
    "menu_profile": "Profile",
    "menu_settings": "Mga Setting",
    "user_role_farmer": "Magsasaka",
    "profile_modal_title": "Profile at mga Setting ng Magsasaka",
    "profile_role_farmer": "Rehistradong Magsasaka",
    "profile_sec_identity": "Impormasyon ng Magsasaka",
    "profile_sec_preferences": "Mabilisang mga Setting",
    "profile_sec_status": "Katayuan ng Device at Sync",
    "profile_lang_label": "Wika / Language",
    "profile_status_online": "Online at Naka-sync sa Cloud",
    "profile_status_offline": "Offline Mode (Lokal na Imbakan)",
    "profile_drafts_count": "Mga Naka-save na Field Draft",
    "profile_btn_refresh": "I-refresh ang Data ng App",
    "profile_btn_logout": "Mag-logout sa Account",
    "profile_logout_confirm": "Sigurado ka bang nais mong mag-logout sa CocoScan?",
    "profile_btn_close": "Isara",
    "btn_logout": "Mag-logout",
    "btn_go_back": "Bumalik",
    "switch_lang_title": "Wika: Tagalog (Pindutin para mag-English)",
    "lang_toggle_en": "EN",
    "lang_toggle_tl": "TL",
    "lang_preference": "Wika"
  },
  "pwa_and_offline": {
    "pwa_install_title": "I-install ang CocoScan App",
    "pwa_install_subtitle": "Ilagay sa Home Screen para sa mabilis at offline na paggamit",
    "pwa_install_btn": "I-install",
    "pwa_dismiss_btn": "Isara",
    "offline_portal_badge": "Aktibo ang Offline Mode ng CocoScan",
    "offline_portal_title": "Ikaw ay Offline",
    "offline_portal_desc": "Kasalukuyang walang koneksyon sa internet. Dahil sa CocoScan PWA, maaari ka pa ring mag-scan ng dahon sa sakahan at tingnan ang mga naka-save na draft kahit walang internet.",
    "offline_portal_btn_scanner": "Buksan ang Field Scanner",
    "offline_portal_btn_drafts": "Tingnan ang mga Offline Draft",
    "offline_portal_btn_dashboard": "Bumalik sa Farmer Dashboard",
    "offline_portal_btn_retry": "Subukan Muling Kumonekta",
    "offline_portal_btn_switch": "Magpalit ng Account",
    "offline_portal_checking": "Sinusuri ang koneksyon...",
    "offline_portal_restored": "Naibalik na ang koneksyon!",
    "offline_portal_still_offline": "Offline Pa Rin",
    "offline_portal_footer": "Awtomatikong ise-save ang mga field scan sa iyong telepono hanggang sa magkaroon muli ng signal."
  },
  "dashboard": {
    "page_title": "Dashboard ng Magsasaka",
    "page_subtitle": "Pangkalahatang-ideya ng iyong mga naiulat at natukoy na peste",
    "greeting_morning": "Magandang Umaga, {name}!",
    "greeting_afternoon": "Magandang Hapon, {name}!",
    "greeting_evening": "Magandang Gabi, {name}!",
    "greeting_welcome": "Maligayang pagbabalik, {name}!",
    "greeting_dashboard": "Dashboard",
    "banner_offline_title": "Aktibo ang Offline Access",
    "banner_offline_desc": "Maaari kang mag-scan at mag-save ng mga draft kahit walang koneksyon sa internet.",
    "banner_offline_action": "Buksan ang Scanner",
    "modal_offline_ready_badge": "Aktibo ang Offline Mode",
    "modal_offline_ready_title": "Handa na ang Offline Access",
    "modal_offline_ready_desc": "Ikaw ay offline, ngunit maaari mo pa ring gamitin ang CocoScan; ise-save ito sa drafts at maaari mong buksan muli mamaya.",
    "modal_offline_btn_scan": "Simulan ang Pag-scan ng Peste",
    "modal_offline_btn_continue": "Magpatuloy sa Dashboard",
    "metric_total_cases": "Kabuuang Naiulat na Kaso",
    "metric_total_subtext": "Lahat ng Naipasa",
    "metric_pending_cases": "Nakabinbin",
    "metric_pending_subtext": "Naghihintay ng Pagsusuri",
    "metric_resolved_cases": "Nalutas Na",
    "metric_resolved_subtext": "Solusyon ng Eksperto",
    "quick_action_title": "Mag-scan Ngayon",
    "quick_action_desc": "Mag-upload ng larawan ng dahon para sa awtomatikong pagsusuri.",
    "quick_action_btn": "Buksan ang Scanner",
    "notif_center_title": "Mga Abiso",
    "notif_btn_clear_all": "I-clear Lahat",
    "notif_btn_mute": "I-mute",
    "notif_btn_unmute": "I-unmute",
    "notif_empty_title": "Walang Bagong Abiso",
    "notif_empty_desc": "Lahat ng iyong ulat sa peste at iskedyul ng pagbisita ay updated.",
    "notif_toast_muted": "Naka-mute ang mga abiso",
    "notif_toast_unmuted": "Aktibo ang mga abiso",
    "notif_toast_cleared": "Na-clear ang lahat ng abiso",
    "notif_badge_updates": "{count} na abiso",
    "notif_badge_update_one": "1 abiso",
    "notif_badge_empty": "0 abiso",
    "notif_tag_diagnosis": "Pagsusuri",
    "notif_tag_resolved": "Naresolba",
    "notif_tag_visit": "Pagbisita",
    "notif_tag_chat": "Usapan",
    "notif_title_reco": "Pagsusuri ng Eksperto: {pest}",
    "notif_title_resolved": "Naresolbang Ulat: {pest}",
    "notif_desc_reco": "Naglabas ang eksperto ng mga rekomendasyon para sa iyong pananim.",
    "notif_desc_resolved": "Nakumpirma ang lunas at naisara na ang ulat.",
    "notif_title_visit_confirmed": "Kumpirmadong Pagbisita: #{id}",
    "notif_title_visit_scheduled": "Naiskedyul na Pagbisita: #{id}",
    "notif_desc_visit": "Kinumpirma ng agriculturist ang iskedyul ng pagbisita sa iyong sakahan.",
    "notif_title_chat": "Bagong Mensahe: #{id}",
    "notif_desc_chat": "{count} mensahe sa iyong usapan sa pagbisita.",
    "notif_action_view": "Tingnan ang Ulat",
    "notif_btn_dismiss": "Alisin",
    "push_consent_title": "Paganahin ang mga Abiso?",
    "push_consent_desc": "Makatanggap ng agarang alerto sa iyong telepono para sa pagsusuri ng eksperto, kumpirmadong petsa ng pagbisita, at mga tugon sa mensahe.",
    "push_consent_btn_enable": "Oo, Paganahin ang Abiso",
    "push_consent_btn_mute": "Huwag Muna / I-mute",
    "push_consent_feature_reco": "Pagsusuri ng eksperto at mga rekomendasyon sa gamot",
    "push_consent_feature_visit": "Iskedyul ng pagbisita sa sakahan at mga paalala",
    "push_consent_feature_chat": "Agarang tugon sa iyong mga katanungan"
  },
  "weather_widget": {
    "title": "Kasalukuyang Panahon",
    "stat_temperature": "Temperatura",
    "stat_humidity": "Halumigmig",
    "stat_rainfall": "Pag-ulan",
    "stat_wind": "Hangin",
    "label_temperature": "Temperatura",
    "label_humidity": "Halumigmig",
    "label_rainfall": "Pag-ulan",
    "label_wind": "Hangin",
    "status_offline": "Offline",
    "alert_offline": "Hindi makuha ang lagay ng panahon ngayon. Pakitingnan ang iyong koneksyon.",
    "risk_high_level": "Mataas na Panganib",
    "risk_high": "Mataas na Panganib",
    "risk_high_desc": "Mabilis ang pagdami ng Brontispa at Rhinoceros Beetle sa ganitong panahon. Suriin agad ang mga murang dahon.",
    "risk_high_text": "Mabilis ang pagdami ng Brontispa at Rhinoceros Beetle sa ganitong panahon. Suriin agad ang mga murang dahon.",
    "risk_moderate_level": "Katamtamang Panganib",
    "risk_moderate": "Katamtamang Panganib",
    "risk_moderate_rhino_text": "Ang mataas na halumigmig ay paborableng pamugaran ng Rhinoceros Beetle at ng kanilang mga uod.",
    "risk_desc_moisture": "Ang mataas na halumigmig ay paborableng pamugaran ng Rhinoceros Beetle at ng kanilang mga uod.",
    "risk_moderate_brontispa_text": "Ang mainit at tuyong dahon ay nagpapabilis sa pagpisa ng mga itlog ng Brontispa.",
    "risk_desc_dry": "Ang mainit at tuyong dahon ay nagpapabilis sa pagpisa ng mga itlog ng Brontispa.",
    "risk_moderate_general_text": "Aktibo ang pagsubaybay sa lagay ng kapaligiran.",
    "risk_desc_monitoring": "Aktibo ang pagsubaybay sa lagay ng kapaligiran.",
    "risk_low_level": "Mababang Panganib",
    "risk_low": "Mababang Panganib",
    "risk_low_desc": "Ang kasalukuyang panahon ay hindi paborable sa mabilis na pagdami ng peste.",
    "risk_low_text": "Ang kasalukuyang panahon ay hindi paborable sa mabilis na pagdami ng peste.",
    "risk_desc_stable": "Ang kasalukuyang panahon ay hindi paborable sa mabilis na pagdami ng peste.",
    "risk_unavailable": "Hindi magagamit ang pagsusuri sa panganib offline."
  },
  "scan_page": {
    "page_title": "Tukuyin ang Peste",
    "page_subtitle": "Pinapagana ng Image Recognition",
    "drop_zone_title": "I-scan o i-upload ang dahon ng niyog",
    "drop_zone_subtext": "I-scan o i-upload ang dahon ng niyog",
    "drop_zone_subtitle": "I-scan o i-upload ang dahon ng niyog",
    "btn_use_camera": "Gamitin ang Kamera",
    "btn_upload_photo": "Mag-upload ng Larawan",
    "gps_helper_text": "Awtomatikong kinukuha ng kamera ang live GPS, habang ang in-upload na larawan ay gumagamit ng manual o map pin na lokasyon.",
    "gps_help_text": "Awtomatikong kinukuha ng kamera ang live GPS, habang ang in-upload na larawan ay gumagamit ng manual o map pin na lokasyon.",
    "gps_unavailable_notice": "Hindi available ang GPS sa device na ito. Minarkahan ang lokasyon bilang unavailable.",
    "tips_title": "Mga Gabay para sa Pinakamagandang Resulta",
    "tip_1": "Gumamit ng magandang kondisyon ng liwanag",
    "tips_item1": "Gumamit ng magandang kondisyon ng liwanag",
    "tip_2": "I-focus sa apektadong bahagi ng dahon",
    "tips_item2": "I-focus sa apektadong bahagi ng dahon",
    "tip_3": "Kunin ang buong dahon kung maaari",
    "tips_item3": "Kunin ang buong dahon kung maaari",
    "tip_4": "Iwasan ang malalabong larawan",
    "tips_item4": "Iwasan ang malalabong larawan",
    "history_logs_title": "Mga Kamakailang Tala ng Scan",
    "history_panel_title": "Mga Kamakailang Tala ng Scan",
    "history_empty_title": "Walang kamakailang tala ng scan",
    "history_empty_desc": "Dito makikita ang iyong mga nakaraang scan kapag nagsimula kang mag-diagnose ng dahon.",
    "history_timestamp_unavailable": "Hindi makuha ang petsa/oras",
    "location_modal_title": "Itakda ang Lokasyon ng Puno",
    "location_modal_desc": "Upang matiyak ang katumpakan ng ulat, ilagay ang lokasyon ng sakahan o i-tap ang mapa upang i-pin ang puno ng niyog.",
    "loc_modal_title": "Itakda ang Lokasyon ng Puno",
    "loc_modal_desc": "Upang matiyak ang katumpakan ng ulat, ilagay ang lokasyon ng sakahan o i-tap ang mapa upang i-pin ang puno ng niyog.",
    "loc_label_farm": "Lokasyon ng Sakahan / Barangay",
    "loc_btn_use_gps": "Gamitin ang Kasalukuyang GPS",
    "loc_input_placeholder": "San Nicolas, San Pablo City",
    "loc_map_pin_label": "I-tap o I-drag ang Pin sa Mapa",
    "loc_detected_badge": "Natukoy na lokasyon",
    "loc_btn_cancel": "Kanselahin",
    "loc_btn_confirm_scan": "Scan Now",
    "location_input_label": "Lokasyon ng Sakahan / Barangay",
    "location_btn_current_gps": "Gamitin ang Kasalukuyang GPS",
    "location_placeholder": "San Nicolas, San Pablo City",
    "location_map_label": "I-tap o I-drag ang Pin sa Mapa",
    "location_detected_badge": "Natukoy na lokasyon",
    "btn_cancel": "Kanselahin",
    "btn_confirm_and_scan": "Scan Now",
    "offline_modal_title": "Na-save sa Lokal na Drafts",
    "offline_modal_desc": "Ikaw ay kasalukuyang offline. Ligtas na na-save ang iyong larawan sa drafts ng iyong telepono. Pagbalik ng internet, buksan ang pahina ng Drafts upang i-scan gamit ang AI at ipasa ang ulat.",
    "offline_saved_title": "Na-save sa Lokal na Drafts",
    "offline_saved_desc": "Ikaw ay kasalukuyang offline. Ligtas na na-save ang iyong larawan sa drafts ng iyong telepono. Pagbalik ng internet, buksan ang pahina ng Drafts upang i-scan gamit ang AI at ipasa ang ulat.",
    "offline_saved_btn_view_drafts": "Tingnan ang mga Naka-save na Draft",
    "offline_saved_btn_another": "Mag-upload / Mag-scan ng Iba Pa",
    "btn_view_saved_drafts": "Tingnan ang mga Naka-save na Draft",
    "btn_scan_another": "Mag-upload / Mag-scan ng Iba Pa",
    "loading_title": "Sinusuri ang Larawan...",
    "loading_subtitle": "Pinoproseso ang pagsusuri ng AI",
    "mobile_access_required_title": "Kailangan ng Smartphone",
    "mobile_restriction_title": "Kailangan ng Smartphone",
    "mobile_access_required_desc": "Maaari mong buksan ang dashboard sa anumang device, ngunit ang Pag-scan ng Peste ay nangangailangan ng smartphone upang magamit ang kamera sa sakahan.",
    "mobile_restriction_desc": "Maaari mong buksan ang dashboard sa anumang device, ngunit ang Pag-scan ng Peste ay nangangailangan ng smartphone upang magamit ang kamera sa sakahan.",
    "alert_select_photo": "Mangyaring kumuha o pumili ng larawan ng dahon ng niyog bago mag-scan.",
    "alert_validation_notice": "Abiso sa Pagsusuri ng Larawan: ",
    "alert_gps_failed": "Hindi makuha ang GPS ng device: ",
    "alert_location_required": "Mangyaring maglagay ng lokasyon o mag-pin sa mapa.",
    "alert_offline_save_prompt": "Hindi makakonekta sa AI Scanner. Nais mo bang i-save ang larawang ito bilang offline draft upang iproseso mamaya?",
    "alert_discard_session": "Sigurado ka bang nais mong itapon ang scan na ito? Mawawala ang mga inilagay na datos.",
    "alert_notes_required": "Mangyaring maglagay ng iyong tala bago ipasa ang ulat.",
    "alert_no_network_save_draft": "Walang koneksyon sa internet. I-save na lamang ba bilang draft?",
    "alert_submit_success": "TAGUMPAY: Matagumpay na naipasa ang ulat para sa {pest}.",
    "alert_submit_failed_save_draft": "Hindi ma-sync ang ulat ngayon. I-save na lamang ba bilang draft?"
  },
  "drafts_page": {
    "page_title": "Mga Naka-save na Draft",
    "page_subtitle": "Ipagpatuloy, ipasa, o tanggalin ang iyong mga naka-save na ulat ng field scan.",
    "btn_refresh": "I-refresh ang Pahina",
    "empty_title": "Walang Naka-save na Draft",
    "empty_desc": "Wala ka pang naka-save na draft scan. Pumunta sa pahina ng Mag-scan ng Peste upang simulan ang iyong unang ulat.",
    "offline_scan_title": "Offline Scan",
    "badge_pending_ai": "Naghihintay sa Pagscan",
    "badge_scanned": "Na-scan Na",
    "label_captured": "Kinuha noong:",
    "label_saved": "Na-save noong:",
    "label_gps": "GPS",
    "label_notes": "Mga Tala",
    "label_no_notes": "Walang inilagay na tala",
    "no_notes": "Walang inilagay na tala",
    "btn_continue_edit": "Ipagpatuloy",
    "btn_scan": "I-scan",
    "btn_delete_draft": "Burahin ang Draft",
    "btn_save_changes": "I-save ang mga Pagbabago",
    "btn_saving_changes": "Inise-save ang mga Pagbabago...",
    "alert_confirm_delete": "Sigurado ka bang nais mong burahin ang naka-save na draft na ito?",
    "alert_draft_saved_online": "Matagumpay na na-save ang draft!",
    "alert_draft_saved_offline": "Na-save ang scan bilang Offline Draft! Pagkakaroon ng internet, buksan ang Drafts page upang patakbuhin ang AI at ipasa ang ulat.",
    "alert_connect_to_scan": "Kinakailangan ng koneksyon sa internet upang masuri ng AI ang peste. Kumonekta sa internet upang ma-scan ang draft.",
    "alert_scanning_in_progress": "Nagsasagawa ng scan...",
    "alert_changes_saved": "Matagumpay na na-save ang mga pagbabago sa draft.",
    "draft_not_found": "Hindi nahanap ang draft.",
    "unable_load_draft": "Hindi ma-load ang draft."
  },
  "reports_page": {
    "page_title": "Aking mga Ulat",
    "page_subtitle": "Pangkalahatang mga naipasa na ulat",
    "banner_offline_title": "Offline Mode • Lokal na Ulat",
    "banner_offline_desc": "Naka-sync ang mga ulat at maglo-load kapag may koneksyon na sa internet.",
    "banner_offline_badge": "Naka-cache",
    "offline_banner_title": "Offline Mode • Lokal na Ulat",
    "offline_banner_desc": "Naka-sync ang mga ulat at maglo-load kapag may koneksyon na sa internet.",
    "offline_cached_badge": "Naka-cache",
    "filter_all": "Lahat",
    "filter_status": "Katayuan ▾",
    "filter_pest": "Peste ▾",
    "filter_all_statuses": "Lahat ng Katayuan",
    "filter_all_pests": "Lahat ng Peste",
    "filter_calendar_title": "Salain ayon sa petsa",
    "filter_by_date": "Salain ayon sa petsa",
    "btn_clear_filters": "Burahin ang mga Filter",
    "clear_filters": "Burahin ang mga Filter",
    "btn_refresh": "I-refresh ang Pahina",
    "empty_title": "Walang Nahanap na Ulat",
    "empty_desc": "Walang rekord na tumutugma sa iyong filter o hinahanap. Subukang baguhin ang iyong paghahanap.",
    "empty_offline_title": "Pag-sync ng mga Offline na Ulat",
    "empty_offline_desc": "Naka-sync ang mga ulat at maglo-load kapag may aktibong koneksyon na sa internet.",
    "pagination_showing": "Ipinapakita ang {start}–{end} ng {total}",
    "pagination_prev": "← Nakaraan",
    "pagination_next": "Susunod →",
    "badge_unread": "{count} bago",
    "followup_title": "Detalye ng Follow-up",
    "followup_detected_pest": "Natukoy na Peste:",
    "followup_confidence": "Antas ng Katiyakan:",
    "followup_damage": "Pinsala:",
    "followup_orig_notes": "Orihinal na Tala:",
    "fup_modal_title": "Detalye ng Follow-up",
    "fup_detected_pest": "Natukoy na Peste:",
    "fup_confidence": "Antas ng Katiyakan:",
    "fup_damage": "Pinsala:",
    "fup_original_notes": "Orihinal na Tala:",
    "fup_upload_title": "Mag-upload ng Bagong Larawan ng Dahon",
    "fup_upload_desc": "Kumuha ng update na larawan ng dahon",
    "fup_btn_take_photo": "Kumuha ng Larawan",
    "fup_btn_upload_image": "Mag-upload ng Larawan",
    "fup_progress_notes_title": "Tala sa Pag-unlad ng Gamutan",
    "fup_progress_notes_placeholder": "Isulat dito ang karagdagang tala sa isinagawang gamutan...",
    "fup_btn_submit": "Ipasa ang Follow-up",
    "fup_btn_submitting": "Ipinapasa ang Follow-up...",
    "fup_success": "Matagumpay na naipasa ang follow-up.",
    "fup_failed": "Hindi maipasa ang follow-up sa ngayon."
  },
  "report_modal": {
    "modal_title": "Buod ng Ulat",
    "summary_title": "Buod ng Ulat",
    "btn_print": "I-print ang ulat",
    "btn_close": "Isara",
    "label_status": "Katayuan:",
    "status_label": "Katayuan:",
    "label_confidence": "Antas ng Katiyakan:",
    "confidence_label": "Antas ng Katiyakan:",
    "label_farmer": "Magsasaka:",
    "farmer_label": "Magsasaka:",
    "label_location": "Lokasyon:",
    "location_label": "Lokasyon:",
    "label_scanned": "Petsa ng Pag-scan:",
    "scanned_label": "Petsa ng Pag-scan:",
    "label_reason": "Dahilan",
    "label_outcome": "Kinahinatnan",
    "notes_card_title": "Mga Tala ng Magsasaka",
    "farmer_notes_title": "Mga Tala ng Magsasaka",
    "notes_card_placeholder": "Ilarawan ang iyong napansin sa puno ng niyog (hal., paninilaw ng dahon, sirang bunga, di-karaniwang insekto, o iba pang palatandaan).",
    "farmer_notes_placeholder": "Ilarawan ang iyong napansin sa puno ng niyog (hal., paninilaw ng dahon, sirang bunga, di-karaniwang insekto, o iba pang palatandaan).",
    "notes_empty": "Walang inilagay na tala.",
    "initial_reco_title": "Paunang mga Rekomendasyon",
    "verified_reco_title": "Mga Rekomendasyon",
    "initial_reco_desc": "Pangkalahatang gabay para sa natukoy na peste upang matulungan ka sa agarang aksyon.",
    "initial_reco_subtext": "Pindutin ang question mark icon para sa karagdagang detalye.",
    "initial_reco_tooltip_prompt": "Pindutin ang question mark icon para sa karagdagang detalye.",
    "initial_reco_empty": "Wala pang available na paunang rekomendasyon.",
    "supporting_photos_title": "Karagdagang Larawan (opsyonal)",
    "supporting_photos_tap": "Magdagdag ng Larawan",
    "supporting_photos_prompt": "Magdagdag ng Larawan",
    "supporting_photos_subtext": "Pindutin para buksan ang gallery ng iyong telepono",
    "supporting_photos_error": "Hanggang 3 karagdagang larawan lamang ang maaaring i-upload.",
    "supporting_photos_max_error": "Hanggang 3 karagdagang larawan lamang ang maaaring i-upload.",
    "additional_images_title": "Mga Karagdagang Larawan",
    "additional_images_empty": "Walang karagdagang larawang na-upload.",
    "expert_assessment_title": "Pagsusuri ng Eksperto",
    "expert_assessment_empty": "Wala pang available na pagsusuri mula sa eksperto.",
    "expert_assessment_prompt": "Ipasa ang ulat para sa pagsusuri ng eksperto",
    "expert_assessment_issued": "Naibigay na ang pagsusuri ng eksperto.",
    "expert_issued_by": "Isinuri ni {name}",
    "btn_submit_report": "Ipasa ang Ulat",
    "btn_submitting_report": "Ipinapasa ang ulat…",
    "btn_cancel_report": "Kanselahin",
    "followup_card_title": "Follow-up",
    "followup_section_title": "Follow-up",
    "discussion_toggle_title": "Talakayan sa Kahilingan sa Pagbisita",
    "discussion_messages_count": "{count} mensahe",
    "discussion_message_singular": "mensahe",
    "discussion_message_plural": "mensahe",
    "discussion_empty": "Wala pang mga mensahe sa talakayan.",
    "discussion_placeholder": "Mag-type ng mensahe para sumagot...",
    "discussion_btn_send": "Ipadala",
    "discussion_tip_reschedule": "Tip: Pindutin ang 'Talakayan sa Kahilingan sa Pagbisita' upang mag-usap at magkasundo sa bagong petsa at oras.",
    "discussion_closed": "Isinara na ang talakayan sa pag-iskedyul.",
    "btn_request_reschedule": "Humiling ng Bagong Iskedyul",
    "resolution_details_title": "Mga Detalye ng Paglutas",
    "report_summary_resolution_title": "Resolusyon ng Buod ng Ulat",
    "schedule_new_confirmed": "Kumpirmado ang Bagong Iskedyul",
    "schedule_confirmed_prefix": "Kumpirmado:",
    "schedule_previous_prefix": "Nakaraang Iskedyul:",
    "schedule_from": "mula",
    "schedule_to": "hanggang",
    "resolution_outcome_text": "Kinahinatnan: Nalutas ang isyu sa pamamagitan ng pagsunod sa pagsusuri ng eksperto.",
    "resolution_resolved_on": "Nalutas Noong:",
    "resolution_expert_assessment_label": "Ibinigay na Pagsusuri ng Eksperto:",
    "resolution_visit_completed_text": "Nakumpleto na ng agriculturist ang pagbisita at minarkahang nalutas na ang isyu.",
    "feedback_question": "Nalutas ba ng paunang rekomendasyon at pagsusuri ng eksperto ang iyong problema sa peste?",
    "feedback_subtext": "Kung hindi, maaari kang humiling ng aktwal na pagbisita ng agriculturist sa iyong sakahan.",
    "feedback_option_yes": "Oo",
    "feedback_yes": "Oo",
    "feedback_option_no": "Hindi",
    "feedback_no": "Hindi",
    "feedback_reason_label": "Dahilan kung bakit humihiling ng pagbisita",
    "feedback_reason_placeholder": "Ilarawan kung bakit kailangan mo pa rin ng tulong sa sakahan...",
    "btn_confirm_resolved": "Kumpirmahing Nalutas Na",
    "btn_request_visit": "Humiling ng Pagbisita",
    "visit_requested_notice": "Matagumpay na naipasa ang kahilingan sa pagbisita. Susuriin ng agriculturist ang iyong mga inilagay na oras.",
    "reschedule_modal_title": "Humiling ng Bagong Iskedyul",
    "reschedule_reason_label": "Dahilan",
    "reschedule_opt_emergency": "Kagipitan / Emergency",
    "reschedule_opt_weather": "Masamang panahon",
    "reschedule_opt_conflict": "May ibang mahalagang lakad",
    "reschedule_opt_other": "Iba pa",
    "reschedule_details_label": "Paliwanag sa Dahilan",
    "reschedule_details_placeholder": "Maglagay ng karagdagang paliwanag...",
    "reschedule_btn_submit": "Ipasa ang Kahilingan",
    "reschedule_btn_submitting": "Ipinapasa...",
    "reschedule_success": "Naipasa na ang kahilingan para sa bagong iskedyul.",
    "alert_select_reason": "Mangyaring pumili ng dahilan bago ipasa ang kahilingan.",
    "alert_provide_details": "Mangyaring magbigay ng paliwanag para sa 'Iba pa'.",
    "reschedule_offline_saved": "Offline Mode: Ang iyong kahilingan para sa bagong iskedyul ay na-save sa device at awtomatikong ipapadala kapag nagkaroon ng koneksyon.",
    "feedback_offline_saved": "Offline Mode: Ang iyong tugon ay na-save sa device at awtomatikong ipapadala kapag nagkaroon ng koneksyon.",
    "followup_offline_saved": "Offline Mode: Ang iyong follow-up ay na-save sa device at awtomatikong ipapadala kapag nagkaroon ng koneksyon."
  },
  "pest_recommendations": {
    "tooltip_sanitation": "<strong>Hakbang 1:</strong> Tipunin ang lahat ng tuyong dahon, nabubulok na puno, at laglag na bunga.<br><strong>Hakbang 2:</strong> Sunugin o ibaon nang malalim malayo sa malulusog na puno upang masira ang pinamumugaran ng peste.",
    "tooltip_pheromone": "<strong>Hakbang 1:</strong> Isabit ang bitag 1.5 hanggang 2 metro ang taas sa poste.<br><strong>Hakbang 2:</strong> Ilagay ito nang 20-30 metro ang layo sa malulusog na puno upang ilayo ang peste sa sakahan.",
    "tooltip_fungus": "Ihalo ang inirekomendang Green Muscardine fungus sa tubig at direktang i-spray sa compost pits o nabubulok na kahoy kung saan nangingitlog ang mga salagubang.",
    "tooltip_biological": "Magpakawala ng natural na kaaway ng peste gaya ng earwigs o gumamit ng aprubadong organikong pamatay mula sa tanggapan ng agrikultura.",
    "tooltip_light_trap": "Maglagay ng maliwanag na bumbilya sa ibabaw ng plangganang may tubig at sabon sa gabi upang maakit at malunod ang mga lumilipad na salagubang.",
    "tooltip_prune": "Gamit ang matalas at malinis na itak, putulin ang matinding napinsalang dahon. Sunugin o ibaon agad ang mga naputol na bahagi upang hindi lumipat sa ibang dahon.",
    "tooltip_fertilizer": "Maglagay ng inirekomendang pataba (nitrogen o potassium) sa paligid ng puno (mga 1 metro mula sa puno) upang mapabilis ang pagbawi nito.",
    "tooltip_chemical": "<strong>BABALA:</strong> Gamitin lamang ang kemikal bilang huling paraan. Magsuot ng guwantes at mask, sundin ang tamang timpla sa bote, at i-spray lamang sa may sira.<br><br><i>Paunawa: Kung hindi sigurado sa kemikal na gagamitin, magtanong sa agriculturist sa pamamagitan ng paglalagay nito sa iyong Mga Tala ng Magsasaka sa ibaba bago ipasa.</i>",
    "tooltip_monitor": "Bisitahin ang sakahan kada 3-5 araw. Suriin ang itaas at murang dahon para sa mga bagong butas, ngatngat, o dumi ng insekto.",
    "tooltip_default": "Mangyaring sundin ang rekomendasyong ito nang maingat. Para sa eksaktong sukat o detalyadong gabay, maghintay sa pagsusuri ng agriculturist."
  },
  "workflow_statuses": {
    "under_review": "Kasalukuyang Sinusuri",
    "assessment_issued": "Naibigay na ang Pagsusuri",
    "awaiting_confirmed_schedule": "Naghihintay ng Kumpirmadong Iskedyul",
    "visit_requested": "Humiling ng Pagbisita",
    "visit_scheduled": "Nai-iskedyul ang Pagbisita",
    "visit_completed": "Natapos ang Pagbisita",
    "final_remarks_issued": "May Panghuling Puna Na",
    "resolved": "Nalutas Na",
    "recommendation_issued": "Naibigay na ang Rekomendasyon",
    "ready_to_submit": "Handa nang Ipasa",
    "offline_draft": "Offline Scan (Naghihintay sa Pagscan)",
    "draft": "Draft"
  },
  "pest_knowledge_base": {
    "pests": {
      "rhinoceros_beetle": "Salagubang / Oyang (Rhinoceros Beetle)",
      "brontispa": "Brontispa (Coconut Leaf Beetle)",
      "healthy_leaf": "Malusog na Dahon ng Niyog",
      "unknown_pest": "Hindi Matukoy na Peste"
    },
    "risk_levels": {
      "high": "Mataas",
      "medium": "Katamtaman",
      "low": "Mababa"
    },
    "urgency_levels": {
      "high": "Mataas",
      "medium": "Katamtaman",
      "low": "Mababa"
    },
    "recommendations": {
      "initial_items": {
        "Prune and safely dispose of infested leaves": "Putulin at ligtas na sunugin o ibaon ang mga apektadong dahon",
        "Maintain field sanitation and monitor infestation levels": "Panatilihin ang kalinisan ng sakahan at subaybayan ang dami ng peste",
        "Release earwigs and Tetrastichus parasitoids for natural control": "Magpakawala ng earwigs at Tetrastichus parasitoids para sa natural na pagpuksa",
        "Spray white Muscardine fungus": "Mag-spray ng white Muscardine fungus",
        "Use approved pesticide early morning for severe infestations": "Gumamit ng aprubadong pamatay-peste sa madaling araw kapag labis na ang pamemeste",
        "Improve farm sanitation and remove breeding sites": "Pabutihin ang kalinisan ng sakahan at alisin ang mga pinamumugaran",
        "Install pheromone traps and green Muscardine fungus log traps": "Magkabit ng mga pheromone trap at green Muscardine fungus log trap",
        "Apply biological treatment or use light traps at night": "Maglapat ng biological treatment o gumamit ng light trap sa gabi",
        "Monitor weekly and consult an agricultural technician for severe cases": "Subaybayan linggu-linggo at sumangguni sa agricultural technician kapag malala ang kaso",
        "Continue regular monitoring": "Ipagpatuloy ang regular na pagsubaybay",
        "Maintain current sanitation practices": "Panatilihin ang kasalukuyang gawi sa kalinisan",
        "Inspect central spear leaves and unopened fronds weekly for early feeding streaks or browning edges.": "Suriin linggu-linggo ang mga gitnang ubod at hindi pa bumubukas na palapa para sa mga unang bakas ng pagkain ng uod o pangingitim ng gilid.",
        "Maintain clean weed management and ensure adequate sunlight penetration and aeration around younger palms.": "Panatilihing malinis ang damo sa paligid at tiyaking nasisikatan ng araw at mahahanginan ang mga nakababatang puno.",
        "Carefully collect and safely compost or dispose of fallen, dried, or curled fronds to disrupt shelter sites.": "Maingat na tipunin at ligtas na ibaon o linisin ang mga nalaglag, tuyo, o nakarolyong palapa upang sirain ang pamugaran ng peste.",
        "Preserve native beneficial predator populations (such as earwigs); avoid broad-spectrum chemical sprays.": "Pangalagaan ang mga likas na kaibigang insekto (tulad ng mga earwig); iwasan ang pag-spray ng matatapang na kemikal.",
        "Improve general farm sanitation by clearing fallen decaying coconut logs, rotting wood, and compost heaps.": "Pabutihin ang kalinisan ng sakahan sa pamamagitan ng pag-alis ng mga nabubulok na troso ng niyog, bulok na kahoy, at bunton ng compost.",
        "Inspect palm crowns and spear leaves regularly for characteristic V-shaped cuts or entry boreholes.": "Regular na suriin ang tuktok ng puno at mga ubod para sa mga natatanging V-shaped na hiwa o butas na pinasukan ng uwang.",
        "Install non-chemical perimeter light traps or organic pheromone monitoring traps to observe beetle activity.": "Maglagay ng mga light trap o organic na pheromone trap sa paligid upang masubaybayan ang paglipad ng mga uwang.",
        "Avoid applying unverified chemical insecticides; await formal recommendations from your agricultural officer.": "Iwasan ang paggamit ng hindi beripikadong kemikal na pestisidyo; hintayin ang opisyal na rekomendasyon mula sa agriculturist.",
        "Maintain regular monthly orchard inspections to monitor tree crown vigor and spot any early pest arrivals.": "Magsagawa ng regular na buwanang pag-iinspeksyon sa sakahan upang subaybayan ang sigla ng puno at maagang mapansin ang peste.",
        "Ensure balanced soil fertilization and organic mulching to maintain natural tree resistance.": "Tiyakin ang balanseng pataba sa lupa at paglalagay ng organic mulch upang mapanatili ang likas na resistensya ng puno.",
        "Keep palm bases clear of dense weeds and decaying organic litter.": "Panatilihing malinis ang paanan ng puno mula sa makakapal na damo at nabubulok na dumi.",
        "Record routine tree observation dates in your farm notebook or digital log.": "Itala ang mga petsa ng regular na pagmamasid sa inyong talaan o digital log.",
        "Ensure the camera is focused directly on a coconut leaf, frond, or crown section under daylight.": "Tiyaking nakatutok ang camera sa dahon, palapa, o tuktok ng puno ng niyog sa ilalim ng liwanag ng araw.",
        "Hold the device steady and re-scan from approximately 1 to 2 feet away.": "Hawakan nang matatag ang camera at kumuha muli sa layong 1 hanggang 2 talampakan.",
        "Avoid scanning non-plant objects, background scenery, or extremely blurry images.": "Iwasang kumuha ng litrato ng mga bagay na hindi halaman, tanawin sa paligid, o malabong larawan."
      },
      "rhinoceros_beetle": [
        "Pabutihin ang kalinisan ng sakahan at alisin ang mga pinamumugaran",
        "Magkabit ng mga pheromone trap at green Muscardine fungus log trap",
        "Maglapat ng biological treatment o gumamit ng light trap sa gabi",
        "Subaybayan linggu-linggo at sumangguni sa agricultural technician kapag malala ang kaso"
      ],
      "brontispa": [
        "Putulin at ligtas na sunugin o ibaon ang mga apektadong dahon",
        "Panatilihin ang kalinisan ng sakahan at subaybayan ang dami ng peste",
        "Magpakawala ng earwigs at Tetrastichus parasitoids para sa natural na pagpuksa",
        "Mag-spray ng white Muscardine fungus",
        "Gumamit ng aprubadong pamatay-peste sa madaling araw kapag labis na ang pamemeste"
      ],
      "healthy_leaf": [
        "Ipagpatuloy ang regular na pagsubaybay",
        "Panatilihin ang kasalukuyang gawi sa kalinisan"
      ]
    },
    "risk_factors": {
      "rhinoceros_beetle": [
        "Maruming sakahan",
        "Mga nabubulok na troso",
        "Pamugaran ng insekto",
        "Mainit na temperatura sa gabi",
        "Malakas na hangin",
        "Dating napeste na puno"
      ],
      "brontispa": [
        "Lugar ng punlaan (Nursery)",
        "Makapal na halaman",
        "Malamig at malilim na kapaligiran",
        "Kakulangan sa kalinisan",
        "Dating napeste na puno"
      ]
    },
    "tooltips": {
      "sanitation": "Hakbang 1: Tipunin ang lahat ng tuyong dahon, nabubulok na puno, at laglag na bunga. Hakbang 2: Sunugin o ibaon nang malalim malayo sa malulusog na puno upang masira ang pinamumugaran ng peste.",
      "pheromone_trap": "Hakbang 1: Isabit ang bitag 1.5 hanggang 2 metro ang taas sa poste. Hakbang 2: Ilagay ito nang 20-30 metro ang layo sa malulusog na puno upang ilayo ang peste sa sakahan.",
      "muscardine_fungus": "Ihalo ang inirekomendang Green Muscardine fungus sa tubig at direktang i-spray sa compost pits o nabubulok na kahoy kung saan nangingitlog ang mga salagubang.",
      "biological_control": "Magpakawala ng natural na kaaway ng peste gaya ng earwigs o gumamit ng aprubadong organikong pamatay mula sa tanggapan ng agrikultura.",
      "light_trap": "Maglagay ng maliwanag na bumbilya sa ibabaw ng plangganang may tubig at sabon sa gabi upang maakit at malunod ang mga lumilipad na salagubang.",
      "pruning": "Gamit ang matalas at malinis na itak, putulin ang matinding napinsalang dahon. Sunugin o ibaon agad ang mga naputol na bahagi upang hindi lumipat sa ibang dahon.",
      "fertilizer": "Maglagay ng inirekomendang pataba (nitrogen o potassium) sa paligid ng puno (mga 1 metro mula sa puno) upang mapabilis ang pagbawi nito.",
      "chemical_warning": "BABALA: Gamitin lamang ang kemikal bilang huling paraan. Magsuot ng guwantes at mask, sundin ang tamang timpla sa bote, at i-spray lamang sa may sira.",
      "monitoring": "Bisitahin ang sakahan kada 3-5 araw. Suriin ang itaas at murang dahon para sa mga bagong butas, ngatngat, o dumi ng insekto.",
      "general": "Mangyaring sundin ang rekomendasyong ito nang maingat. Para sa eksaktong sukat o detalyadong gabay, maghintay sa pagsusuri ng agriculturist."
    }
  },
  "backend_messages": {
    "report_submitted_success": "Matagumpay na naipasa at na-sync ang iyong ulat!",
    "report_submitted_failure": "Hindi mai-save ang ulat. Mangyaring subukan muli.",
    "follow_up_success": "Naipasa na ang iyong update at naibalik ang ulat para sa muling pagsusuri.",
    "follow_up_failure": "Hindi mai-save ang follow-up.",
    "visit_reason_required": "Mangyaring magbigay ng dahilan sa paghiling ng pagbisita.",
    "availability_shared": "Naibahagi na sa agriculturist ang iyong bakanteng oras.",
    "availability_failure": "Hindi maipasa ang iyong mga bakanteng oras.",
    "image_required": "Walang larawang na-upload",
    "image_invalid": "Hindi wasto ang in-upload na larawan",
    "inference_failed": "Hindi maiproseso ang larawan ng AI"
  }
}
  };

  function getCookie(name) {  
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  function setCookie(name, value, days) {
    let expires = "";
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax";
  }

  function resolveDotKey(obj, key) {
    if (!obj || !key) return null;
    let parts;
    if (key.startsWith("pest_knowledge_base.recommendations.initial_items.")) {
      const item = key.substring("pest_knowledge_base.recommendations.initial_items.".length);
      parts = obj.pest_knowledge_base ? ["pest_knowledge_base", "recommendations", "initial_items", item] : ["recommendations", "initial_items", item];
    } else if (key.startsWith("recommendations.initial_items.")) {
      const item = key.substring("recommendations.initial_items.".length);
      parts = (obj.pest_knowledge_base && !obj.recommendations) ? ["pest_knowledge_base", "recommendations", "initial_items", item] : ["recommendations", "initial_items", item];
    } else {
      parts = key.split(".");
    }
    if (parts && parts[0] === "scanner" && (!obj.scanner) && obj.scan_page) {
      parts[0] = "scan_page";
    } else if (parts && parts[0] === "scan_page" && (!obj.scan_page) && obj.scanner) {
      parts[0] = "scanner";
    } else if (parts && parts[0] === "modal" && (!obj.modal) && obj.report_modal) {
      parts[0] = "report_modal";
    } else if (parts && parts[0] === "report_modal" && (!obj.report_modal) && obj.modal) {
      parts[0] = "modal";
    } else if (parts && parts[0] === "drafts" && (!obj.drafts) && obj.drafts_page) {
      parts[0] = "drafts_page";
    } else if (parts && parts[0] === "drafts_page" && (!obj.drafts_page) && obj.drafts) {
      parts[0] = "drafts";
    } else if (parts && parts[0] === "reports" && (!obj.reports) && obj.reports_page) {
      parts[0] = "reports_page";
    } else if (parts && parts[0] === "reports_page" && (!obj.reports_page) && obj.reports) {
      parts[0] = "reports";
    } else if (parts && parts[0] === "recommendations" && (!obj.recommendations) && obj.pest_knowledge_base && obj.pest_knowledge_base.recommendations) {
      parts = ["pest_knowledge_base", "recommendations", ...parts.slice(1)];
    } else if (parts && parts.length >= 2 && parts[0] === "pest_knowledge_base" && parts[1] === "recommendations" && (!obj.pest_knowledge_base) && obj.recommendations) {
      parts = ["recommendations", ...parts.slice(2)];
    }
    let current = obj;
    for (let i = 0; i < parts.length; i++) {
      if (current && typeof current === "object" && parts[i] in current) {
        current = current[parts[i]];
      } else {
        return null;
      }
    }
    return current;
  }

  const CocoScanI18n = {
    dictionaries: TRANSLATIONS,

    getLanguage: function () {
      const stored = localStorage.getItem("cocoscan_lang");
      if (stored === "en" || stored === "tl") return stored;
      const cookieVal = getCookie("cocoscan_lang");
      if (cookieVal === "en" || cookieVal === "tl") return cookieVal;
      const docLang = document.documentElement.getAttribute("lang");
      if (docLang === "tl" || docLang === "en") return docLang;
      return "en";
    },

    setLanguage: function (lang, reload) {
      if (reload === undefined) reload = true;
      if (lang !== "en" && lang !== "tl") lang = "en";
      localStorage.setItem("cocoscan_lang", lang);
      setCookie("cocoscan_lang", lang, 365);
      document.documentElement.setAttribute("lang", lang);

      // Update backend session if online
      if (navigator.onLine) {
        fetch("/api/user/language-preference", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ language: lang })
        }).catch(err => console.warn("Failed to sync lang pref to backend:", err));
      }

      // Dispatch event
      window.dispatchEvent(new CustomEvent("cocoscan:languagechange", { detail: { language: lang } }));

      if (reload) {
        window.location.reload();
      } else {
        CocoScanI18n.applyToDOM();
        CocoScanI18n.updateToggleButtons();
      }
    },

    toggleLanguage: function (reload) {
      if (reload === undefined) reload = true;
      const current = CocoScanI18n.getLanguage();
      const next = current === "tl" ? "en" : "tl";
      CocoScanI18n.setLanguage(next, reload);
      return next;
    },

    t: function (key, defaultVal, params) {
      const lang = CocoScanI18n.getLanguage();
      let val = resolveDotKey(TRANSLATIONS[lang], key);
      if (val === null || val === undefined) {
        val = resolveDotKey(TRANSLATIONS["en"], key);
      }
      if (val === null || val === undefined) {
        val = defaultVal !== undefined ? defaultVal : key;
      }

      if (typeof val === "string" && params && typeof params === "object") {
        for (const [k, v] of Object.entries(params)) {
          val = val.replace(new RegExp(`\{${k}\}`, "g"), v);
        }
      }
      return val;
    },

    applyToDOM: function (root) {
      const container = root || document;
      const currentLang = CocoScanI18n.getLanguage();

      // Helper to safely update text without destroying icon children (<i>, <svg>, <img>)
      function updateTextPreservingIcons(el, newText) {
        const icons = el.querySelectorAll("i, svg, img");
        if (icons.length === 0) {
          el.textContent = newText;
          return;
        }
        // Find existing text node among children
        let foundTextNode = false;
        for (let i = 0; i < el.childNodes.length; i++) {
          const node = el.childNodes[i];
          if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim().length > 0) {
            node.nodeValue = " " + newText.trim() + " ";
            foundTextNode = true;
            break;
          }
        }
        if (!foundTextNode) {
          el.appendChild(document.createTextNode(" " + newText.trim()));
        }
      }

      // Text content
      container.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (key) {
          const defaultVal = el.textContent ? el.textContent.trim() : key;
          const translated = CocoScanI18n.t(key, defaultVal);
          updateTextPreservingIcons(el, translated);
        }
      });

      // Placeholders
      container.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (key) {
          el.setAttribute("placeholder", CocoScanI18n.t(key, el.getAttribute("placeholder")));
        }
      });

      // Titles / Tooltips
      container.querySelectorAll("[data-i18n-title]").forEach(el => {
        const key = el.getAttribute("data-i18n-title");
        if (key) {
          el.setAttribute("title", CocoScanI18n.t(key, el.getAttribute("title")));
        }
      });

      // Aria labels
      container.querySelectorAll("[data-i18n-aria]").forEach(el => {
        const key = el.getAttribute("data-i18n-aria");
        if (key) {
          el.setAttribute("aria-label", CocoScanI18n.t(key, el.getAttribute("aria-label")));
        }
      });
    },

    updateToggleButtons: function () {
      const currentLang = CocoScanI18n.getLanguage();
      document.querySelectorAll(".lang-toggle-btn").forEach(btn => {
        const enSpan = btn.querySelector(".lang-en");
        const tlSpan = btn.querySelector(".lang-tl");
        if (enSpan && tlSpan) {
          if (currentLang === "tl") {
            enSpan.classList.remove("active-lang");
            tlSpan.classList.add("active-lang");
          } else {
            enSpan.classList.add("active-lang");
            tlSpan.classList.remove("active-lang");
          }
        } else {
          btn.setAttribute("data-current-lang", currentLang);
          btn.innerHTML = `<i class="fa-solid fa-globe"></i> ${currentLang === "tl" ? "Tagalog" : "English"}`;
        }
      });
    }
  };

  // Expose globally
  global.CocoScanI18n = CocoScanI18n;
  global.toggleLanguagePreference = function () {
    return CocoScanI18n.toggleLanguage(true);
  };
  global.setLanguagePreference = function (lang) {
    return CocoScanI18n.setLanguage(lang, true);
  };

  // Auto-init on DOMContentLoaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      CocoScanI18n.applyToDOM();
      CocoScanI18n.updateToggleButtons();
    });
  } else {
    CocoScanI18n.applyToDOM();
    CocoScanI18n.updateToggleButtons();
  }
})(window);
