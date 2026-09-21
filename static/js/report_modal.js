(function () {
    window.COCOSCAN_BARANGAYS = [
        "Bagong Bayan II-A", "Bagong Pook VI-C", "Barangay I-A", "Barangay I-B", "Barangay II-A", "Barangay II-B", "Barangay II-C", "Barangay II-D", "Barangay II-E", "Barangay II-F", "Barangay III-A", "Barangay III-B", "Barangay III-C", "Barangay III-D", "Barangay III-E", "Barangay III-F", "Barangay IV-A", "Barangay IV-B", "Barangay IV-C", "Barangay V-A", "Barangay V-B", "Barangay V-C", "Barangay V-D", "Barangay VI-A", "Barangay VI-B", "Bautista", "Concepcion", "Del Remedio", "Dolores", "San Antonio 1", "San Antonio 2", "San Bartolome", "San Buenaventura", "San Crispin", "San Cristobal", "San Diego", "San Francisco", "San Gabriel", "San Gregorio", "San Ignacio", "San Isidro", "San Joaquin", "San Jose", "San Juan", "San Lorenzo", "San Lucas 1", "San Lucas 2", "San Marcos", "San Mateo", "San Miguel", "San Nicolas", "San Pedro", "San Rafael", "San Roque", "San Vicente", "Santa Ana", "Santa Catalina", "Santa Cruz", "Santa Elena", "Santa Filomena", "Santa Isabel", "Santa Maria", "Santa Maria Magdalena", "Santa Monica", "Santa Veronica", "Santiago I", "Santiago II", "Santisimo Rosario", "Santo Angel", "Santo Cristo", "Santo Niño", "Soledad", "Atisan", "Balagtas", "Dapdap", "Dolores", "Sta. Catalina", "Sta. Cruz", "Sta. Elena"
    ];

    const SUPABASE_REPORT_IMAGE_BASE_URL =
        "https://utvltqgxqnpcqrphuojc.supabase.co/storage/v1/object/public/reports/";

    // Inject compact schedule input styles once so templates don't need edits
    (function injectScheduleInputStyles() {
        if (typeof document === 'undefined' || document.getElementById('schedule-input-styles')) return;
        const css = `
            .schedule-input {
                width: 100%;
                box-sizing: border-box;
                height: 44px;
                line-height: 44px;
                padding: 6px 10px;
                border-radius: 10px;
                font-size: 0.95rem;
                border: 1px solid #e6eaf0;
                background: #ffffff;
                -webkit-appearance: none;
                appearance: none;
                vertical-align: middle;
            }
            /* ensure date/time controls align visually when placed in grid columns */
            .farmer-schedule-row .schedule-input { display: block; }
            .farmer-schedule-row { box-sizing: border-box; box-shadow: 0 1px 2px rgba(16,24,40,0.04); }
            .farmer-schedule-row .remove-schedule-btn { width: 100%; justify-self: stretch; margin-top: 8px; }
        `;
        const style = document.createElement('style');
        style.id = 'schedule-input-styles';
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    })();

    const t = (k, def) => {
        if (currentReportModalMode !== "farmer") {
            return def !== undefined ? def : k;
        }
        return (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
    };

    function isTagalogActive() {
        if (currentReportModalMode !== "farmer") return false;
        if (window.CocoScanI18n && typeof window.CocoScanI18n.getLanguage === 'function') {
            return window.CocoScanI18n.getLanguage() === 'tl';
        }
        return false;
    }

    function getInitialRecoTitle() {
        const isTl = isTagalogActive();
        const fallback = isTl ? 'Paunang mga Rekomendasyon' : 'Initial Recommendations';
        return (window.CocoScanI18n && typeof window.CocoScanI18n.t === 'function')
            ? window.CocoScanI18n.t('modal.initial_reco_title', fallback)
            : fallback;
    }

    function getVerifiedRecoTitle() {
        const isTl = isTagalogActive();
        const fallback = isTl ? 'Mga Rekomendasyon' : 'Recommendations';
        return (window.CocoScanI18n && typeof window.CocoScanI18n.t === 'function')
            ? window.CocoScanI18n.t('modal.verified_reco_title', fallback)
            : fallback;
    }

    window.addEventListener("cocoscan:languagechange", () => {
        const recoHeading = document.getElementById("report-initial-reco-heading-text");
        if (!recoHeading) return;
        const isVerified = recoHeading.getAttribute("data-i18n") === "modal.verified_reco_title";
        recoHeading.textContent = isVerified ? getVerifiedRecoTitle() : getInitialRecoTitle();
    });
    let currentReportModalRecord = null;
    let currentReportModalMode = "farmer";
    let activeReportModalSubmissionController = null;
    let currentWorkflowDefaultSubmitAction = null;
    let visitDiscussionPollTimer = null;
    const VISIT_DISCUSSION_POLL_INTERVAL_MS = 2500;
    let currentVisitUploadFiles = [];

    function getModalRoot() {
        return document.querySelector("[data-report-modal]");
    }

    function getCurrentUserRole() {
        const modalRoot = getModalRoot();
        const dataRole = (modalRoot?.getAttribute("data-user-role") || "").trim().toLowerCase();
        if (["agriculturist", "agri", "agri_expert"].includes(dataRole)) return "agriculturist";
        if (["admin", "lgu"].includes(dataRole)) return dataRole;

        const bodyRole = ((document.body && (document.body.getAttribute("data-user-role") || document.body.dataset.userRole)) || "").toLowerCase();
        if (bodyRole === "staff" || bodyRole === "admin" || bodyRole.includes("agri") || bodyRole.includes("lgu")) {
            if (["agriculturist", "agri", "agri_expert"].includes(bodyRole)) return "agriculturist";
            if (["admin", "lgu"].includes(bodyRole)) return bodyRole;
        }

        const path = (window.location.pathname || "").toLowerCase();
        if (path.includes("/agriculturist") || path.includes("/agri")) return "agriculturist";
        if (path.includes("/admin")) return "admin";
        if (path.includes("/lgu")) return "lgu";
        if (path.includes("/reports") || path.includes("/overview")) {
            const clientRole = (window.currentUserRole || localStorage.getItem('cocoscan_user_role') || "").trim().toLowerCase();
            if (clientRole === "admin" || clientRole === "lgu") return clientRole;
            const dataElem = document.getElementById("reports-data");
            const elemRole = (dataElem?.getAttribute("data-role") || "").toLowerCase();
            if (elemRole && ["admin", "lgu", "agriculturist"].includes(elemRole)) return elemRole;
            return "admin";
        }
        if (path.startsWith("/farmer")) return "farmer";

        const clientRole = (window.currentUserRole || localStorage.getItem('cocoscan_user_role') || "").trim().toLowerCase();
        if (["agriculturist", "agri", "agri_expert"].includes(clientRole)) return "agriculturist";
        if (["admin", "lgu"].includes(clientRole)) return clientRole;
        if (clientRole === "farmer" && path.startsWith("/farmer")) return "farmer";

        return "admin";
    }

    function shouldPollVisitDiscussion(report) {
        if (!report || !report.id) return false;
        if (currentReportModalMode === "lgu" || currentReportModalMode === "admin") return false;
        if (report.visitArchived) return false;
        const statusKey = getStatusKey(report.status || "");
        const activeDiscussionStatuses = [
            "awaiting_confirmed_schedule",
            "visit_requested",
            "waiting_for_agriculturist_confirmation",
            "waiting_agriculturist_confirmation",
            "visit_scheduled"
        ];
        if (!activeDiscussionStatuses.includes(statusKey) && !report.visitRescheduleReason) {
            return false;
        }
        return true;
    }

    function stopVisitDiscussionPoll() {
        if (visitDiscussionPollTimer !== null) {
            clearInterval(visitDiscussionPollTimer);
            visitDiscussionPollTimer = null;
        }
    }

    function updateVisitDiscussionMessages(report = currentReportModalRecord) {
        if (!report) return;
        if (currentReportModalMode === "lgu" || currentReportModalMode === "admin") return;
        const feedbackContainer = document.getElementById("report-farmer-feedback");
        if (!feedbackContainer) return;

        const badgeCount = feedbackContainer.querySelector("#visit-discussion-badge-count");
        const chats = Array.isArray(report.visitChats) ? report.visitChats : [];
        if (badgeCount) {
            badgeCount.textContent = chats.length;
        }

        const messagesContainer = feedbackContainer.querySelector("#visit-discussion-messages-container");
        if (!messagesContainer) {
            renderVisitDiscussionCard(currentReportModalMode, report);
            return;
        }

        const isScrolledToBottom = (messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight) < 70;

        messagesContainer.innerHTML = chats.length ? chats.map((chat) => {
            const isAgriculturistMessage = String(chat.sender_role || chat.sender_label || "").toLowerCase().includes("agriculturist");
            const role = isAgriculturistMessage ? "Agriculturist" : "Farmer";
            const firstName = chat.sender_first_name || "";
            const displayHeader = firstName ? `${role.toUpperCase()} (${firstName})` : role.toUpperCase();
            return `
                <div style="display:flex; justify-content:${isAgriculturistMessage ? "flex-end" : "flex-start"};">
                    <div style="max-width:82%; display:grid; gap:4px;">
                        <div style="font-size:0.74rem; font-weight:700; color:#64748b; letter-spacing:0.04em; padding:${isAgriculturistMessage ? "0 0 0 8px" : "0 8px 0 0"};">${escapeHtml(displayHeader)}</div>
                        <div style="padding:10px 12px; border-radius:16px; background:${isAgriculturistMessage ? "#ecfdf5" : "#f8fafc"}; color:#0f172a; box-shadow:0 1px 2px rgba(15,23,42,0.06);">
                            <div style="font-size:0.9rem; line-height:1.5;">${escapeHtml(chat.message || "")}</div>
                            <div style="margin-top:6px; font-size:0.72rem; color:#64748b;">${escapeHtml(formatVisitChatTimestamp(chat.created_at) || t('reports.just_now', "Just now"))}</div>
                        </div>
                    </div>
                </div>`;
        }).join("") : `<div style="font-size:0.9rem; color:#64748b;">${escapeHtml(t('modal.discussion_empty', 'No discussion messages yet.'))}</div>`;

        if (isScrolledToBottom) {
            requestAnimationFrame(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            });
        }
    }

    function startVisitDiscussionPoll(report) {
        stopVisitDiscussionPoll();
        if (!shouldPollVisitDiscussion(report)) return;

        visitDiscussionPollTimer = setInterval(async () => {
            try {
                const modalRoot = getModalRoot();
                if (!modalRoot || !modalRoot.classList.contains("open-modal") || currentReportModalRecord?.id !== report.id) {
                    stopVisitDiscussionPoll();
                    return;
                }

                if (!shouldPollVisitDiscussion(currentReportModalRecord)) {
                    stopVisitDiscussionPoll();
                    return;
                }

                const prevCount = (report.visitChats || []).length;
                await loadVisitDiscussion(report);
                if (!shouldPollVisitDiscussion(report)) {
                    stopVisitDiscussionPoll();
                    return;
                }

                const newChats = report.visitChats || [];
                if (newChats.length !== prevCount) {
                    updateVisitDiscussionMessages(report);
                }
            } catch (error) {
                console.warn("Visit discussion poll failed", error);
            }
        }, VISIT_DISCUSSION_POLL_INTERVAL_MS);
    }

    function queueOfflineAction(action) {
        if (!action || !action.type || !action.report_id) return;
        try {
            const raw = localStorage.getItem('cocoscan_offline_actions_queue') || '[]';
            const queue = JSON.parse(raw);
            queue.push({
                ...action,
                id: 'offline_act_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
                created_at: new Date().toISOString()
            });
            localStorage.setItem('cocoscan_offline_actions_queue', JSON.stringify(queue));
            console.info('[OfflineSync] Action queued for offline sync:', action);
        } catch (e) {
            console.warn('[OfflineSync] Could not queue offline action:', e);
        }
    }

    function updateLocalReportState(reportId, updaterFn) {
        if (!reportId || typeof updaterFn !== 'function') return;
        try {
            const raw = localStorage.getItem('cocoscan_cached_farmer_reports');
            if (raw) {
                let reports = JSON.parse(raw);
                if (Array.isArray(reports)) {
                    reports = reports.map(r => {
                        if (String(r.id) === String(reportId)) {
                            return updaterFn({ ...r });
                        }
                        return r;
                    });
                    if (window.CocoScanAuth && typeof window.CocoScanAuth.cacheFarmerReports === 'function') {
                        window.CocoScanAuth.cacheFarmerReports(reports);
                    } else {
                        localStorage.setItem('cocoscan_cached_farmer_reports', JSON.stringify(reports));
                    }
                }
            }
        } catch (e) {
            console.debug('updateLocalReportState note:', e);
        }
    }

    async function syncOfflineReportActions() {
        if (typeof navigator !== 'undefined' && !navigator.onLine) return;
        try {
            const queueRaw = localStorage.getItem('cocoscan_offline_actions_queue');
            if (!queueRaw) return;
            const queue = JSON.parse(queueRaw);
            if (!Array.isArray(queue) || queue.length === 0) return;

            const remaining = [];
            for (const action of queue) {
                try {
                    let res = null;
                    if (action.type === 'reschedule') {
                        res = await fetch(`/reports/${action.report_id}/request-reschedule`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(action.payload || {})
                        });
                    } else if (action.type === 'farmer-feedback') {
                        const fd = new FormData();
                        fd.append('report_id', action.report_id);
                        fd.append('confirmation', action.payload?.confirmation || 'resolved');
                        fd.append('reason', action.payload?.reason || '');
                        res = await fetch('/farmer/submit-assessment-feedback', {
                            method: 'POST',
                            body: fd
                        });
                    } else if (action.type === 'follow_up') {
                        res = await fetch('/farmer/follow-up-report', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                report_id: action.report_id,
                                notes: action.payload?.notes || ''
                            })
                        });
                    } else if (action.type === 'visit_chat') {
                        res = await fetch(`/reports/${action.report_id}/visit-chat`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                message: action.payload?.message || ''
                            })
                        });
                    }

                    if (!res || !res.ok) {
                        if (res && res.status >= 400 && res.status < 500) {
                            console.warn('[OfflineSync] Discarding invalid queued action (status ' + res.status + '):', action);
                        } else {
                            remaining.push(action);
                        }
                    }
                } catch (err) {
                    console.warn('[OfflineSync] Network error while syncing action:', action, err);
                    remaining.push(action);
                    break;
                }
            }

            if (remaining.length > 0) {
                localStorage.setItem('cocoscan_offline_actions_queue', JSON.stringify(remaining));
            } else {
                localStorage.removeItem('cocoscan_offline_actions_queue');
                console.info('[OfflineSync] All offline report actions synchronized successfully.');
            }
        } catch (e) {
            console.warn('[OfflineSync] Error during sync loop:', e);
        }
    }

    if (typeof window !== 'undefined') {
        window.addEventListener('online', () => {
            syncOfflineReportActions();
        });
        window.queueOfflineReportAction = queueOfflineAction;
        window.syncOfflineReportActions = syncOfflineReportActions;
        window.updateLocalReportState = updateLocalReportState;
        setTimeout(syncOfflineReportActions, 2000);
    }

    function escapeHtml(text) {
        return String(text ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }
    const escapeHTML = escapeHtml;

    function normalizeList(value) {
        if (Array.isArray(value)) {
            return value
                .map((item) => {
                    if (typeof item === "object" && item !== null) {
                        return String(item.image_url || item.url || item.src || "").trim();
                    }
                    return String(item ?? "").trim();
                })
                .filter(Boolean);
        }

        if (typeof value === "string") {
            const cleaned = value.trim();
            if (cleaned.startsWith("[") && cleaned.endsWith("]")) {
                try {
                    const parsed = JSON.parse(cleaned);
                    if (Array.isArray(parsed)) {
                        return parsed.map((item) => String(item ?? "").trim()).filter(Boolean);
                    }
                } catch (e) {
                    // Ignore JSON parse errors and treat as a regular string
                }
            }
            return cleaned ? [cleaned] : [];
        }

        return [];
    }

    function normalizeConfidence(value) {
        if (value === null || value === undefined || value === "") {
            return "--";
        }

        if (typeof value === "string") {
            const cleaned = value.trim();
            if (!cleaned) return "--";
            if (cleaned.endsWith("%")) return cleaned;
            const parsed = Number(cleaned);
            if (Number.isNaN(parsed)) return cleaned;
            return `${parsed <= 1 ? Math.round(parsed * 100) : Math.round(parsed)}%`;
        }

        const parsed = Number(value);
        if (Number.isNaN(parsed)) {
            return String(value);
        }

        return `${parsed <= 1 ? Math.round(parsed * 100) : Math.round(parsed)}%`;
    }

    function resolveReportImageUrl(imageUrl) {
        if (!imageUrl) return "";

        const resolved = String(imageUrl).trim();
        if (!resolved) return "";

        if (resolved.startsWith("http://") || resolved.startsWith("https://") || resolved.startsWith("data:") || resolved.startsWith("blob:")) {
            return resolved;
        }

        return `${SUPABASE_REPORT_IMAGE_BASE_URL}${resolved.replace(/^\/+/, "")}`;
    }

    function formatTimestamp(value) {
        if (!value) return "Timestamp unavailable";

        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) {
            return String(value);
        }

        const dateStr = new Intl.DateTimeFormat("en-US", {
            timeZone: "Asia/Manila",
            year: "numeric",
            month: "short",
            day: "numeric",
        }).format(parsed);

        const timeStr = new Intl.DateTimeFormat("en-US", {
            timeZone: "Asia/Manila",
            hour: "2-digit",
            minute: "2-digit",
            hour12: true,
        }).format(parsed);

        return `${dateStr} ${timeStr}`;
    }

    function cleanFarmerNotes(rawNotes = "") {
        if (!rawNotes) return "";
        const blocks = rawNotes.split(/\n\n+/);
        const cleanBlocks = blocks.filter(block => {
            const txt = block.trim();
            if (/^(Farmer confirmed the assessment|Farmer requested a visit|Agriculturist proposed a schedule|Farmer proposed a reschedule|Reason:|Availability:|Option \d+:|Visit scheduled|Visit completed|Visit canceled)/i.test(txt)) {
                return false;
            }
            return true;
        });
        return cleanBlocks.join("\n\n").trim();
    }

    function normalizeReportData(reportData = {}) {
        const gps = reportData.gps || {};
        const primaryImage = reportData.primary_image || reportData.img || reportData.image_url || reportData.image || "";
        const additionalImages = normalizeList(reportData.additional_images || reportData.supporting_images);
        const rawNotes = reportData.notes || reportData.farmer_notes || reportData.field_notes || "";
        const cleanNotes = cleanFarmerNotes(rawNotes);
        const feedbackData = extractFarmerFeedback(rawNotes, reportData.status);
        const visitCompletedMatch = String(rawNotes || "").match(/Visit completed:\s*([^\n]+)/i);
        const extractedVisitSummary = visitCompletedMatch ? visitCompletedMatch[1].trim() : "";
        const finalVisitSummary = reportData.visit_summary || reportData.visitSummary || extractedVisitSummary || "";

        return {
            id: reportData.id ?? null,
            mode: reportData.mode || currentReportModalMode,
            pest: reportData.pest || reportData.pest_type || reportData.prediction || "Unknown Pest",
            confidence: normalizeConfidence(reportData.confidence || reportData.pest_confidence),
            status: String(reportData.status || reportData.current_status || "").trim() || (currentReportModalMode === "scan" ? "Ready to Submit" : "Pending"),
            timestamp: reportData.timestamp || reportData.created_at || reportData.submitted_at || reportData.photo_taken_at || "",
            updated_at: reportData.updated_at || reportData.resolved_at || "",
            farmer: String(reportData.farmer || reportData.farmer_name || "Farmer").trim(),
            notes: cleanNotes,
            rawNotes: rawNotes,
            locationText: reportData.location_text || reportData.full_location || reportData.location || [reportData.barangay, reportData.municipality, reportData.province].filter(Boolean).join(", ") || "No location logged",
            latitude: gps.latitude ?? reportData.latitude ?? "",
            longitude: gps.longitude ?? reportData.longitude ?? "",
            accuracy: gps.accuracy ?? reportData.gps_accuracy ?? "",
            source: gps.source ?? reportData.location_source ?? "",
            primaryImage: resolveReportImageUrl(primaryImage),
            additionalImages,
            initialRecommendations: normalizeList(reportData.initial_recommendations || reportData.recommendations),
            expertRecommendations: normalizeList(reportData.expert_recommendations || reportData.expert_recommendation),
            reviewer_name: reportData.reviewer_name || reportData.reviewerName || "",
            reviewer_position: reportData.reviewer_position || reportData.position_title || "Agriculturist",
            reviewer_office: reportData.reviewer_office || reportData.agency_office || "",
            farmerFeedbackReason: feedbackData.reason || reportData.farmerFeedbackReason || reportData.farmer_feedback_reason || "",
            farmerFeedbackConfirmation: feedbackData.confirmation || reportData.farmerFeedbackConfirmation || reportData.farmer_feedback_confirmation || "",
            farmerSchedules: feedbackData.schedules?.length ? feedbackData.schedules : (reportData.farmerSchedules || []),
            availabilitySlots: normalizeAvailabilitySlots(reportData.availability_slots || reportData.availability || reportData.availabilitySlots || reportData.farmer_availability || feedbackData.schedules?.map((item) => item.date ? `${item.date} ${item.time || "Morning"}`.trim() : "") || []),
            agriBookedSchedules: normalizeAvailabilitySlots(reportData.agri_booked_schedules || reportData.agri_booked_slots || reportData.booked_schedules || []),
            weather: reportData.weather || {},
            visit_summary: finalVisitSummary,
            visit_images: normalizeList(reportData.visit_images || reportData.visitImages).map(resolveReportImageUrl),
            visitImages: normalizeList(reportData.visitImages || reportData.visit_images).map(resolveReportImageUrl),
            visit_completed_at: reportData.visit_completed_at || reportData.visitCompletedAt || "",
            final_remarks: reportData.final_remarks || reportData.finalRemarks || "",
            visitScheduleStamp: reportData.visitScheduleStamp || reportData.schedule_stamp || "",
            visitScheduleTitle: reportData.visitScheduleTitle || reportData.schedule_title || "",
            visitChats: Array.isArray(reportData.visitChats) ? reportData.visitChats : (Array.isArray(reportData.visit_chats) ? reportData.visit_chats : []),
            chat_count: reportData.chat_count ?? 0,
        };
    }

    function extractFarmerFeedback(notes = "", status = "") {
        const raw = String(notes || "").trim();
        const feedback = { reason: "", confirmation: "", schedules: [] };

        if (/Farmer confirmed the assessment resolved/i.test(raw) || /confirmed the assessment resolved/i.test(raw)) {
            feedback.confirmation = "resolved";
            return feedback;
        }

        if (/farmer requested a visit/i.test(raw)) {
            const reasonMatch = raw.match(/Reason:\s*([^\.]+)\./i);
            feedback.reason = reasonMatch ? reasonMatch[1].trim() : "";

            const availabilityMatch = raw.match(/Availability:\s*\[(.*?)\]/i);
            if (availabilityMatch) {
                const availabilitySlots = availabilityMatch[1]
                    .split(",")
                    .map((slot) => String(slot || "").trim())
                    .filter(Boolean);
                feedback.schedules = availabilitySlots.map((slot) => ({ date: slot, time: "", display: slot }));
            }

            const optionRegex = /Option\s*\d+:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*at\s*([0-9]{2}:[0-9]{2})\./gi;
            let match;
            while ((match = optionRegex.exec(raw)) !== null) {
                const date = match[1];
                const time = match[2];
                let display = `${date} ${time}`;
                try {
                    const dt = new Date(`${date}T${time}`);
                    if (!Number.isNaN(dt.getTime())) {
                        display = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(dt) + ' • ' + new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }).format(dt);
                    }
                } catch (e) {
                    // keep fallback
                }
                feedback.schedules.push({ date, time, display });
            }
        }

        return feedback;
    }

    const TIME_WINDOW_DEFINITIONS = {
        morning: { label: "Morning", shortLabel: "Morning", range: "8:00 AM - 12:00 PM" },
        afternoon: { label: "Afternoon", shortLabel: "Afternoon", range: "1:00 PM - 5:00 PM" },
    };

    function normalizeAvailabilitySlots(value) {
        if (Array.isArray(value)) {
            return value
                .map((item) => {
                    if (typeof item === "string") return item.trim();
                    if (item && typeof item === "object") {
                        const date = item.date || item.day || "";
                        const windowName = item.window || item.timeWindow || item.time || item.windowKey || "";
                        if (date) {
                            return windowName ? `${date} ${String(windowName)}`.trim() : date;
                        }
                    }
                    return "";
                })
                .filter(Boolean);
        }

        if (typeof value === "string") {
            const trimmed = value.trim();
            if (!trimmed) return [];
            if (trimmed.startsWith("[")) {
                try {
                    const parsed = JSON.parse(trimmed);
                    return normalizeAvailabilitySlots(parsed);
                } catch (e) {
                    return [];
                }
            }
            return trimmed
                .split(/,|\n|;/)
                .map((slot) => slot.trim())
                .filter(Boolean);
        }

        return [];
    }

    function parseAvailabilitySlot(slot) {
        const cleaned = String(slot || "").trim();
        if (!cleaned) return null;
        const match = cleaned.match(/^(\d{4}-\d{2}-\d{2})\s+(.+)$/i);
        if (!match) return { date: cleaned, windowKey: "morning" };
        const [, date, windowValue] = match;
        const lowerValue = String(windowValue).trim().toLowerCase();
        if (lowerValue.includes("afternoon")) return { date, windowKey: "afternoon", windowLabel: "Afternoon" };
        if (lowerValue.includes("morning")) return { date, windowKey: "morning", windowLabel: "Morning" };
        return { date, windowKey: "morning", windowLabel: windowValue };
    }

    function buildAvailabilitySlot(dateValue, windowKey) {
        const normalizedWindow = TIME_WINDOW_DEFINITIONS[windowKey] ? windowKey : "morning";
        return `${dateValue} ${TIME_WINDOW_DEFINITIONS[normalizedWindow].label}`;
    }

    function formatAvailabilitySlotLabel(slot) {
        const parsed = parseAvailabilitySlot(slot);
        if (!parsed) return String(slot || "");
        try {
            const formatter = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });
            const dateValue = new Date(`${parsed.date}T12:00:00`);
            return `${formatter.format(dateValue)} - ${parsed.windowLabel || TIME_WINDOW_DEFINITIONS[parsed.windowKey]?.label || "Morning"}`;
        } catch (e) {
            return String(slot || "");
        }
    }

    function getNextAvailabilityDates(count = 5) {
        const dates = [];
        const base = new Date();
        for (let index = 0; index < count; index += 1) {
            const current = new Date(base);
            current.setDate(base.getDate() + index);
            const year = current.getFullYear();
            const month = String(current.getMonth() + 1).padStart(2, "0");
            const day = String(current.getDate()).padStart(2, "0");
            dates.push(`${year}-${month}-${day}`);
        }
        return dates;
    }

    function getStatusKey(status) {
        return String(status || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
    }

    function setDisplay(element, visible, displayValue = "block") {
        if (!element) return;
        element.style.display = visible ? displayValue : "none";
    }

    function getWorkflowStatusDisplayLabel(status) {
        const normalized = getStatusKey(status);
        const labels = {
            "under_review": "Under Review",
            "assessment_issued": "Assessment Issued",
            "awaiting_confirmed_schedule": "Awaiting Confirmed Schedule",
            "visit_requested": "Visit Requested",
            "waiting_for_agriculturist_confirmation": "Waiting for Agriculturist Confirmation",
            "waiting_agriculturist_confirmation": "Waiting for Agriculturist Confirmation",
            "visit_scheduled": "Visit Scheduled",
            "visit_completed": "Visit Completed",
            "final_remarks_issued": "Final Remarks Issued",
            "recommendation_issued": "Recommendation Issued",
            "closed": "Closed",
            "resolved": "Resolved",
            "ready_to_submit": "Ready to Submit",
        };
        const defaultLabel = labels[normalized] || normalized || "Pending";
        if (currentReportModalMode === "farmer" && window.CocoScanI18n && typeof window.CocoScanI18n.t === "function") {
            return window.CocoScanI18n.t(`workflow_statuses.${normalized}`, defaultLabel);
        }
        return defaultLabel;
    }

    function getWorkflowStatusBadgeStyle(status) {
        const normalized = getStatusKey(status);
        const palette = {
            "under_review": { backgroundColor: "#fef3c7", color: "#92400e" },
            "assessment_issued": { backgroundColor: "#ecfdf5", color: "#065f46" },
            "awaiting_confirmed_schedule": { backgroundColor: "#eff6ff", color: "#1d4ed8" },
            "visit_requested": { backgroundColor: "#fdf2f8", color: "#be185d" },
            "waiting_for_agriculturist_confirmation": { backgroundColor: "#eff6ff", color: "#1d4ed8" },
            "waiting_agriculturist_confirmation": { backgroundColor: "#eff6ff", color: "#1d4ed8" },
            "visit_scheduled": { backgroundColor: "#fefce8", color: "#a16207" },
            "visit_completed": { backgroundColor: "#ecfeff", color: "#0f766e" },
            "final_remarks_issued": { backgroundColor: "#ede9fe", color: "#5b21b6" },
            "recommendation_issued": { backgroundColor: "#ecfdf5", color: "#065f46" },
            "resolved": { backgroundColor: "#dcfce7", color: "#166534" },
            "closed": { backgroundColor: "#dcfce7", color: "#166534" },
        };
        return palette[normalized] || { backgroundColor: "#f8fafc", color: "#475569" };
    }

    function isRecommendationIssuedStatus(status) {
        const normalized = getStatusKey(status);
        return [
            "recommendation_issued",
            "recommendation-issued",
            "reviewed",
            "reviewed_&_issued",
            "final_remarks_issued",
            "resolved",
            "closed",
            "completed",
            "assessment_issued",
            "assessment-issued",
            "assessment issued",
        ].includes(normalized);
    }

    function clearNode(node) {
        if (!node) return;
        node.innerHTML = "";
    }

    function setButtonLoading(button, isLoading, loadingText = "Saving...") {
        if (!button) return;
        const dataset = button.dataset || {};
        if (isLoading) {
            if (!dataset.defaultHtml) {
                try { button.dataset.defaultHtml = button.innerHTML; } catch (e) { button._defaultHtml = button.innerHTML; }
            }
            button.disabled = true;
            button.classList.add("btn-loading", "is-disabled");
            button.innerHTML = `
                <span style="display:inline-flex; align-items:center; gap:8px;">
                    <i class="fa-solid fa-circle-notch fa-spin"></i> ${loadingText}
                </span>
                <span class="btn-loading-bar"></span>
            `;
        } else {
            button.disabled = false;
            button.classList.remove("btn-loading", "is-disabled");
            const defaultHtml = dataset.defaultHtml || button._defaultHtml;
            if (defaultHtml) {
                button.innerHTML = defaultHtml;
            }
        }
    }

    function setReportModalSubmissionState(isSubmitting, pendingLabel = "Submitting your report…") {
        const scanSubmitButton = document.getElementById("report-scan-submit-btn");
        const agriSubmitButton = document.getElementById("report-agri-submit-btn");
        const cancelButton = document.getElementById("report-modal-cancel-btn");
        const actionButtons = [scanSubmitButton, agriSubmitButton].filter(Boolean);

        actionButtons.forEach((button) => {
            if (!button) return;
            const dataset = button.dataset || {};
            const shouldDisable = isSubmitting;
            button.disabled = shouldDisable;
            button.classList.toggle("is-disabled", shouldDisable);
            button.classList.toggle("btn-loading", shouldDisable);
            button.setAttribute("aria-busy", isSubmitting ? "true" : "false");

            if (isSubmitting) {
                if (!dataset.defaultHtml) {
                    try { button.dataset.defaultHtml = button.innerHTML; } catch (e) { button._defaultHtml = button.innerHTML; }
                }
                const icon = "fa-solid fa-circle-notch fa-spin";
                button.innerHTML = `
                    <span style="display:inline-flex; align-items:center; gap:8px;">
                        <i class="${icon}"></i> ${pendingLabel}
                    </span>
                    <span class="btn-loading-bar"></span>
                `;
            } else {
                const defaultHtml = dataset.defaultHtml || button._defaultHtml;
                if (defaultHtml) {
                    button.innerHTML = defaultHtml;
                }
            }
        });

        if (cancelButton) {
            cancelButton.disabled = false;
            cancelButton.classList.remove("is-disabled");
            cancelButton.setAttribute("aria-busy", "false");
        }
    }

    function abortActiveReportModalSubmission() {
        if (activeReportModalSubmissionController) {
            activeReportModalSubmissionController.abort();
            activeReportModalSubmissionController = null;
        }
        setReportModalSubmissionState(false);
    }

    function getRecommendationTooltip(text) {
        const lower = String(text).toLowerCase();
        const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
        if (lower.includes("sanitation")) return t("pest_recommendations.tooltip_sanitation", "<strong>Step 1:</strong> Collect all dead leaves, rotting trunks, and fallen fruits.<br><strong>Step 2:</strong> Burn them or bury them deep away from healthy trees to destroy hidden pest breeding grounds.");
        if (lower.includes("trap") && lower.includes("pheromone")) return t("pest_recommendations.tooltip_pheromone", "<strong>Step 1:</strong> Hang the trap 1.5 to 2 meters high on a pole.<br><strong>Step 2:</strong> Place it at least 20-30 meters away from your healthy trees so it lures pests AWAY from your farm, not into it.");
        if (lower.includes("fungus") || lower.includes("muscardine")) return t("pest_recommendations.tooltip_fungus", "Mix the recommended Green Muscardine fungus with water and spray directly onto compost pits, rotting logs, or traps where adult beetles lay eggs.");
        if (lower.includes("biological")) return t("pest_recommendations.tooltip_biological", "Introduce natural predators like earwigs or use organic biocontrol agents recommended by the local agriculture office.");
        if (lower.includes("light trap")) return t("pest_recommendations.tooltip_light_trap", "Set up a bright light bulb over a basin of soapy water at night. Flying pests will be attracted to the light and drown in the water.");
        if (lower.includes("prun") || lower.includes("cut")) return t("pest_recommendations.tooltip_prune", "Use a clean, sharp bolo to cut off heavily infested fronds. Burn or bury the cut pieces immediately so pests don't spread to other leaves.");
        if (lower.includes("fertiliz")) return t("pest_recommendations.tooltip_fertilizer", "Apply the recommended nitrogen or potassium fertilizers around the base of the tree (about 1 meter away from the trunk) to help the tree recover faster.");
        if (lower.includes("chemical") || lower.includes("insecticide")) return t("pest_recommendations.tooltip_chemical", "<strong>WARNING:</strong> Only use chemicals as a final option. Wear gloves and a mask, follow the exact dosage on the bottle, and spray only on affected areas.<br><br><i>Note: If you are unsure about what chemical to use, ask the agriculturist by putting it in your Farmer Notes below before submitting.</i>");
        if (lower.includes("monitor")) return t("pest_recommendations.tooltip_monitor", "Visit your farm every 3-5 days. Check the crown and young leaves of the affected trees for any new boreholes, chewed leaves, or pest droppings.");
        return t("pest_recommendations.tooltip_default", "Please follow this recommendation carefully. For exact measurements or detailed guidance, wait for the agriculturist's expert assessment.");
    }

    function getRecommendationPriority(text) {
        const lower = String(text).toLowerCase();
        if (lower.includes("sanitation") || lower.includes("prun") || lower.includes("cut") || lower.includes("remov")) return 1;
        if (lower.includes("trap") || lower.includes("net") || lower.includes("physical")) return 2;
        if (lower.includes("biological") || lower.includes("fungus") || lower.includes("muscardine") || lower.includes("natural")) return 3;
        if (lower.includes("fertiliz") || lower.includes("water") || lower.includes("nutrient")) return 4;
        if (lower.includes("monitor") || lower.includes("check")) return 5;
        if (lower.includes("chemical") || lower.includes("insecticide") || lower.includes("pesticide") || lower.includes("spray")) return 7;
        return 6;
    }

    function localizeRecommendationItem(item) {
        if (!item) return "";
        const clean = String(item).trim();
        const lang = (window.CocoScanI18n && typeof window.CocoScanI18n.getLanguage === 'function') 
            ? window.CocoScanI18n.getLanguage() 
            : (document.documentElement.lang || 'en');
        if (lang !== 'tl') return clean;

        const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
        const map = {
            "Prune and safely dispose of infested leaves": t("recommendations.initial_items.Prune and safely dispose of infested leaves", "Putulin at ligtas na sunugin o ibaon ang mga apektadong dahon"),
            "Maintain field sanitation and monitor infestation levels": t("recommendations.initial_items.Maintain field sanitation and monitor infestation levels", "Panatilihin ang kalinisan ng sakahan at subaybayan ang dami ng peste"),
            "Release earwigs and Tetrastichus parasitoids for natural control": t("recommendations.initial_items.Release earwigs and Tetrastichus parasitoids for natural control", "Magpakawala ng earwigs at Tetrastichus parasitoids para sa natural na pagpuksa"),
            "Spray white Muscardine fungus": t("recommendations.initial_items.Spray white Muscardine fungus", "Mag-spray ng white Muscardine fungus"),
            "Use approved pesticide early morning for severe infestations": t("recommendations.initial_items.Use approved pesticide early morning for severe infestations", "Gumamit ng aprubadong pamatay-peste sa madaling araw kapag labis na ang pamemeste"),
            "Improve farm sanitation and remove breeding sites": t("recommendations.initial_items.Improve farm sanitation and remove breeding sites", "Pabutihin ang kalinisan ng sakahan at alisin ang mga pinamumugaran"),
            "Install pheromone traps and green Muscardine fungus log traps": t("recommendations.initial_items.Install pheromone traps and green Muscardine fungus log traps", "Magkabit ng mga pheromone trap at green Muscardine fungus log trap"),
            "Apply biological treatment or use light traps at night": t("recommendations.initial_items.Apply biological treatment or use light traps at night", "Maglapat ng biological treatment o gumamit ng light trap sa gabi"),
            "Monitor weekly and consult an agricultural technician for severe cases": t("recommendations.initial_items.Monitor weekly and consult an agricultural technician for severe cases", "Subaybayan linggu-linggo at sumangguni sa agricultural technician kapag malala ang kaso"),
            "Continue regular monitoring": t("recommendations.initial_items.Continue regular monitoring", "Ipagpatuloy ang regular na pagsubaybay"),
            "Maintain current sanitation practices": t("recommendations.initial_items.Maintain current sanitation practices", "Panatilihin ang kasalukuyang gawi sa kalinisan"),
            "Inspect central spear leaves and unopened fronds weekly for early feeding streaks or browning edges.": t("recommendations.initial_items.Inspect central spear leaves and unopened fronds weekly for early feeding streaks or browning edges.", "Suriin linggu-linggo ang mga gitnang ubod at hindi pa bumubukas na palapa para sa mga unang bakas ng pagkain ng uod o pangingitim ng gilid."),
            "Maintain clean weed management and ensure adequate sunlight penetration and aeration around younger palms.": t("recommendations.initial_items.Maintain clean weed management and ensure adequate sunlight penetration and aeration around younger palms.", "Panatilihing malinis ang damo sa paligid at tiyaking nasisikatan ng araw at mahahanginan ang mga nakababatang puno."),
            "Carefully collect and safely compost or dispose of fallen, dried, or curled fronds to disrupt shelter sites.": t("recommendations.initial_items.Carefully collect and safely compost or dispose of fallen, dried, or curled fronds to disrupt shelter sites.", "Maingat na tipunin at ligtas na ibaon o linisin ang mga nalaglag, tuyo, o nakarolyong palapa upang sirain ang pamugaran ng peste."),
            "Preserve native beneficial predator populations (such as earwigs); avoid broad-spectrum chemical sprays.": t("recommendations.initial_items.Preserve native beneficial predator populations (such as earwigs); avoid broad-spectrum chemical sprays.", "Pangalagaan ang mga likas na kaibigang insekto (tulad ng mga earwig); iwasan ang pag-spray ng matatapang na kemikal."),
            "Improve general farm sanitation by clearing fallen decaying coconut logs, rotting wood, and compost heaps.": t("recommendations.initial_items.Improve general farm sanitation by clearing fallen decaying coconut logs, rotting wood, and compost heaps.", "Pabutihin ang kalinisan ng sakahan sa pamamagitan ng pag-alis ng mga nabubulok na troso ng niyog, bulok na kahoy, at bunton ng compost."),
            "Inspect palm crowns and spear leaves regularly for characteristic V-shaped cuts or entry boreholes.": t("recommendations.initial_items.Inspect palm crowns and spear leaves regularly for characteristic V-shaped cuts or entry boreholes.", "Regular na suriin ang tuktok ng puno at mga ubod para sa mga natatanging V-shaped na hiwa o butas na pinasukan ng uwang."),
            "Install non-chemical perimeter light traps or organic pheromone monitoring traps to observe beetle activity.": t("recommendations.initial_items.Install non-chemical perimeter light traps or organic pheromone monitoring traps to observe beetle activity.", "Maglagay ng mga light trap o organic na pheromone trap sa paligid upang masubaybayan ang paglipad ng mga uwang."),
            "Avoid applying unverified chemical insecticides; await formal recommendations from your agricultural officer.": t("recommendations.initial_items.Avoid applying unverified chemical insecticides; await formal recommendations from your agricultural officer.", "Iwasan ang paggamit ng hindi beripikadong kemikal na pestisidyo; hintayin ang opisyal na rekomendasyon mula sa agriculturist."),
            "Maintain regular monthly orchard inspections to monitor tree crown vigor and spot any early pest arrivals.": t("recommendations.initial_items.Maintain regular monthly orchard inspections to monitor tree crown vigor and spot any early pest arrivals.", "Magsagawa ng regular na buwanang pag-iinspeksyon sa sakahan upang subaybayan ang sigla ng puno at maagang mapansin ang peste."),
            "Ensure balanced soil fertilization and organic mulching to maintain natural tree resistance.": t("recommendations.initial_items.Ensure balanced soil fertilization and organic mulching to maintain natural tree resistance.", "Tiyakin ang balanseng pataba sa lupa at paglalagay ng organic mulch upang mapanatili ang likas na resistensya ng puno."),
            "Keep palm bases clear of dense weeds and decaying organic litter.": t("recommendations.initial_items.Keep palm bases clear of dense weeds and decaying organic litter.", "Panatilihing malinis ang paanan ng puno mula sa makakapal na damo at nabubulok na dumi."),
            "Record routine tree observation dates in your farm notebook or digital log.": t("recommendations.initial_items.Record routine tree observation dates in your farm notebook or digital log.", "Itala ang mga petsa ng regular na pagmamasid sa inyong talaan o digital log."),
            "Ensure the camera is focused directly on a coconut leaf, frond, or crown section under daylight.": t("recommendations.initial_items.Ensure the camera is focused directly on a coconut leaf, frond, or crown section under daylight.", "Tiyaking nakatutok ang camera sa dahon, palapa, o tuktok ng puno ng niyog sa ilalim ng liwanag ng araw."),
            "Hold the device steady and re-scan from approximately 1 to 2 feet away.": t("recommendations.initial_items.Hold the device steady and re-scan from approximately 1 to 2 feet away.", "Hawakan nang matatag ang camera at kumuha muli sa layong 1 hanggang 2 talampakan."),
            "Avoid scanning non-plant objects, background scenery, or extremely blurry images.": t("recommendations.initial_items.Avoid scanning non-plant objects, background scenery, or extremely blurry images.", "Iwasang kumuha ng litrato ng mga bagay na hindi halaman, tanawin sa paligid, o malabong larawan.")
        };
        return map[clean] || clean;
    }

    function formatScheduleStamp(stamp) {
        if (!stamp) return "";
        const lang = (window.CocoScanI18n && typeof window.CocoScanI18n.getLanguage === 'function') 
            ? window.CocoScanI18n.getLanguage() 
            : (document.documentElement.lang || 'en');
        if (lang !== 'tl') return stamp;

        const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
        let res = String(stamp).trim();
        if (res.startsWith("Confirmed:")) {
            res = res.replace("Confirmed:", t("modal.schedule_confirmed_prefix", "Kumpirmado:"));
        } else if (res.startsWith("Previous Schedule:")) {
            res = res.replace("Previous Schedule:", t("modal.schedule_previous_prefix", "Nakaraang Iskedyul:"));
        }

        res = res.replace(", from ", ", " + t("modal.schedule_from", "mula") + " ");
        res = res.replace(" to ", " " + t("modal.schedule_to", "hanggang") + " ");

        const months = {
            "January": "Enero", "February": "Pebrero", "March": "Marso", "April": "Abril",
            "May": "Mayo", "June": "Hunyo", "July": "Hulyo", "August": "Agosto",
            "September": "Setyembre", "October": "Oktubre", "November": "Nobyembre", "December": "Disyembre"
        };
        for (const [enMonth, tlMonth] of Object.entries(months)) {
            res = res.replace(new RegExp(`\\b${enMonth}\\b`, 'g'), tlMonth);
        }
        return res;
    }

    function renderList(node, items, emptyText, showIcon = true, withTooltip = false) {
        if (!node) return;
        node.innerHTML = "";

        if (!items || items.length === 0) {
            const li = document.createElement("li");
            const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
            const isExpertAssessmentEmpty = (
                emptyText === "No expert assessment available yet." ||
                emptyText === "Submit report for expert assessment" ||
                emptyText === t("modal.expert_assessment_empty", "No expert assessment available yet.") ||
                emptyText === t("modal.expert_assessment_prompt", "Submit report for expert assessment")
            );
            if (isExpertAssessmentEmpty) {
                li.style.listStyle = "none";
                li.style.margin = "0";
                li.style.padding = "0";
                li.innerHTML = `
                <div style="background-color: #fffbeb; color: #92400e; padding: 12px 16px; border-radius: 8px; font-size: 0.92rem; margin-top: 4px; display: flex; align-items: center; gap: 10px; border: 1px solid #fcd34d; width: 100%; box-sizing: border-box;">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size: 1.2rem; color:#d97706;"></i> 
                    <span style="font-weight: 500;">${escapeHtml(emptyText)}</span>
                </div>`;
            } else if (showIcon) {
                li.innerHTML = `<i class="fa-solid fa-circle-info" style="color: #d97706;"></i> <span>${escapeHtml(emptyText)}</span>`;
            } else {
                li.textContent = emptyText;
            }
            node.appendChild(li);
            return;
        }

        const sortedItems = withTooltip ? [...items].sort((a, b) => getRecommendationPriority(a) - getRecommendationPriority(b)) : items;

        sortedItems.forEach((item, index) => {
            const li = document.createElement("li");
            li.style.display = "flex";
            li.style.flexDirection = "column";
            li.style.marginBottom = "4px";

            let html = `<div style="display: flex; align-items: flex-start; gap: 4px;">`;
            if (showIcon && !withTooltip) {
                html += `<i class="fa-solid fa-circle-check" style="margin-top: 2px; color: var(--primary-green); flex-shrink: 0;"></i>`;
            } else if (showIcon && withTooltip) {
                html += `<div style="font-weight: 700; color: var(--text-muted); font-size: 0.85rem; margin-top: 0px; flex-shrink: 0; min-width: 14px; text-align: right; margin-right: 2px;">${index + 1}.</div>`;
            }
            const isExpertList = node && node.id === "report-expert-list";
            const textColor = isExpertList ? "#64748b" : "var(--text-dark)";
            const displayText = isExpertList ? escapeHtml(item) : escapeHtml(localizeRecommendationItem(item));
            html += `<span style="font-size: 0.85rem; line-height: 1.3; color: ${textColor}; padding: 0;">${displayText}</span>`;

            const tooltipText = withTooltip ? getRecommendationTooltip(item) : "";
            if (withTooltip) {
                html += `<i class="fa-solid fa-circle-question reco-tooltip-icon" style="color: rgba(56, 189, 248, 0.7); cursor: pointer; margin-top: 0px; font-size: 1.05rem; transition: opacity 0.2s; flex-shrink: 0;" title="Click for details"></i>`;
            }
            html += `</div>`;

            li.innerHTML = html;

            if (withTooltip) {
                const dropdownDiv = document.createElement("div");
                dropdownDiv.style.display = "none";
                dropdownDiv.style.marginTop = "2px";
                dropdownDiv.style.padding = "6px 8px";
                dropdownDiv.style.backgroundColor = "rgba(56, 189, 248, 0.1)";
                dropdownDiv.style.borderLeft = "3px solid rgba(56, 189, 248, 0.7)";
                dropdownDiv.style.borderRadius = "0 6px 6px 0";
                dropdownDiv.style.fontSize = "0.8rem";
                dropdownDiv.style.color = "var(--text-dark)";
                dropdownDiv.style.lineHeight = "1.3";
                dropdownDiv.innerHTML = tooltipText;

                li.appendChild(dropdownDiv);

                const icon = li.querySelector(".reco-tooltip-icon");
                if (icon) {
                    icon.addEventListener("click", () => {
                        if (dropdownDiv.style.display === "none") {
                            dropdownDiv.style.display = "block";
                            icon.style.opacity = "1";
                        } else {
                            dropdownDiv.style.display = "none";
                            icon.style.opacity = "0.7";
                        }
                    });
                }
            }

            node.appendChild(li);
        });
    }

    function renderAdditionalImages(node, images) {
        if (!node) return;
        node.innerHTML = "";

        if (!images || images.length === 0) {
            if (currentReportModalMode !== "scan") {
                const emptyText = (currentReportModalMode === "farmer" && window.CocoScanI18n)
                    ? window.CocoScanI18n.t("modal.additional_images_empty", "No additional images uploaded.")
                    : "No additional images uploaded.";
                node.innerHTML = `<div style="width:100%;"><p style="font-size: 0.82rem; color: var(--text-muted); margin: 0; text-align: left;">${escapeHtml(emptyText)}</p></div>`;
            }
            return;
        }

        images.forEach((imageUrl, index) => {
            const frame = document.createElement("div");
            frame.style.borderRadius = "12px";
            frame.style.overflow = "hidden";
            frame.style.background = "#eaeaea";
            frame.style.aspectRatio = "1 / 1";

            const image = document.createElement("img");
            image.src = resolveReportImageUrl(imageUrl);
            image.alt = `Additional report image ${index + 1}`;
            image.style.width = "100%";
            image.style.height = "100%";
            image.style.objectFit = "cover";
            frame.appendChild(image);
            node.appendChild(frame);
        });
    }

    function weatherLine(value, suffix) {
        if (value === null || value === undefined || value === "") {
            return "--";
        }
        return suffix ? `${value}${suffix}` : String(value);
    }

    async function fetchWeatherSnapshot(latitude, longitude) {
        try {
            if (latitude === "" || longitude === "" || latitude === null || longitude === null || latitude === undefined || longitude === undefined) {
                throw new Error("Missing coordinates");
            }

            const latValue = Number(latitude);
            const lngValue = Number(longitude);
            if (Number.isNaN(latValue) || Number.isNaN(lngValue)) {
                throw new Error("Invalid coordinates");
            }

            const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${latValue}&longitude=${lngValue}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m`;
            const response = await fetch(weatherUrl);
            if (!response.ok) {
                throw new Error(`Weather service returned ${response.status}`);
            }

            const data = await response.json();
            const current = data.current || {};
            return {
                location: `${latValue.toFixed(4)}, ${lngValue.toFixed(4)}`,
                temp: current.temperature_2m ?? "--",
                humidity: current.relative_humidity_2m ?? "--",
                rainfall: current.precipitation ?? "--",
                wind: current.wind_speed_10m ?? "--",
                is_down: false,
            };
        } catch (error) {
            return {
                location: "Weather unavailable",
                temp: "--",
                humidity: "--",
                rainfall: "--",
                wind: "--",
                is_down: true,
            };
        }
    }

    function applyStatusStyle(report) {
        const severityBanner = document.getElementById("report-severity-banner");
        const statusNode = document.getElementById("report-status-text");
        const pestTitle = document.getElementById("report-pest-title");

        if (statusNode) {
            const statusStyle = getWorkflowStatusBadgeStyle(report.status || "--");
            statusNode.textContent = getWorkflowStatusDisplayLabel(report.status || "--");
            statusNode.style.color = statusStyle.color;
        }

        if (severityBanner) {
            severityBanner.style.backgroundColor = "#1E4620";
            severityBanner.style.color = "#E6F4EA";
        }

        if (pestTitle) {
            pestTitle.style.color = "#E6F4EA";
        }
    }

    function applyModeState(mode, report = currentReportModalRecord) {
        const scanButton = document.getElementById("report-scan-submit-btn");
        const agriButton = document.getElementById("report-agri-submit-btn");
        const cancelButton = document.getElementById("report-modal-cancel-btn");
        const notesInput = document.getElementById("field-notes-capture");
        const notesDisplay = document.getElementById("report-notes-display");
        const expertInput = document.getElementById("expert-notes-input");
        const expertHelp = document.getElementById("expert-notes-help");
        const agriVerificationGroup = document.getElementById("agri-verification-group");
        const scanOnlyNodes = document.querySelectorAll("[data-scan-only]");
        const readonlyOnlyNodes = document.querySelectorAll("[data-readonly-only]");
        const isReviewed = isRecommendationIssuedStatus(report?.status || "");

        const normalizedMode = String(mode || "").toLowerCase();
        const isAgriMode = ["agriculturist", "agri", "agri_expert"].includes(normalizedMode);

        const statusKey = getStatusKey(report?.status || "");
        const assessmentAlreadyIssued = ["assessment_issued", "recommendation_issued", "waiting_for_agriculturist_confirmation", "waiting_agriculturist_confirmation", "awaiting_confirmed_schedule", "visit_requested", "visit_scheduled", "visit_completed", "final_remarks_issued", "resolved", "closed"].includes(statusKey) || (Array.isArray(report.expertRecommendations) && report.expertRecommendations.length > 0);

        setDisplay(scanButton, normalizedMode === "scan", "flex");
        // Show agriculturist submit only when in agriculturist mode and no recommendation/assessment has been issued
        setDisplay(agriButton, isAgriMode && !assessmentAlreadyIssued, "flex");
        setDisplay(cancelButton, true, "inline-flex");

        scanOnlyNodes.forEach((node) => setDisplay(node, normalizedMode === "scan", "block"));
        readonlyOnlyNodes.forEach((node) => setDisplay(node, normalizedMode !== "scan", "block"));

        // Agriculturist submit button state: disable when assessment already issued or report reviewed
        if (agriButton) {
            const disableAgri = assessmentAlreadyIssued;
            agriButton.disabled = disableAgri;
            agriButton.classList.toggle("is-disabled", disableAgri);
            agriButton.setAttribute("aria-disabled", String(disableAgri));
            if (disableAgri) {
                agriButton.style.backgroundColor = "#cbd5e1";
                agriButton.style.color = "#475569";
                agriButton.innerHTML = '<i class="fa-solid fa-lock"></i> Assessment Issued';
            } else {
                agriButton.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Assessment &amp; Verification';
                agriButton.style.backgroundColor = "";
                agriButton.style.color = "";
            }
        }

        if (expertInput) {
            const allowExpertInput = isAgriMode && !assessmentAlreadyIssued;
            setDisplay(expertInput, allowExpertInput, "block");
        }

        if (expertHelp) {
            const allowExpertHelp = isAgriMode && !assessmentAlreadyIssued;
            setDisplay(expertHelp, allowExpertHelp, "block");
        }

        if (agriVerificationGroup) {
            const showVerification = isAgriMode && !assessmentAlreadyIssued;
            setDisplay(agriVerificationGroup, showVerification, "block");
            if (showVerification && typeof window.setAgriValidationMode === "function") {
                window.setAgriValidationMode("validate");
            }
        }

        const scanActionBar = document.getElementById("report-scan-action-bar");
        if (scanActionBar) setDisplay(scanActionBar, normalizedMode === "scan", "flex");

        if (notesInput && notesDisplay) {
            if (normalizedMode === "scan") {
                setDisplay(notesInput, true, "block");
                setDisplay(notesDisplay, false);
            } else {
                setDisplay(notesInput, false);
                setDisplay(notesDisplay, true, "block");
                notesDisplay.textContent = report?.notes || t("modal.notes_empty", "No notes logged.");
            }
        }
    }

    function getOfficialRecommendationsForPest(pestName) {
        const pLower = String(pestName || "").toLowerCase();
        if (window.CocoScanI18n && window.CocoScanI18n.currentStrings?.pest_knowledge_base?.recommendations) {
            const baseRecs = window.CocoScanI18n.currentStrings.pest_knowledge_base.recommendations;
            if (pLower.includes("brontispa") || pLower.includes("leaf beetle")) {
                return baseRecs.brontispa || [];
            }
            if (pLower.includes("rhino") || pLower.includes("beetle")) {
                return baseRecs.rhinoceros_beetle || [];
            }
            if (pLower.includes("healthy") || pLower.includes("malusog")) {
                return baseRecs.healthy_leaf || [];
            }
        }
        if (pLower.includes("brontispa") || pLower.includes("leaf beetle")) {
            return [
                "Prune and safely dispose of infested leaves",
                "Maintain field sanitation and monitor infestation levels",
                "Release earwigs and Tetrastichus parasitoids for natural control",
                "Spray white Muscardine fungus",
                "Use approved pesticide early morning for severe infestations"
            ];
        }
        if (pLower.includes("rhino") || pLower.includes("beetle")) {
            return [
                "Improve farm sanitation and remove breeding sites",
                "Install pheromone traps and green Muscardine fungus log traps",
                "Apply biological treatment or use light traps at night",
                "Monitor weekly and consult an agricultural technician for severe cases"
            ];
        }
        if (pLower.includes("healthy") || pLower.includes("malusog")) {
            return [
                "Continue regular monitoring",
                "Maintain current sanitation practices"
            ];
        }
        return [
            "Ensure the camera is focused directly on a coconut leaf, frond, or crown section under daylight.",
            "Hold the device steady and re-scan from approximately 1 to 2 feet away."
        ];
    }

    function formatCleanPestName(pest) {
        if (!pest || pest === "--") return "--";
        const pLower = String(pest).toLowerCase();
        if (pLower.includes("healthy") || pLower.includes("malusog")) {
            return window.CocoScanI18n ? window.CocoScanI18n.t("pest_knowledge_base.pests.healthy_leaf", "Healthy Coconut Leaf") : "Healthy Coconut Leaf";
        }
        if (pLower.includes("not a coconut") || pLower.includes("hindi larawan")) {
            return "Not a Coconut Leaf Image";
        }
        if (pLower.includes("brontispa") || pLower.includes("leaf beetle")) {
            return "Brontispa";
        }
        if (pLower.includes("rhino") || pLower.includes("beetle")) {
            return "Rhinoceros Beetle";
        }
        return pest.replace(/^possible pest:\s*/i, '').replace(/^posibleng peste:\s*/i, '');
    }

    function getVerifiedFirstName(fullName) {
        if (!fullName) return "";
        const clean = String(fullName).trim();
        if (/pca agriculturist/i.test(clean) || /^agriculturist$/i.test(clean)) {
            return "";
        }
        return clean.split(/\s+/)[0];
    }

    let currentAgriValidationMode = "validate";

    window.handleAgriPestSelectChange = function (val) {
        const customWrap = document.getElementById("agri-custom-pest-wrap");
        const customInput = document.getElementById("agri-custom-pest-input");
        if (val === "custom") {
            if (customWrap) customWrap.style.display = "block";
            if (customInput) {
                const cur = (customInput.value || "").trim().toLowerCase();
                if (!cur || cur === "brontispa" || cur.includes("rhino") || cur.includes("beetle") || cur.includes("healthy") || cur.includes("not a coconut")) {
                    customInput.value = "";
                }
                customInput.focus();
            }
        } else {
            if (customWrap) customWrap.style.display = "none";
            if (customInput) customInput.value = "";
        }
    };

    window.setAgriValidationMode = function (mode) {
        currentAgriValidationMode = mode === "correct" ? "correct" : "validate";
        const btnValidate = document.getElementById("btn-tab-validate-correct");
        const btnCorrect = document.getElementById("btn-tab-correct-result");
        const selectWrap = document.getElementById("agri-correction-select-wrap");
        const select = document.getElementById("agri-verified-pest-select");
        const customWrap = document.getElementById("agri-custom-pest-wrap");
        const customInput = document.getElementById("agri-custom-pest-input");
        const report = currentReportModalRecord;

        if (btnValidate) btnValidate.classList.toggle("active", currentAgriValidationMode === "validate");
        if (btnCorrect) btnCorrect.classList.toggle("active", currentAgriValidationMode === "correct");

        if (currentAgriValidationMode === "validate") {
            if (selectWrap) selectWrap.style.display = "none";
            if (customWrap) customWrap.style.display = "none";
            if (select && report?.pest) {
                const pestName = String(report.pest || "").toLowerCase();
                if (pestName.includes("brontispa")) {
                    select.value = "Brontispa";
                    if (customInput) customInput.value = "";
                } else if (pestName.includes("rhino") || pestName.includes("beetle")) {
                    select.value = "Rhinoceros Beetle";
                    if (customInput) customInput.value = "";
                } else if (pestName.includes("healthy") || pestName.includes("malusog")) {
                    select.value = "Healthy Coconut Leaf";
                    if (customInput) customInput.value = "";
                } else if (pestName.includes("not a coconut") || pestName.includes("not coconut") || pestName.includes("hindi larawan")) {
                    select.value = "Not a Coconut Leaf Image";
                    if (customInput) customInput.value = "";
                } else {
                    select.value = "custom";
                    if (customWrap) customWrap.style.display = "block";
                    if (customInput) customInput.value = report.pest;
                }
            }
        } else {
            if (selectWrap) selectWrap.style.display = "block";
            if (select) {
                if (select.value === "custom" && customWrap) {
                    customWrap.style.display = "block";
                }
                select.focus();
            }
        }
    };

    async function submitExpertAssessment() {
        const expertInput = document.getElementById("expert-notes-input");
        const report = currentReportModalRecord;
        if (!report?.id) {
            alert("This report does not have a valid identifier.");
            return;
        }
        if (!expertInput) {
            return submitWorkflowAction(currentWorkflowDefaultSubmitAction || "submit-assessment");
        }

        const assessment = String(expertInput.value || "").trim();
        if (!assessment) {
            alert("Please provide expert assessment notes before submitting.");
            return;
        }

        setReportModalSubmissionState(true, "Submitting assessment & verification…");
        try {
            const verifiedSelect = document.getElementById("agri-verified-pest-select");
            const customInput = document.getElementById("agri-custom-pest-input");
            let verifiedPest = verifiedSelect ? verifiedSelect.value : "";
            if (verifiedPest === "custom" && customInput && customInput.value.trim()) {
                verifiedPest = customInput.value.trim();
            }
            const isCorrection = currentAgriValidationMode === "correct";

            const response = await fetch("/agriculturist/submit-assessment", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    report_id: report.id,
                    assessment_notes: assessment,
                    verified_pest: verifiedPest || report.pest,
                    is_correction: isCorrection,
                }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
                alert(data.message || "The assessment could not be saved.");
                return;
            }
            report.status = "assessment_issued";
            if (data.verified_pest || verifiedPest) {
                report.pest = data.verified_pest || verifiedPest;
            }
            if (data.reviewer_name) {
                report.reviewer_name = data.reviewer_name;
            }
            if (data.reviewer_position) {
                report.reviewer_position = data.reviewer_position;
            }
            if (data.reviewer_office) {
                report.reviewer_office = data.reviewer_office;
            }
            if (Array.isArray(data.official_recommendations) && data.official_recommendations.length > 0) {
                report.officialRecommendations = data.official_recommendations;
                report.initialRecommendations = data.official_recommendations;
            } else {
                const recs = getOfficialRecommendationsForPest(report.pest);
                report.officialRecommendations = recs;
                report.initialRecommendations = recs;
            }
            if (!Array.isArray(report.expertRecommendations)) {
                report.expertRecommendations = [];
            }
            report.expertRecommendations.push(assessment);

            const verifierName = data.reviewer_name || report.reviewer_name || "";
            const verifierFirstName = data.reviewer_first_name || getVerifiedFirstName(verifierName);

            // 1. Dynamic Result Card Header Update:
            // Remove "POSSIBLE PEST" badge and warning notice banner; show "DETECTED PEST"
            const eyebrowPending = document.getElementById("pest-eyebrow-pending");
            if (eyebrowPending) setDisplay(eyebrowPending, false);

            const eyebrowVerified = document.getElementById("pest-eyebrow-verified");
            if (eyebrowVerified) {
                setDisplay(eyebrowVerified, true, "inline-flex");
                eyebrowVerified.innerHTML = `<span id="pest-verified-by-text" data-i18n="modal.detected_pest_eyebrow">DETECTED PEST</span>`;
            }

            const pendingNotice = document.getElementById("report-pending-validation-notice");
            if (pendingNotice) setDisplay(pendingNotice, false);

            // Dynamically switch main title to official verified pest name
            const pestTitle = document.getElementById("report-pest-title");
            if (pestTitle) {
                pestTitle.textContent = formatCleanPestName(report.pest);
            }

            // Confidence row update: "Verified by Agriculturist (First Name)"
            const confidenceRow = document.getElementById("report-confidence-row");
            if (confidenceRow) {
                const verifiedText = verifierFirstName ? `Verified by Agriculturist ${escapeHtml(verifierFirstName)}` : `Verified by Agriculturist`;
                confidenceRow.innerHTML = `<span id="pest-verified-by-text">${verifiedText}</span>`;
            }

            // 2. Dynamic Recommendations Switch:
            // Remove temporary "Safe Precautionary Actions" notice and general safe steps description
            document.querySelectorAll(".safe-actions-notice-banner, #report-safe-actions-notice").forEach((el) => setDisplay(el, false));
            document.querySelectorAll(".initial-reco-desc-text, #report-initial-reco-desc").forEach((el) => setDisplay(el, false));
            
            const recoHeading = document.getElementById("report-initial-reco-heading-text");
            if (recoHeading) {
                recoHeading.textContent = getVerifiedRecoTitle();
                recoHeading.setAttribute("data-i18n", "modal.verified_reco_title");
            }

            // Automatically load and display official complete recommendations
            renderList(document.getElementById("report-initial-list"), report.officialRecommendations, t("modal.initial_reco_empty", "No recommendations available."), true, true);

            // 3. Update Expert Assessment List & hide input controls
            const expertEmptyText = (currentReportModalMode === "farmer" && window.CocoScanI18n)
                ? window.CocoScanI18n.t("modal.expert_assessment_empty", "No expert assessment available yet.")
                : "No expert assessment available yet.";
            renderList(document.getElementById("report-expert-list"), report.expertRecommendations, expertEmptyText, false);

            const issuedNote = document.getElementById("expert-assessment-issued-note");
            if (issuedNote) setDisplay(issuedNote, false);

            const issuerNote = document.getElementById("expert-assessment-issuer-note");
            if (issuerNote) {
                const displayName = verifierName || "PCA Agriculturist";
                const pos = data.reviewer_position || report.reviewer_position || "Agriculturist";
                const off = data.reviewer_office || report.reviewer_office || "";
                let html = `Issued by ${escapeHtml(displayName)}<br>${escapeHtml(pos)}`;
                if (off) html += `<br>${escapeHtml(off)}`;
                issuerNote.innerHTML = html;
                issuerNote.style.lineHeight = "1.4";
                setDisplay(issuerNote, true, "block");
            }

            const agriVerificationGroup = document.getElementById("agri-verification-group");
            if (agriVerificationGroup) setDisplay(agriVerificationGroup, false);
            if (expertInput) setDisplay(expertInput, false);
            const expertHelp = document.getElementById("expert-notes-help");
            if (expertHelp) setDisplay(expertHelp, false);
            const agriSubmitBtn = document.getElementById("report-agri-submit-btn");
            if (agriSubmitBtn) setDisplay(agriSubmitBtn, false);

            // Update local report storage cache
            updateLocalReportState(report.id, (r) => ({
                ...r,
                status: "assessment_issued",
                pest: report.pest,
                pest_type: report.pest,
                reviewer_name: verifierName,
                reviewer_position: report.reviewer_position,
                reviewer_office: report.reviewer_office,
                expert_recommendations: report.expertRecommendations,
                official_recommendations: report.officialRecommendations,
                initial_recommendations: report.officialRecommendations,
            }));

            applyStatusStyle(report);
            renderWorkflowActions(currentReportModalMode, report);

            if (typeof window.renderReportsGrid === "function") {
                try { window.renderReportsGrid(); } catch (e) { console.debug(e); }
            }

            alert(data.message || "Assessment notes saved successfully.");
        } catch (error) {
            console.error("Assessment submission error:", error);
            alert("The assessment could not be submitted right now.");
        } finally {
            setReportModalSubmissionState(false);
        }
    }

    window.submitExpertValidation = function () {
        return submitExpertAssessment();
    };

    function formatVisitChatTimestamp(value) {
        if (!value) return "";
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) return String(value);
        return new Intl.DateTimeFormat("en-US", {
            timeZone: "Asia/Manila",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: true,
        }).format(parsed);
    }

    async function loadVisitDiscussion(report) {
        if (!report?.id) return;
        try {
            const response = await fetch(`/reports/${report.id}/visit-discussion`);
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
                return;
            }
            report.visitChats = Array.isArray(data.messages) ? data.messages : [];
            report.schedule = data.schedule || null;
            report.visitScheduleStamp = data.schedule_stamp || "";
            report.visitArchived = Boolean(data.is_archived);
            const rawVisitImages = Array.isArray(data.visit_images) ? data.visit_images : [];
            report.visitImages = rawVisitImages.map(item => {
                const rawUrl = typeof item === "object" && item !== null ? (item.image_url || item.url || item.src || "") : item;
                return resolveReportImageUrl(rawUrl);
            }).filter(Boolean);
            report.visit_images = report.visitImages;
            report.visit_summary = data.visit_summary || data.report?.visit_summary || report.visit_summary || "";
            report.visit_completed_at = data.report?.visit_completed_at || report.visit_completed_at || "";
            report.final_remarks = data.report?.final_remarks || report.final_remarks || "";
            report.visitRescheduleReason = data.visit_reschedule_reason || "";
            report.visitRescheduledAt = data.visit_rescheduled_at || "";
            report.visitRescheduledBy = data.visit_rescheduled_by || "";
            report.visitScheduleTitle = data.schedule_title || (report.visitRescheduleReason ? "Reschedule Requested" : "Visit Scheduled");
            report.status = data.status || report.status;
            if (report.status && typeof report.status === "string") {
                report.status = report.status;
            }
        } catch (error) {
            console.warn("Unable to load visit discussion", error);
        }
    }

    function renderVisitDiscussionCard(mode, report = currentReportModalRecord) {
        const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
        const feedbackContainer = document.getElementById("report-farmer-feedback");
        const feedbackCard = document.getElementById("report-farmer-feedback-card");
        if (!feedbackContainer || !feedbackCard) {
            return;
        }

        const isArchived = Boolean(report?.visitArchived);
        const isAgriculturist = mode === "agriculturist";
        const isLguOrAdmin = (mode === "lgu" || mode === "admin");
        const chats = Array.isArray(report?.visitChats) ? report.visitChats : [];
        const normalizedStatus = getStatusKey(report?.status || "");
        const hasScheduleStamp = Boolean(report?.visitScheduleStamp);
        const hasVisitSummary = Boolean(report?.visit_summary);
        const hasPendingReschedule = Boolean(report?.visitRescheduleReason);
        const activeDiscussionStatuses = [
            "awaiting_confirmed_schedule",
            "visit_requested",
            "waiting_for_agriculturist_confirmation",
            "waiting_agriculturist_confirmation",
            "visit_scheduled"
        ];
        const isDiscussionStatus = activeDiscussionStatuses.includes(normalizedStatus);

        // In LGU or Admin mode: Follow-up card is only shown when there's an actual scheduled stamp or visit summary
        if (isLguOrAdmin) {
            if (!hasScheduleStamp && !hasVisitSummary) {
                feedbackContainer.innerHTML = "";
                setDisplay(feedbackCard, false);
                return;
            }
        } else {
            // For Farmer / Agriculturist: only show when there is an active discussion, existing chats, schedule, reschedule, or archived state
            const hasActionableContent = isDiscussionStatus || chats.length > 0 || hasScheduleStamp || hasPendingReschedule || isArchived;
            if (!hasActionableContent) {
                feedbackContainer.innerHTML = "";
                setDisplay(feedbackCard, false);
                return;
            }
        }

        const statusLabel = getWorkflowStatusDisplayLabel(report?.status || "");
        const rawScheduleTitle = report?.visitScheduleTitle || (report?.visitRescheduleReason ? "Reschedule Requested" : "Visit Scheduled");
        let localizedScheduleTitle = rawScheduleTitle;
        if (report?.visitRescheduleReason || rawScheduleTitle === "Reschedule Requested") {
            localizedScheduleTitle = t("workflow_statuses.visit_requested", "Reschedule Requested");
        } else if (rawScheduleTitle === "New Schedule Confirmed") {
            localizedScheduleTitle = t("modal.schedule_new_confirmed", "New Schedule Confirmed");
        } else if (rawScheduleTitle === "Visit Scheduled") {
            localizedScheduleTitle = t("workflow_statuses.visit_scheduled", "Visit Scheduled");
        }
        const scheduleTitle = localizedScheduleTitle;
        const statusText = isArchived ? scheduleTitle : statusLabel;
        const messagePlaceholder = isAgriculturist ? "Type a message..." : t("modal.discussion_placeholder", "Discuss visit details...");
        const messageCount = chats.length;
        const messageLabel = `${messageCount} ${messageCount === 1 ? "message" : "messages"}`;
        if (report && report.visitDiscussionExpanded === undefined) {
            report.visitDiscussionExpanded = true;
        }
        const isExpanded = report?.visitDiscussionExpanded !== false;

        const bannerStyle = hasPendingReschedule
            ? "background:#fffbeb; color:#b45309;" // Yellow/Orange
            : "background:#ecfdf5; color:#065f46;"; // Green

        feedbackContainer.innerHTML = `
            <div style="display:grid; gap:14px; padding:8px 0 4px 0; width:100%; max-width:100%; min-width:0; box-sizing:border-box;">
                ${(mode !== "lgu" && mode !== "admin") ? `
               <button id="visit-discussion-toggle" type="button"
                onclick="window.toggleVisitDiscussion ? window.toggleVisitDiscussion(event) : null"
                aria-expanded="${isExpanded ? "true" : "false"}"
                style="
                    display:flex;
                    align-items:center;
                    justify-content:space-between;
                    width:100%;
                    max-width:100%;
                    box-sizing:border-box;
                    padding:10px 14px;
                    border:1px solid #bfdbfe;
                    border-radius:999px;
                    background:#eff6ff;
                    color:#1d4ed8;
                    font-weight:700;
                    text-align:left;
                    cursor:pointer;
                    box-shadow:inset 0 1px 2px rgba(59,130,246,0.08);
                ">

                <!-- Left -->
                <span style="
                    display:flex;
                    align-items:center;
                    gap:10px;
                    min-width:0;
                    flex:1;
                    white-space:nowrap;
                    overflow:hidden;
                ">

                    <span id="visit-discussion-badge-count" style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        width:24px;
                        height:24px;
                        border-radius:50%;
                        background:#dbeafe;
                        color:#2563eb;
                        border:1px solid #93c5fd;
                        font-size:0.85rem;
                        font-weight:700;
                        line-height:1;
                        flex-shrink:0;
                    ">
                        ${messageCount}
                    </span>


                    <!-- Title -->
                    <span id="visit-discussion-toggle-title" style="
                        font-size:0.90rem;
                        font-weight:600;
                        white-space:nowrap;
                        overflow:hidden;
                        text-overflow:ellipsis;
                        display:inline-block;
                        transform:none !important;
                    ">
                        ${escapeHtml(t('modal.discussion_toggle_title', 'Visit Request Discussion'))}
                    </span>

                </span>

                <!-- Chevron -->
                <span id="visit-discussion-chevron" class="visit-discussion-chevron" style="
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    width:30px;
                    height:30px;
                    border-radius:50%;
                    background:#dbeafe;
                    color:#2563eb;
                    flex-shrink:0;
                    transform:rotate(${isExpanded ? 90 : 0}deg);
                    transition:transform .2s ease;
                ">
                    <i class="fa-solid fa-chevron-right"></i>
                </span>

            </button>
                <div id="visit-discussion-body" style="display:${isExpanded ? "grid" : "none"}; gap:10px;">
                    <div id="visit-discussion-messages-container" style="display:grid; gap:8px; padding:10px; border:1px solid #e2e8f0; border-radius:16px; background:#fff; max-height:320px; overflow-y:auto;">
                        ${chats.length ? chats.map((chat) => {
            const isAgriculturistMessage = String(chat.sender_role || chat.sender_label || "").toLowerCase().includes("agriculturist");
            const role = isAgriculturistMessage ? "Agriculturist" : "Farmer";
            const firstName = chat.sender_first_name || "";
            const displayHeader = firstName ? `${role.toUpperCase()} (${firstName})` : role.toUpperCase();
            return `
                                <div style="display:flex; justify-content:${isAgriculturistMessage ? "flex-end" : "flex-start"};">
                                    <div style="max-width:82%; display:grid; gap:4px;">
                                        <div style="font-size:0.74rem; font-weight:700; color:#64748b; letter-spacing:0.04em; padding:${isAgriculturistMessage ? "0 0 0 8px" : "0 8px 0 0"};">${escapeHtml(displayHeader)}</div>
                                        <div style="padding:10px 12px; border-radius:16px; background:${isAgriculturistMessage ? "#ecfdf5" : "#f8fafc"}; color:#0f172a; box-shadow:0 1px 2px rgba(15,23,42,0.06);">
                                            <div style="font-size:0.9rem; line-height:1.5;">${escapeHtml(chat.message || "")}</div>
                                            <div style="margin-top:6px; font-size:0.72rem; color:#64748b;">${escapeHtml(formatVisitChatTimestamp(chat.created_at) || t('reports.just_now', "Just now"))}</div>
                                        </div>
                                    </div>
                                </div>`;
        }).join("") : `<div style="font-size:0.9rem; color:#64748b;">${escapeHtml(t('modal.discussion_empty', 'No discussion messages yet.'))}</div>`}
                    </div>
                    ${isArchived ? "" : `
                        <div style="display:flex; align-items:flex-end; background:#f8fafc; border:1px solid #cbd5e1; border-radius:24px; padding:6px 6px 6px 16px; gap:8px;">
                            <textarea id="visit-discussion-input" placeholder="${escapeHtml(messagePlaceholder)}" style="flex:1; border:none; background:transparent; resize:none; min-height:24px; max-height:100px; padding:10px 0; font-family:inherit; font-size:0.95rem; color:#0f172a; outline:none; line-height:1.4;" rows="1" oninput="this.style.height='24px'; this.style.height=(this.scrollHeight)+'px';"></textarea>
                            <button type="button" id="visit-discussion-send-btn" style="background:#2563eb; color:#fff; border:none; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; cursor:pointer; flex-shrink:0; transition:opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                                <i class="fa-solid fa-paper-plane" style="margin-right:2px; margin-top:1px; font-size:1rem;"></i>
                            </button>
                        </div>
                    `}
                </div>
                ` : ""}
                ${report?.visitScheduleStamp ? `<div style="padding:10px 12px; border-radius:14px; ${bannerStyle} font-size:0.92rem; font-weight:600; width:100%; max-width:100%; box-sizing:border-box; word-break:break-word;">${escapeHtml(scheduleTitle)}<br>${escapeHtml(formatScheduleStamp(report.visitScheduleStamp))}</div>` : ""}
                ${(hasPendingReschedule && !isArchived && mode !== "lgu" && mode !== "admin") ? `
                    <div style="background:#eff6ff; color:#1e3a8a; padding:12px 14px; border-radius:8px; border:1px solid #bfdbfe; font-size:0.9rem; display:flex; align-items:center; gap:10px; font-family: sans-serif; width:100%; max-width:100%; box-sizing:border-box;">
                        <strong>${escapeHtml(t('modal.tip_label', 'Tip:'))}</strong> ${escapeHtml(t('modal.discussion_tip_reschedule', 'Click the "Visit Request Discussion" button to chat and finalize a new date and time.'))}
                    </div>
                ` : ""}
                ${(!isArchived && isAgriculturist && mode !== "lgu" && mode !== "admin") ? `<button type="button" id="visit-discussion-finalize-btn" class="btn-control submit-primary" style="justify-self:start; margin-top:4px;" onclick="window.openFinalizeVisitScheduleModal ? window.openFinalizeVisitScheduleModal() : null">Finalize Schedule</button>` : ""}
                ${(isArchived && mode !== "lgu" && mode !== "admin") ? `<div style="font-size:0.9rem; color:#475569; line-height:1.5; width:100%; max-width:100%; box-sizing:border-box;">${escapeHtml(t('modal.discussion_closed', 'The scheduling discussion has been closed.'))}</div>` : ""}
                ${(isArchived && mode !== "lgu" && mode !== "admin") ? `<button type="button" id="request-reschedule-btn" class="btn-control submit-primary" style="width:100%; max-width:100%; box-sizing:border-box; margin-top:6px; margin-bottom:4px;" onclick="window.openRequestRescheduleModal ? window.openRequestRescheduleModal() : null">${escapeHtml(t('modal.btn_request_reschedule', 'Request Reschedule'))}</button>` : ""}
                ${(report?.visit_summary && (mode === "lgu" || mode === "admin")) ? `<div style="font-size:0.95rem; color:#334155; line-height:1.6; background:#f8fafc; padding:14px; border-radius:12px; border:1px solid #e2e8f0; margin-top:10px; width:100%; max-width:100%; box-sizing:border-box;"><strong>${escapeHtml(t('modal.visit_summary_title', 'Visit Summary'))}:</strong><br>${escapeHtml(report.visit_summary)}</div>` : ""}
            </div>`;

        // If no visible text content was generated, keep card hidden
        if (!feedbackContainer.textContent.trim()) {
            feedbackContainer.innerHTML = "";
            setDisplay(feedbackCard, false);
            return;
        }

        setDisplay(feedbackCard, true, "block");

        const h4 = feedbackCard.querySelector('h4');
        if (h4) {
            if (normalizedStatus === "resolved") {
                h4.innerHTML = `<i class="fa-solid fa-check-circle"></i> ${escapeHtml(t('modal.resolution_details_title', 'Resolution Details'))}`;
            } else {
                h4.innerHTML = `<i class="fa-solid fa-calendar-check"></i> ${escapeHtml(t('modal.followup_section_title', 'Follow-up'))}`;
            }
        }

        const toggleButton = feedbackContainer.querySelector('#visit-discussion-toggle');
        if (toggleButton) {
            toggleButton.onclick = (e) => {
                if (window.toggleVisitDiscussion) {
                    window.toggleVisitDiscussion(e);
                }
            };
        }

        const finalizeBtn = feedbackContainer.querySelector('#visit-discussion-finalize-btn');
        if (finalizeBtn) {
            finalizeBtn.addEventListener('click', () => {
                openFinalizeVisitScheduleModal(report);
            });
        }

        const sendButton = feedbackContainer.querySelector('#visit-discussion-send-btn');
        if (sendButton) {
            sendButton.addEventListener('click', async () => {
                const messageInput = feedbackContainer.querySelector('#visit-discussion-input');
                const message = messageInput?.value?.trim() || "";
                if (!message) {
                    alert("Please type a message before sending.");
                    return;
                }

                // Disable button and input to prevent double sending
                sendButton.disabled = true;
                sendButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="font-size:1rem;"></i>';
                messageInput.disabled = true;

                // Save scroll position of the modal wrapper to prevent jumping
                const modalRoot = getModalRoot();
                let scrollContainer = modalRoot;
                if (modalRoot) {
                    const descendants = modalRoot.querySelectorAll('*');
                    for (const el of descendants) {
                        const style = getComputedStyle(el);
                        if (el.scrollHeight > el.clientHeight && (style.overflowY === 'auto' || style.overflowY === 'scroll')) {
                            scrollContainer = el;
                            break;
                        }
                    }
                }
                const savedScrollTop = scrollContainer ? scrollContainer.scrollTop : 0;

                try {
                    const response = await fetch(`/reports/${report.id}/visit-chat`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message }),
                    });
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok || !data.success) {
                        alert(data.message || "The message could not be saved.");
                        sendButton.disabled = false;
                        sendButton.innerHTML = '<i class="fa-solid fa-paper-plane" style="margin-right:2px; margin-top:1px; font-size:1rem;"></i>';
                        messageInput.disabled = false;
                        return;
                    }

                    // Clear message input and re-enable controls immediately
                    messageInput.value = "";
                    messageInput.style.height = "24px";
                    sendButton.disabled = false;
                    sendButton.innerHTML = '<i class="fa-solid fa-paper-plane" style="margin-right:2px; margin-top:1px; font-size:1rem;"></i>';
                    messageInput.disabled = false;
                    messageInput.focus();

                    await loadVisitDiscussion(report);
                    updateVisitDiscussionMessages(report);
                    const messagesContainer = feedbackContainer.querySelector('#visit-discussion-messages-container');
                    if (messagesContainer) {
                        requestAnimationFrame(() => {
                            messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        });
                    }

                    renderWorkflowActions(currentReportModalMode, report);
                    startVisitDiscussionPoll(report);

                    if (scrollContainer) {
                        requestAnimationFrame(() => {
                            scrollContainer.scrollTop = savedScrollTop;
                        });
                    }
                } catch (error) {
                    alert("The message could not be sent right now.");
                    sendButton.disabled = false;
                    sendButton.innerHTML = '<i class="fa-solid fa-paper-plane" style="margin-right:2px; margin-top:1px; font-size:1rem;"></i>';
                    messageInput.disabled = false;
                }
            });
        }

        const messageInput = feedbackContainer.querySelector('#visit-discussion-input');
        if (messageInput && sendButton) {
            messageInput.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    e.preventDefault();
                    if (!sendButton.disabled) {
                        sendButton.click();
                    }
                }
            });
        }

        const confirmButton = feedbackContainer.querySelector('#confirm-visit-schedule-btn');
        if (confirmButton) {
            confirmButton.addEventListener('click', () => openFinalizeVisitScheduleModal(report));
        }

        const requestRescheduleButton = feedbackContainer.querySelector('#request-reschedule-btn');
        if (requestRescheduleButton) {
            requestRescheduleButton.addEventListener('click', () => openRequestRescheduleModal(report));
        }

        const messagesContainer = feedbackContainer.querySelector('#visit-discussion-messages-container');
        if (messagesContainer && isExpanded) {
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 10);
        }
        setDisplay(feedbackCard, true, "block");
    }

    function openRequestRescheduleModal(report = currentReportModalRecord) {
        if (!report || !report.id) {
            report = currentReportModalRecord;
        }
        if (!report || !report.id) {
            alert("Report details not found. Please refresh and try again.");
            return;
        }

        const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
        const existingModal = document.getElementById("visit-reschedule-mini-modal");
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement("div");
        modal.id = "visit-reschedule-mini-modal";
        modal.style.position = "fixed";
        modal.style.inset = "0";
        modal.style.background = "rgba(15, 23, 42, 0.65)";
        modal.style.backdropFilter = "blur(4px)";
        modal.style.webkitBackdropFilter = "blur(4px)";
        modal.style.display = "flex";
        modal.style.alignItems = "center";
        modal.style.justifyContent = "center";
        modal.style.padding = "20px";
        modal.style.zIndex = "200000";
        modal.innerHTML = `
            <div style="width:min(100%, 430px); background:#fff; border-radius:20px; box-shadow:0 20px 50px rgba(15,23,42,0.25); padding:28px; display:grid; gap:20px;" onclick="event.stopPropagation()">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:14px;">
                    <div style="font-size:1.05rem; font-weight:700; color:#102a43;">${escapeHtml(t('modal.reschedule_modal_title', 'Request Reschedule'))}</div>
                    <button type="button" id="visit-reschedule-modal-close" class="btn-control cancel-secondary" style="width: auto; min-height: 34px; padding: 8px 12px; border-radius: 999px; background: #dc2626; color: #ffffff; border: 1px solid #dc2626; box-shadow: none;">${escapeHtml(t('modal.btn_close', 'Close'))}</button>
                </div>
                <div style="display:grid; gap:14px;">
                    <label style="display:grid; gap:10px; font-size:0.98rem; color:#334155;">
                        <span style="font-weight:700;">${escapeHtml(t('modal.reschedule_reason_label', 'Reason'))}</span>
                        <select id="visit-reschedule-reason" class="schedule-input" style="padding:0 14px; border-radius:12px; border:1px solid #e6e6e6; height:48px; box-sizing:border-box; font-size:1rem;">
                            <option value="Emergency">${escapeHtml(t('modal.reschedule_opt_emergency', 'Emergency'))}</option>
                            <option value="Bad weather">${escapeHtml(t('modal.reschedule_opt_weather', 'Bad weather'))}</option>
                            <option value="Personal conflict">${escapeHtml(t('modal.reschedule_opt_conflict', 'Personal conflict'))}</option>
                            <option value="Other">${escapeHtml(t('modal.reschedule_opt_other', 'Other'))}</option>
                        </select>
                    </label>
                    <div id="visit-reschedule-other-wrapper" style="display:none;">
                        <label style="display:grid; gap:10px; font-size:0.98rem; color:#334155;">
                            <span style="font-weight:700;">${escapeHtml(t('modal.reschedule_details_label', 'Reason Details'))}</span>
                            <textarea id="visit-reschedule-other-details" class="notes-input-box" placeholder="${escapeHtml(t('modal.reschedule_details_placeholder', 'Add more details...'))}" style="min-height:140px; padding:18px;"></textarea>
                        </label>
                    </div>
                </div>
                <button type="button" id="visit-reschedule-save-btn" class="btn-control submit-primary" style="width:100%; padding:16px 20px; border-radius:14px;">${escapeHtml(t('modal.reschedule_btn_submit', 'Submit Request'))}</button>
            </div>`;
        document.body.appendChild(modal);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

        const reasonSelect = modal.querySelector('#visit-reschedule-reason');
        const otherWrapper = modal.querySelector('#visit-reschedule-other-wrapper');
        const toggleOtherInput = () => {
            if (otherWrapper) {
                otherWrapper.style.display = reasonSelect?.value === 'Other' ? 'block' : 'none';
            }
        };
        reasonSelect?.addEventListener('change', toggleOtherInput);
        toggleOtherInput();

        modal.querySelector('#visit-reschedule-modal-close')?.addEventListener('click', () => modal.remove());
        modal.querySelector('#visit-reschedule-save-btn')?.addEventListener('click', async (e) => {
            const saveBtn = e.target.closest('button');
            const reason = reasonSelect?.value || "";
            const details = modal.querySelector('#visit-reschedule-other-details')?.value?.trim() || "";
            if (reason === 'Other' && !details) {
                alert(t('modal.alert_provide_details', "Please provide reason details for 'Other'."));
                return;
            }
            const finalReason = reason === 'Other' ? `${reason}: ${details}` : reason;
            if (!finalReason) {
                alert(t('modal.alert_select_reason', "Please select a reason before submitting the reschedule request."));
                return;
            }
            const isOffline = typeof navigator !== 'undefined' && (!navigator.onLine || (typeof localStorage !== 'undefined' && localStorage.getItem('cocoscan_offline_active') === 'true'));
            if (isOffline) {
                queueOfflineAction({
                    type: 'reschedule',
                    report_id: report.id,
                    payload: { reason: finalReason }
                });
                report.visitArchived = false;
                report.visitDiscussionExpanded = true;
                report.visit_reschedule_reason = finalReason;
                report.status = "Awaiting Confirmed Schedule";
                report.visitScheduleTitle = "Reschedule Requested";
                if (!Array.isArray(report.visitChats)) report.visitChats = [];
                report.visitChats.push({
                    message: `Reschedule requested: ${finalReason}`,
                    created_at: new Date().toISOString(),
                    is_farmer: true
                });
                updateLocalReportState(report.id, (r) => ({
                    ...r,
                    status: 'Awaiting Confirmed Schedule',
                    visit_reschedule_reason: finalReason
                }));
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                if (typeof window.renderReportsGrid === "function") {
                    try { window.renderReportsGrid(); } catch (gridErr) { console.debug(gridErr); }
                }
                modal.remove();
                alert(t('modal.reschedule_offline_saved', "Offline Mode: Your reschedule request has been saved locally and will be automatically submitted once you regain connection."));
                return;
            }

            setButtonLoading(saveBtn, true, "Submitting Request...");
            try {
                const response = await fetch(`/reports/${report.id}/request-reschedule`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ reason: finalReason }),
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The reschedule request could not be submitted.");
                    setButtonLoading(saveBtn, false);
                    return;
                }
                report.visitArchived = false;
                report.visitDiscussionExpanded = true;
                report.visit_reschedule_reason = finalReason;
                report.status = "Awaiting Confirmed Schedule";
                report.visitScheduleTitle = "Reschedule Requested";
                await loadVisitDiscussion(report);
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                if (typeof window.renderReportsGrid === "function") {
                    try { window.renderReportsGrid(); } catch (gridErr) { console.debug(gridErr); }
                }
                modal.remove();
                alert(data.message || t('modal.reschedule_success', "Reschedule request submitted."));
            } catch (error) {
                queueOfflineAction({
                    type: 'reschedule',
                    report_id: report.id,
                    payload: { reason: finalReason }
                });
                report.visitArchived = false;
                report.visitDiscussionExpanded = true;
                report.visit_reschedule_reason = finalReason;
                report.status = "Awaiting Confirmed Schedule";
                report.visitScheduleTitle = "Reschedule Requested";
                if (!Array.isArray(report.visitChats)) report.visitChats = [];
                report.visitChats.push({
                    message: `Reschedule requested: ${finalReason}`,
                    created_at: new Date().toISOString(),
                    is_farmer: true
                });
                updateLocalReportState(report.id, (r) => ({
                    ...r,
                    status: 'Awaiting Confirmed Schedule',
                    visit_reschedule_reason: finalReason
                }));
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                if (typeof window.renderReportsGrid === "function") {
                    try { window.renderReportsGrid(); } catch (gridErr) { console.debug(gridErr); }
                }
                modal.remove();
                alert(t('modal.reschedule_offline_saved', "Offline Mode: Your reschedule request has been saved locally and will be automatically submitted once you regain connection."));
            }
        });
    }

    function openFinalizeVisitScheduleModal(report = currentReportModalRecord) {
        if (!report || !report.id) {
            report = currentReportModalRecord;
        }
        if (!report || !report.id) {
            alert("Report details not found. Please refresh and try again.");
            return;
        }

        const existingModal = document.getElementById("visit-schedule-mini-modal");
        if (existingModal) {
            existingModal.remove();
        }

        const localNow = new Date();
        const curY = localNow.getFullYear();
        const curM = String(localNow.getMonth() + 1).padStart(2, '0');
        const curD = String(localNow.getDate()).padStart(2, '0');
        const todayStr = `${curY}-${curM}-${curD}`;
        const modal = document.createElement("div");
        modal.id = "visit-schedule-mini-modal";
        modal.style.position = "fixed";
        modal.style.inset = "0";
        modal.style.background = "rgba(15, 23, 42, 0.65)";
        modal.style.backdropFilter = "blur(4px)";
        modal.style.webkitBackdropFilter = "blur(4px)";
        modal.style.display = "flex";
        modal.style.alignItems = "center";
        modal.style.justifyContent = "center";
        modal.style.padding = "20px";
        modal.style.zIndex = "200000";
        modal.innerHTML = `
            <div style="width:min(100%, 430px); background:#fff; border-radius:18px; box-shadow:0 20px 50px rgba(15,23,42,0.25); padding:28px; display:grid; gap:20px;" onclick="event.stopPropagation()">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:14px;">
                    <div style="font-size:1.05rem; font-weight:700; color:#102a43;">Finalize Visit Schedule</div>
                    <button type="button" id="visit-schedule-modal-close" class="btn-control cancel-secondary" style="width: auto; min-height: 34px; padding: 8px 12px; border-radius: 999px; background: #dc2626; color: #ffffff; border: 1px solid #dc2626; box-shadow: none;">Close</button>
                </div>
                <div style="display:grid; gap:14px;">
                    <label style="display:grid; gap:8px; font-size:0.96rem; color:#334155;">
                        <span style="font-weight:700;">Select the agreed date</span>
                        <input id="visit-confirmed-date" type="date" min="${todayStr}" value="${todayStr}" class="schedule-input" style="padding:0 14px; border-radius:12px; border:1px solid #e6e6e6; height:48px; box-sizing:border-box;">
                    </label>
                    <label style="display:grid; gap:8px; font-size:0.96rem; color:#334155;">
                        <span style="font-weight:700;">Start Time</span>
                        <select id="visit-start-time" class="schedule-input" style="padding:0 14px; border-radius:12px; border:1px solid #e6e6e6; height:48px; box-sizing:border-box; background-color:#fff;">
                            <option value="" disabled selected>Select start time</option>
                            <option value="08:00">8:00 AM</option><option value="08:30">8:30 AM</option>
                            <option value="09:00">9:00 AM</option><option value="09:30">9:30 AM</option>
                            <option value="10:00">10:00 AM</option><option value="10:30">10:30 AM</option>
                            <option value="11:00">11:00 AM</option><option value="11:30">11:30 AM</option>
                            <option value="12:00">12:00 PM</option><option value="12:30">12:30 PM</option>
                            <option value="13:00">1:00 PM</option><option value="13:30">1:30 PM</option>
                            <option value="14:00">2:00 PM</option><option value="14:30">2:30 PM</option>
                            <option value="15:00">3:00 PM</option><option value="15:30">3:30 PM</option>
                            <option value="16:00">4:00 PM</option><option value="16:30">4:30 PM</option>
                            <option value="17:00">5:00 PM</option>
                        </select>
                    </label>
                    <label style="display:grid; gap:8px; font-size:0.96rem; color:#334155;">
                        <span style="font-weight:700;">End Time</span>
                        <select id="visit-end-time" class="schedule-input" style="padding:0 14px; border-radius:12px; border:1px solid #e6e6e6; height:48px; box-sizing:border-box; background-color:#fff;">
                            <option value="" disabled selected>Select end time</option>
                            <option value="08:00">8:00 AM</option><option value="08:30">8:30 AM</option>
                            <option value="09:00">9:00 AM</option><option value="09:30">9:30 AM</option>
                            <option value="10:00">10:00 AM</option><option value="10:30">10:30 AM</option>
                            <option value="11:00">11:00 AM</option><option value="11:30">11:30 AM</option>
                            <option value="12:00">12:00 PM</option><option value="12:30">12:30 PM</option>
                            <option value="13:00">1:00 PM</option><option value="13:30">1:30 PM</option>
                            <option value="14:00">2:00 PM</option><option value="14:30">2:30 PM</option>
                            <option value="15:00">3:00 PM</option><option value="15:30">3:30 PM</option>
                            <option value="16:00">4:00 PM</option><option value="16:30">4:30 PM</option>
                            <option value="17:00">5:00 PM</option>
                        </select>
                    </label>
                </div>
                <button type="button" id="visit-schedule-save-btn" class="btn-control submit-primary" style="width:100%; padding:16px 20px; border-radius:14px;">Save Schedule</button>
            </div>`;
        document.body.appendChild(modal);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

        const startTimeSelect = modal.querySelector('#visit-start-time');
        const endTimeSelect = modal.querySelector('#visit-end-time');
        if (startTimeSelect && endTimeSelect) {
            startTimeSelect.addEventListener('change', () => {
                const val = startTimeSelect.value;
                if (!val) return;
                const [h, m] = val.split(':').map(Number);
                const endH = String(Math.min(17, h + 1)).padStart(2, '0');
                const endM = String(m).padStart(2, '0');
                const candidate = `${endH}:${endM}`;
                if (Array.from(endTimeSelect.options).some(o => o.value === candidate)) {
                    endTimeSelect.value = candidate;
                }
            });
        }

        modal.querySelector('#visit-schedule-modal-close')?.addEventListener('click', () => modal.remove());
        modal.querySelector('#visit-schedule-save-btn')?.addEventListener('click', async (e) => {
            const saveBtn = e.target.closest('button');
            const confirmedDate = modal.querySelector('#visit-confirmed-date')?.value || "";
            const startTime = modal.querySelector('#visit-start-time')?.value || "";
            const endTime = modal.querySelector('#visit-end-time')?.value || "";
            if (!confirmedDate || !startTime || !endTime) {
                alert("Please enter the confirmed date and visit window.");
                return;
            }

            const currentNow = new Date();
            const y = currentNow.getFullYear();
            const m = String(currentNow.getMonth() + 1).padStart(2, '0');
            const d = String(currentNow.getDate()).padStart(2, '0');
            const currentTodayStr = `${y}-${m}-${d}`;

            if (confirmedDate < currentTodayStr) {
                alert("You cannot schedule a visit in the past. Please select today or an upcoming date.");
                return;
            }

            const [startH, startM] = startTime.split(':').map(Number);
            const [endH, endM] = endTime.split(':').map(Number);
            const startMinutes = startH * 60 + startM;
            const endMinutes = endH * 60 + endM;

            if (endMinutes <= startMinutes) {
                alert("The visit end time must be after the start time.");
                return;
            }

            if (confirmedDate === currentTodayStr) {
                const currentMinutes = currentNow.getHours() * 60 + currentNow.getMinutes();
                if (startMinutes <= currentMinutes) {
                    const ampm = startH < 12 ? 'AM' : 'PM';
                    const h12 = startH % 12 || 12;
                    const timeFormatted = `${h12}:${String(startM).padStart(2, '0')} ${ampm}`;
                    alert(`The visit start time (${timeFormatted}) has already passed for today. Please select an upcoming time.`);
                    return;
                }
            }

            setButtonLoading(saveBtn, true, "Saving Schedule...");
            try {
                const response = await fetch("/agriculturist/finalize-visit-schedule", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ request_id: report?.id, confirmed_date: confirmedDate, start_time: startTime, end_time: endTime, status: "Visit Scheduled" }),
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The schedule could not be finalized.");
                    setButtonLoading(saveBtn, false);
                    return;
                }
                report.status = "Visit Scheduled";
                report.visitArchived = true;
                report.visitDiscussionExpanded = false;
                report.visitScheduleTitle = data.schedule_title || "Visit Scheduled";
                report.visitScheduleStamp = data.schedule_stamp || "";
                await loadVisitDiscussion(report);
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                if (typeof window.renderReportsGrid === "function") {
                    try { window.renderReportsGrid(); } catch (gridErr) { console.debug(gridErr); }
                }
                modal.remove();
                alert(data.message || "The visit schedule has been finalized.");
            } catch (error) {
                alert("The schedule could not be finalized right now.");
                setButtonLoading(saveBtn, false);
            }
        });
    }

    function openReportPhotoLightbox(url, filename) {
        const lightbox = document.getElementById("cocoscan-photo-lightbox");
        const img = document.getElementById("cocoscan-photo-lightbox-img");
        const downloadBtn = document.getElementById("cocoscan-photo-download-btn");
        if (!lightbox || !img) {
            window.open(url, "_blank");
            return;
        }

        const resolvedUrl = resolveReportImageUrl(url);
        img.src = resolvedUrl;
        img.alt = filename || "Visit inspection photo";

        if (downloadBtn) {
            downloadBtn.href = resolvedUrl;
            downloadBtn.setAttribute("download", filename || "visit_photo.jpg");
            downloadBtn.onclick = async function (e) {
                e.preventDefault();
                try {
                    const resp = await fetch(resolvedUrl);
                    if (!resp.ok) throw new Error("Fetch failed");
                    const blob = await resp.blob();
                    const blobUrl = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = blobUrl;
                    link.download = filename || "visit_photo.jpg";
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    setTimeout(() => URL.revokeObjectURL(blobUrl), 1500);
                } catch (err) {
                    window.open(resolvedUrl, "_blank");
                }
            };
        }

        lightbox.style.display = "flex";
        document.body.style.overflow = "hidden";
    }

    function closeReportPhotoLightbox() {
        const lightbox = document.getElementById("cocoscan-photo-lightbox");
        const img = document.getElementById("cocoscan-photo-lightbox-img");
        if (lightbox) {
            lightbox.style.display = "none";
        }
        if (img) {
            img.src = "";
        }
        document.body.style.overflow = "";
    }

    window.openReportPhotoLightbox = openReportPhotoLightbox;
    window.closeReportPhotoLightbox = closeReportPhotoLightbox;

    window.handleVisitImageUploadSelection = function(input) {
        if (!input || !input.files) return;
        const newFiles = Array.from(input.files);
        if (newFiles.length > 0) {
            currentVisitUploadFiles = currentVisitUploadFiles.concat(newFiles);
            renderVisitUploadPreviews();
        }
        input.value = "";
    };

    window.removeVisitUploadFile = function(index) {
        if (index >= 0 && index < currentVisitUploadFiles.length) {
            currentVisitUploadFiles.splice(index, 1);
            renderVisitUploadPreviews();
        }
    };

    function renderVisitUploadPreviews() {
        const grid = document.getElementById("workflow-visit-preview-grid");
        const statusText = document.getElementById("workflow-visit-upload-status-text");
        if (statusText) {
            statusText.textContent = currentVisitUploadFiles.length > 0
                ? `${currentVisitUploadFiles.length} photo(s) selected (tap to add more)`
                : "Tap to open your phone gallery directory";
        }
        if (!grid) return;
        grid.innerHTML = "";

        currentVisitUploadFiles.forEach((file, index) => {
            const card = document.createElement("div");
            card.style.cssText = "position:relative; border-radius:12px; overflow:hidden; aspect-ratio:1/1; background:#f8fafb; border:1px solid rgba(0,0,0,0.1); box-shadow:0 1px 3px rgba(0,0,0,0.06);";

            const img = document.createElement("img");
            try {
                img.src = URL.createObjectURL(file);
            } catch (e) {
                img.src = "";
            }
            img.alt = file.name || `Visit image ${index + 1}`;
            img.style.cssText = "width:100%; height:100%; object-fit:cover; display:block;";
            card.appendChild(img);

            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.title = "Remove image";
            removeBtn.setAttribute("aria-label", "Remove image");
            removeBtn.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            removeBtn.style.cssText = "position:absolute; top:5px; right:5px; border:none; background:#ef4444; color:#ffffff; border-radius:50%; width:24px; height:24px; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:12px; box-shadow:0 2px 5px rgba(0,0,0,0.25); transition:transform 0.15s ease, background 0.15s ease;";
            removeBtn.onmouseover = () => {
                removeBtn.style.transform = "scale(1.12)";
                removeBtn.style.background = "#dc2626";
            };
            removeBtn.onmouseout = () => {
                removeBtn.style.transform = "scale(1)";
                removeBtn.style.background = "#ef4444";
            };
            removeBtn.onclick = (e) => {
                e.stopPropagation();
                window.removeVisitUploadFile(index);
            };
            card.appendChild(removeBtn);

            grid.appendChild(card);
        });
    }

    if (typeof document !== "undefined") {
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                closeReportPhotoLightbox();
            }
        });
        document.addEventListener("DOMContentLoaded", () => {
            const lightbox = document.getElementById("cocoscan-photo-lightbox");
            if (lightbox) {
                lightbox.addEventListener("click", (e) => {
                    if (e.target === lightbox) {
                        closeReportPhotoLightbox();
                    }
                });
            }
        });
    }

    function renderVisitSummaryCard(report) {
        const visitCard = document.getElementById("report-visit-summary-card");
        const visitContent = document.getElementById("report-visit-summary-content");
        if (!visitCard || !visitContent) return;

        const visitSummary = String(report?.visit_summary || report?.visitSummary || "").trim();
        const rawImages = Array.isArray(report?.visitImages) && report.visitImages.length
            ? report.visitImages
            : (Array.isArray(report?.visit_images) ? report.visit_images : []);
        const visitImages = rawImages.map(item => {
            const rawUrl = typeof item === "object" && item !== null ? (item.image_url || item.url || item.src || "") : item;
            return resolveReportImageUrl(rawUrl);
        }).filter(Boolean);
        const hasVisitSummary = Boolean(visitSummary || visitImages.length > 0);

        if (!hasVisitSummary) {
            setDisplay(visitCard, false);
            visitContent.innerHTML = "";
            return;
        }

        let html = "";
        if (visitSummary) {
            html += `<p style="margin:0; font-size:0.95rem; color:#334155; line-height:1.6; white-space:pre-wrap;">${escapeHtml(visitSummary)}</p>`;
        }
        if (visitImages.length > 0) {
            html += `
                <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:${visitSummary ? '12px' : '0'};">
                    ${visitImages.map((url, idx) => `
                        <div style="position:relative; border-radius:10px; overflow:hidden; border:1px solid #cbd5e1; box-shadow:0 1px 3px rgba(0,0,0,0.08); background:#f8fafc; cursor:pointer;" onclick="openReportPhotoLightbox('${escapeHtml(url)}', 'visit_photo_${idx + 1}.jpg')" title="Click to view full photo">
                            <img src="${escapeHtml(url)}" alt="Visit photo ${idx + 1}" loading="lazy" style="height:90px; width:130px; object-fit:cover; display:block; transition:transform 0.2s ease;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        </div>
                    `).join('')}
                </div>
            `;
        }

        visitContent.innerHTML = html;
        setDisplay(visitCard, true, "block");
    }

    function renderResolutionDetailsCard(report) {
        const resolutionCard = document.getElementById("report-resolution-details-card");
        const resolutionContent = document.getElementById("report-resolution-details-content");
        if (!resolutionCard || !resolutionContent) return;

        const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
        const normalizedStatus = getStatusKey(report?.status || "");
        const isResolved = normalizedStatus === "resolved" || String(report?.status || "").toLowerCase() === "resolved";

        if (!isResolved) {
            setDisplay(resolutionCard, false);
            resolutionContent.innerHTML = "";
            return;
        }

        const hasCompletedVisit = Boolean(
            report?.visit_summary ||
            report?.visit_completed_at ||
            (Array.isArray(report?.visitImages) && report.visitImages.length > 0) ||
            (Array.isArray(report?.visit_images) && report.visit_images.length > 0)
        );

        let message = "";
        if (hasCompletedVisit) {
            message = `
                <div style="font-size:0.92rem; color:#334155; line-height:1.5; display:flex; flex-direction:column; gap:8px;">
                    <div><strong style="color:#1e293b;">${escapeHtml(t('modal.label_outcome', 'Outcome'))}:</strong> ${escapeHtml(t('modal.resolution_visit_completed_text', 'The agriculturist has completed the visit and marked the issue as resolved.'))}</div>
                    <div style="padding-top:6px; border-top:1px dashed #e2e8f0; margin-top:2px;">
                        <strong style="color:#1e293b;">${escapeHtml(t('modal.resolution_resolved_on', 'Resolved On:'))}</strong> 
                        <span style="color:#475569;">${formatTimestamp(report.visit_completed_at || report.updated_at || report.timestamp)}</span>
                    </div>
                </div>`;
        } else {
            message = `
                <div style="font-size:0.92rem; color:#334155; line-height:1.5; display:flex; flex-direction:column; gap:8px;">
                    <div><strong style="color:#1e293b;">${escapeHtml(t('modal.label_outcome', 'Outcome'))}:</strong> ${escapeHtml(t('modal.resolution_outcome_text', 'Issue resolved by following expert assessment.'))}</div>
                    <div style="padding-top:6px; border-top:1px dashed #e2e8f0; margin-top:2px;">
                        <strong style="color:#1e293b;">${escapeHtml(t('modal.resolution_resolved_on', 'Resolved On:'))}</strong> 
                        <span style="color:#475569;">${formatTimestamp(report.updated_at || report.timestamp)}</span>
                    </div>
                </div>`;
        }

        resolutionContent.innerHTML = `
            <div style="margin-top:4px; display:grid; gap:12px;">
                ${message}
            </div>`;

        setDisplay(resolutionCard, true, "block");
    }

    function renderResolvedDetailsCard(feedbackContainer, feedbackCard, report) {
        renderVisitSummaryCard(report);
        renderResolutionDetailsCard(report);
    }

    function renderWorkflowActions(mode, report = currentReportModalRecord) {
        const workflowCard = document.getElementById("workflow-actions-card");
        if (workflowCard) {
            workflowCard.remove();
        }
        const feedbackContainer = document.getElementById("report-farmer-feedback");
        const feedbackCard = document.getElementById('report-farmer-feedback-card');

        const normalizedStatus = getStatusKey(report?.status || "");
        const recommendationIssued = isRecommendationIssuedStatus(report?.status || "");
        const discussionStatuses = ["awaiting_confirmed_schedule", "visit_requested", "visit_scheduled"];
        const isVisitDiscussionState = discussionStatuses.includes(normalizedStatus);

        if (feedbackContainer) {
            feedbackContainer.innerHTML = "";
            if (feedbackCard) setDisplay(feedbackCard, false, 'block');
        }

        if (normalizedStatus === "resolved") {
            if (feedbackCard) setDisplay(feedbackCard, false, 'block');
            if (feedbackContainer) feedbackContainer.innerHTML = "";
            renderVisitSummaryCard(report);
            renderResolutionDetailsCard(report);
            return;
        }

        if (isVisitDiscussionState) {
            renderVisitDiscussionCard(mode, report);
            return;
        }

        if (mode === "farmer") {
            // Show farmer feedback card when an assessment or recommendation has been issued, but not if they already answered it.
            if (recommendationIssued && normalizedStatus !== "visit_requested" && normalizedStatus !== "resolved") {
                if (feedbackContainer) {
                    const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
                    feedbackContainer.innerHTML = `
                        <div style="display:grid; gap:14px; padding:6px 0;">
                            <div style="display:grid; gap:8px;">
                                <p style="font-size:0.92rem; color:#334155; margin:0; line-height:1.55;">
                                    ${t('modal.feedback_question', 'Did the initial recommendation and expert assessment resolve your issue?')}<br>
                                    <em style="font-size:0.72rem; color:#64748b;">${t('modal.feedback_subtext', 'If not, you can request an on-site visit and continue the workflow.')}</em>
                                </p>
                                <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:0;">
                                    <label style="display:flex; align-items:center; gap:8px; font-weight:600; color:#102a43;">
                                        <input type="radio" name="farmer-feedback-choice" value="resolved" checked style="accent-color:#059669;"> ${t('modal.feedback_yes', 'Yes')}
                                    </label>
                                    <label style="display:flex; align-items:center; gap:8px; font-weight:600; color:#102a43;">
                                        <input type="radio" name="farmer-feedback-choice" value="needs-assistance" style="accent-color:#be185d;"> ${t('modal.feedback_no', 'No')}
                                    </label>
                                </div>
                            </div>
                            <div id="farmer-visit-reason-section" style="display:none; display:grid; gap:8px;">
                                <label style="font-size:0.9rem; font-weight:600; color:#334155;">${t('modal.feedback_reason_label', 'Reason for requesting a visit')}</label>
                                <textarea id="farmer-visit-reason" class="notes-input-box" placeholder="${t('modal.feedback_reason_placeholder', 'Describe why you still need assistance...')}" style="min-height:110px; width:100%; box-sizing:border-box; padding:14px 16px;"></textarea>
                            </div>
                            <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:4px;">
                                <button id="farmer-submit-feedback-btn" class="btn-control submit-primary" type="button">${t('modal.btn_confirm_resolved', 'Confirm Resolved')}</button>
                            </div>
                        </div>`;
                    const feedbackRadios = feedbackContainer.querySelectorAll("input[name='farmer-feedback-choice']");
                    const reasonSection = feedbackContainer.querySelector("#farmer-visit-reason-section");
                    const submitFeedbackBtn = feedbackContainer.querySelector('#farmer-submit-feedback-btn');
                    const refreshReasonDisplay = () => {
                        const selectedValue = Array.from(feedbackRadios).find((input) => input.checked)?.value || "resolved";
                        const showReason = selectedValue === 'needs-assistance';
                        if (reasonSection) {
                            setDisplay(reasonSection, showReason, 'grid');
                        }
                        if (submitFeedbackBtn) {
                            submitFeedbackBtn.textContent = showReason ? t('modal.btn_request_visit', 'Request Visit') : t('modal.btn_confirm_resolved', 'Confirm Resolved');
                        }
                    };
                    feedbackRadios.forEach((input) => input.addEventListener('change', refreshReasonDisplay));
                    refreshReasonDisplay();
                    if (submitFeedbackBtn) {
                        submitFeedbackBtn.addEventListener('click', () => submitWorkflowAction('farmer-feedback'));
                    }
                    if (feedbackCard) {
                        setDisplay(feedbackCard, true, 'block');
                        const h4 = feedbackCard.querySelector('h4');
                        if (h4) {
                            h4.innerHTML = `<i class="fa-solid fa-calendar-check"></i> ${escapeHtml(t('modal.followup_section_title', 'Follow-up'))}`;
                        }
                    }
                }
            } else if (normalizedStatus === "visit_requested") {
                const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
                if (feedbackContainer) {
                    const reasonDisplay = report.farmerFeedbackReason ? `<p style="margin:0; font-size:0.95rem; color:#334155;"><strong>${escapeHtml(t('modal.label_reason', 'Reason'))}:</strong> ${escapeHtml(report.farmerFeedbackReason)}</p>` : "";
                    const scheduleDisplay = Array.isArray(report.farmerSchedules) && report.farmerSchedules.length
                        ? `<div style="display:grid; gap:6px; padding-top:8px;">${report.farmerSchedules.map(s => `<div style="font-size:0.95rem; color:#0f172a;">• ${escapeHtml(s.display)}</div>`).join("")}</div>`
                        : "";
                    const message = `<p style="font-size:0.92rem; color:#334155; margin:0;">${escapeHtml(t('modal.visit_requested_notice', 'Your visit request was submitted successfully. The agriculturist will review your preferred schedules.'))}</p>${reasonDisplay}${scheduleDisplay}`;
                    feedbackContainer.innerHTML = `
                        <div style="margin-top:10px; display:grid; gap:12px;">
                            ${message}
                        </div>`;
                    if (feedbackCard) {
                        setDisplay(feedbackCard, true, 'block');
                        const h4 = feedbackCard.querySelector('h4');
                        if (h4) {
                            h4.innerHTML = `<i class="fa-solid fa-calendar-check"></i> ${escapeHtml(t('modal.followup_section_title', 'Follow-up'))}`;
                        }
                    }
                }
            }
        }
    }

    /* Helper functions for dynamic farmer schedule rows inside the feedback card */
    function addFarmerScheduleRow(container, dateVal = "", timeVal = "") {
        if (!container) return;
        const existing = container.querySelectorAll('.farmer-schedule-row');
        if (existing.length >= 3) return;
        const idx = existing.length + 1;
        const localNow = new Date();
        const curY = localNow.getFullYear();
        const curM = String(localNow.getMonth() + 1).padStart(2, '0');
        const curD = String(localNow.getDate()).padStart(2, '0');
        const todayStr = `${curY}-${curM}-${curD}`;
        const row = document.createElement('div');
        row.className = 'farmer-schedule-row';
        row.style.display = 'grid';
        row.style.gridTemplateColumns = '1fr';
        row.style.gap = '12px';
        row.style.padding = '14px';
        row.style.marginBottom = '14px';
        row.style.borderRadius = '16px';
        row.style.backgroundColor = '#fff';
        row.innerHTML = `
            <div style="display:grid; gap:12px;">
                <strong style="font-size:0.95rem; color:#102a43;">Preferred Schedule #${idx}</strong>
                <label style="display:grid; gap:4px; font-size:0.9rem; color:#334155;">
                    <span style="font-weight:500;">Date</span>
                    <input type="date" class="farmer-schedule-date schedule-input" min="${todayStr}" value="${escapeHtml(dateVal)}">
                </label>

                <label style="display:grid; gap:4px; font-size:0.9rem; color:#334155;">
                    <span style="font-weight:500;">Time</span>
                    <select class="farmer-schedule-time schedule-input" style="padding:12px 14px; border-radius:12px; border:1px solid #e6e6e6; min-height:48px; background-color:#fff;">
                        <option value="" disabled ${!timeVal ? "selected" : ""}>Select time</option>
                        ${['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00'].map(val => {
            let h = parseInt(val.substring(0, 2), 10);
            let ampm = h < 12 ? 'AM' : 'PM';
            let h12 = h <= 12 ? h : h - 12;
            if (h12 === 0) h12 = 12;
            let display = h12 + val.substring(2) + ' ' + ampm;
            return `<option value="${val}" ${timeVal === val ? "selected" : ""}>${display}</option>`;
        }).join('')}
                    </select>
                </label>
            </div>
            <button type="button" class="btn-control cancel-secondary remove-schedule-btn" style="min-height:36px; padding:10px 12px; white-space:nowrap; width:100%; margin-top:8px;">Remove</button>
        `;
        container.appendChild(row);
        row.querySelector('.remove-schedule-btn').addEventListener('click', () => { row.remove(); });
    }

    function collectFarmerSchedules(container) {
        if (!container) return [];
        const rows = Array.from(container.querySelectorAll('.farmer-schedule-row'));
        const localNow = new Date();
        const curY = localNow.getFullYear();
        const curM = String(localNow.getMonth() + 1).padStart(2, '0');
        const curD = String(localNow.getDate()).padStart(2, '0');
        const todayStr = `${curY}-${curM}-${curD}`;

        const schedules = rows.map(r => {
            const d = r.querySelector('.farmer-schedule-date')?.value || '';
            const t = r.querySelector('.farmer-schedule-time')?.value || '';
            if (d && d < todayStr) return null;
            let display = '';
            if (d && t) {
                try {
                    const dt = new Date(`${d}T${t}`);
                    display = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(dt) + new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }).format(dt);
                } catch (e) { display = `${d} ${t}`; }
            }
            return { date: d, time: t, display };
        }).filter(Boolean).filter(s => s.date && s.time);
        return schedules.slice(0, 3);
    }

    async function submitWorkflowAction(actionName, clickedBtn = null) {
        const workflowInput = document.getElementById("workflow-detail-input");
        const report = currentReportModalRecord;
        if (!report?.id) {
            alert("This report is missing an identifier.");
            return;
        }

        const activeBtn = clickedBtn || (typeof event !== 'undefined' && event?.target?.closest ? event.target.closest('button') : null) || document.querySelector('#workflow-actions-buttons button') || document.querySelector('#report-farmer-feedback-card button');
        setButtonLoading(activeBtn, true, "Submitting...");

        const formData = new FormData();
        formData.append("report_id", report.id);

        if (actionName === "submit-assessment") {
            const detail = (workflowInput?.value || "").trim();
            if (!detail) {
                setButtonLoading(activeBtn, false);
                alert("Please provide assessment notes before submitting.");
                return;
            }
            formData.append("assessment_notes", detail);
            try {
                const response = await fetch("/agriculturist/submit-assessment", { method: "POST", body: formData });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The assessment could not be saved.");
                    setButtonLoading(activeBtn, false);
                    return;
                }
                report.status = "assessment_issued";
                applyStatusStyle(report);
                if (typeof window.renderReportsGrid === "function") {
                    try { window.renderReportsGrid(); } catch (e) { console.debug(e); }
                }
                renderWorkflowActions(currentReportModalMode, report);
                // Close modal for agriculturist after submit
                if (currentReportModalMode === 'agriculturist') closeReportModal();
                alert(data.message || "Assessment notes saved.");
                closeReportModal();
                window.location.reload();
            } catch (error) {
                alert("The assessment could not be saved right now.");
                setButtonLoading(activeBtn, false);
            }
            return;
        }

        if (actionName === "farmer-feedback") {
            const feedbackChoice = document.querySelector("input[name='farmer-feedback-choice']:checked")?.value || "resolved";
            formData.append("confirmation", feedbackChoice);
            let feedbackReason = "";
            if (feedbackChoice === "resolved") {
                formData.append("reason", "");
                report.farmerFeedbackConfirmation = "resolved";
            } else {
                feedbackReason = document.getElementById("farmer-visit-reason")?.value?.trim() || "";
                if (!feedbackReason) {
                    setButtonLoading(activeBtn, false);
                    alert("Please provide a reason before submitting the visit request.");
                    return;
                }
                formData.append("reason", feedbackReason);
                report.farmerFeedbackReason = feedbackReason;
                report.farmerFeedbackConfirmation = "needs-assistance";
            }

            const isOffline = typeof navigator !== 'undefined' && (!navigator.onLine || (typeof localStorage !== 'undefined' && localStorage.getItem('cocoscan_offline_active') === 'true'));
            if (isOffline) {
                queueOfflineAction({
                    type: 'farmer-feedback',
                    report_id: report.id,
                    payload: { confirmation: feedbackChoice, reason: feedbackReason }
                });
                report.status = feedbackChoice === "resolved" ? "resolved" : "Awaiting Confirmed Schedule";
                if (feedbackChoice !== "resolved") {
                    report.visitArchived = false;
                    report.visitScheduleStamp = "";
                }
                updateLocalReportState(report.id, (r) => ({
                    ...r,
                    status: report.status,
                    visit_request_reason: feedbackReason
                }));
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
                alert(t('modal.feedback_offline_saved', "Offline Mode: Your response has been saved locally and will be automatically submitted once your connection is restored."));
                closeReportModal();
                return;
            }

            try {
                const response = await fetch("/farmer/submit-assessment-feedback", { method: "POST", body: formData });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    if (!navigator.onLine || response.status === 0 || response.status >= 500) {
                        queueOfflineAction({
                            type: 'farmer-feedback',
                            report_id: report.id,
                            payload: { confirmation: feedbackChoice, reason: feedbackReason }
                        });
                        report.status = feedbackChoice === "resolved" ? "resolved" : "Awaiting Confirmed Schedule";
                        if (feedbackChoice !== "resolved") {
                            report.visitArchived = false;
                            report.visitScheduleStamp = "";
                        }
                        updateLocalReportState(report.id, (r) => ({
                            ...r,
                            status: report.status,
                            visit_request_reason: feedbackReason
                        }));
                        applyStatusStyle(report);
                        renderWorkflowActions(currentReportModalMode, report);
                        const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
                        alert(t('modal.feedback_offline_saved', "Offline Mode: Your response has been saved locally and will be automatically submitted once your connection is restored."));
                        closeReportModal();
                        return;
                    }
                    alert(data.message || data.error || "The feedback could not be saved.");
                    setButtonLoading(activeBtn, false);
                    return;
                }
                report.status = feedbackChoice === "resolved" ? "resolved" : "Awaiting Confirmed Schedule";
                if (feedbackChoice !== "resolved") {
                    report.visitArchived = false;
                    report.visitScheduleStamp = "";
                }
                updateLocalReportState(report.id, (r) => ({
                    ...r,
                    status: report.status,
                    visit_request_reason: feedbackReason
                }));
                applyStatusStyle(report);
                if (typeof window.renderReportsGrid === "function") {
                    try { window.renderReportsGrid(); } catch (e) { console.debug(e); }
                }
                if (feedbackChoice !== "resolved") {
                    await loadVisitDiscussion(report);
                }
                renderWorkflowActions(currentReportModalMode, report);
                alert(data.message || "Feedback saved.");
                closeReportModal();
                window.location.reload();
            } catch (error) {
                queueOfflineAction({
                    type: 'farmer-feedback',
                    report_id: report.id,
                    payload: { confirmation: feedbackChoice, reason: feedbackReason }
                });
                report.status = feedbackChoice === "resolved" ? "resolved" : "Awaiting Confirmed Schedule";
                if (feedbackChoice !== "resolved") {
                    report.visitArchived = false;
                    report.visitScheduleStamp = "";
                }
                updateLocalReportState(report.id, (r) => ({
                    ...r,
                    status: report.status,
                    visit_request_reason: feedbackReason
                }));
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                const t = (k, def) => (window.CocoScanI18n ? window.CocoScanI18n.t(k, def) : def);
                alert(t('modal.feedback_offline_saved', "Offline Mode: Your response has been saved locally and will be automatically submitted once your connection is restored."));
                closeReportModal();
            }
            return;
        }

        if (actionName === "confirm-selected-schedule") {
            const selectedSlot = document.querySelector("input[name='agri-availability-choice']:checked")?.value;
            const parsed = parseAvailabilitySlot(selectedSlot);
            formData.append("decision", "accept");
            if (parsed?.date) {
                formData.append("preferred_date", parsed.date);
                formData.append("preferred_time", parsed.windowLabel || TIME_WINDOW_DEFINITIONS[parsed.windowKey]?.label || "Morning");
            }
            try {
                const response = await fetch("/agriculturist/review-visit-request", { method: "POST", body: formData });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The selected schedule could not be saved.");
                    setButtonLoading(activeBtn, false);
                    return;
                }
                report.status = "visit_scheduled";
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                alert(data.message || "Visit scheduled successfully.");
                closeReportModal();
                window.location.reload();
            } catch (error) {
                alert("The selected schedule could not be saved right now.");
                setButtonLoading(activeBtn, false);
            }
            return;
        }

        if (actionName === "propose-selected-schedule") {
            const proposedDate = document.getElementById("agri-proposed-date")?.value || "";
            const proposedWindow = document.getElementById("agri-proposed-window")?.value || "morning";
            const preferredTime = TIME_WINDOW_DEFINITIONS[proposedWindow]?.label || "Morning";
            formData.append("decision", "accept");
            if (!proposedDate) {
                setButtonLoading(activeBtn, false);
                alert("Please select a proposed date before continuing.");
                return;
            }
            formData.append("preferred_date", proposedDate);
            formData.append("preferred_time", preferredTime);
            try {
                const response = await fetch("/agriculturist/review-visit-request", { method: "POST", body: formData });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The proposed schedule could not be saved.");
                    setButtonLoading(activeBtn, false);
                    return;
                }
                report.status = "visit_scheduled";
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                alert(data.message || "Visit scheduled successfully.");
                closeReportModal();
                window.location.reload();
            } catch (error) {
                alert("The proposed schedule could not be saved right now.");
                setButtonLoading(activeBtn, false);
            }
            return;
        }

        if (actionName === "accept-visit-request" || actionName === "reject-visit-request") {
            const decision = actionName === "accept-visit-request" ? "accept" : "reject";
            const detail = (workflowInput?.value || "").trim();
            formData.append("decision", decision);
            if (decision === "accept") {
                // Allow selecting from farmer-provided schedules or a custom date/time
                const selectedIdx = document.querySelector("input[name='agri-selected-schedule']:checked")?.value;
                if (selectedIdx !== undefined && selectedIdx !== null && report.farmerSchedules && report.farmerSchedules[selectedIdx]) {
                    const picked = report.farmerSchedules[selectedIdx];
                    formData.append("preferred_date", picked.date);
                    formData.append("preferred_time", picked.time || "");
                } else {
                    const preferredDate = document.getElementById("visit-review-date")?.value || "";
                    const preferredTime = document.getElementById("visit-review-time")?.value || "";
                    if (!preferredDate || !preferredTime) {
                        setButtonLoading(activeBtn, false);
                        alert("Please confirm the visit date and time before accepting the request.");
                        return;
                    }
                    formData.append("preferred_date", preferredDate);
                    formData.append("preferred_time", preferredTime);
                }
            } else {
                if (!detail) {
                    setButtonLoading(activeBtn, false);
                    alert("Please add a rejection reason before submitting.");
                    return;
                }
                formData.append("reason", detail);
            }
            try {
                const response = await fetch("/agriculturist/review-visit-request", { method: "POST", body: formData });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The visit review could not be saved.");
                    setButtonLoading(activeBtn, false);
                    return;
                }
                report.status = decision === "accept" ? "visit_scheduled" : "assessment_issued";
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                if (typeof window.renderReportsGrid === "function") {
                    try { window.renderReportsGrid(); } catch (e) { console.debug(e); }
                }
                alert(data.message || "Visit request updated.");
                closeReportModal();
                window.location.reload();
            } catch (error) {
                alert("The visit review could not be saved right now.");
                setButtonLoading(activeBtn, false);
            }
            return;
        }

        if (actionName === "complete-visit") {
            const detail = (workflowInput?.value || "").trim();
            if (!detail) {
                setButtonLoading(activeBtn, false);
                alert("Please add a visit summary before submitting.");
                return;
            }
            if (!currentVisitUploadFiles || !currentVisitUploadFiles.length) {
                setButtonLoading(activeBtn, false);
                alert("Please upload at least one visit image before submitting.");
                return;
            }
            formData.append("visit_summary", detail);
            currentVisitUploadFiles.forEach((file) => formData.append("visit_images", file));
            try {
                const response = await fetch("/agriculturist/complete-visit", { method: "POST", body: formData });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The visit summary could not be saved.");
                    setButtonLoading(activeBtn, false);
                    return;
                }
                report.status = "resolved";
                applyStatusStyle(report);
                await loadVisitDiscussion(report);
                renderWorkflowActions(currentReportModalMode, report);
                alert(data.message || "Visit details saved.");
                closeReportModal();
                window.location.reload();
            } catch (error) {
                alert("The visit summary could not be saved right now.");
                setButtonLoading(activeBtn, false);
            }
            return;
        }

        if (actionName === "submit-final-remarks") {
            const detail = (workflowInput?.value || "").trim();
            const additionalNotes = document.getElementById("workflow-additional-notes")?.value?.trim() || "";
            if (!detail) {
                setButtonLoading(activeBtn, false);
                alert("Please provide final remarks before submitting.");
                return;
            }
            formData.append("final_remarks", detail);
            if (additionalNotes) {
                formData.append("feedback", additionalNotes);
            }
            try {
                const response = await fetch("/agriculturist/submit-final-remarks", { method: "POST", body: formData });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The final remarks could not be saved.");
                    setButtonLoading(activeBtn, false);
                    return;
                }
                report.status = "final_remarks_issued";
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                alert(data.message || "Final remarks saved.");
                closeReportModal();
                window.location.reload();
            } catch (error) {
                alert("The final remarks could not be saved right now.");
                setButtonLoading(activeBtn, false);
            }
            return;
        }

        if (actionName === "mark-resolved") {
            const detail = (workflowInput?.value || "").trim();
            if (detail) {
                formData.append("resolution_note", detail);
            }
            try {
                const response = await fetch("/agriculturist/mark-resolved", { method: "POST", body: formData });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.success) {
                    alert(data.message || "The case could not be marked resolved.");
                    setButtonLoading(activeBtn, false);
                    return;
                }
                report.status = "resolved";
                applyStatusStyle(report);
                renderWorkflowActions(currentReportModalMode, report);
                alert(data.message || "The report has been marked as resolved.");
                closeReportModal();
                window.location.reload();
            } catch (error) {
                alert("The case could not be marked resolved right now.");
                setButtonLoading(activeBtn, false);
            }
            return;
        }

        setButtonLoading(activeBtn, false);
        alert("This workflow step is not available yet.");
    }

    function closeReportModal() {
        abortActiveReportModalSubmission();
        stopVisitDiscussionPoll();
        currentVisitUploadFiles = [];
        if (typeof closeReportPhotoLightbox === "function") {
            closeReportPhotoLightbox();
        }

        const modalRoot = getModalRoot();
        if (modalRoot) {
            modalRoot.classList.remove("open-modal");
            modalRoot.setAttribute("aria-hidden", "true");
        }

        document.getElementById("visit-schedule-mini-modal")?.remove();
        document.getElementById("visit-reschedule-mini-modal")?.remove();

        currentReportModalRecord = null;
        currentReportModalMode = "farmer";

        const followUpModal = document.getElementById("followup-modal");
        if (followUpModal && followUpModal.classList.contains("open-modal")) {
            followUpModal.classList.remove("open-modal");
        }

        if (typeof window.resetWorkflowStateToHome === "function") {
            window.resetWorkflowStateToHome();
        }

        // Clean up URL query params if report_id or mode were set
        if (window.location.search) {
            try {
                const params = new URLSearchParams(window.location.search);
                if (params.has('report_id') || params.has('mode')) {
                    params.delete('report_id');
                    params.delete('mode');
                    const newQuery = params.toString() ? '?' + params.toString() : '';
                    window.history.replaceState({}, '', window.location.pathname + newQuery);
                }
            } catch (e) {
                console.debug("Query param cleanup skipped", e);
            }
        }
    }

    async function populateWeather(report) {
        const weather = report.weather || {};
        const hasWeatherData = weather && Object.keys(weather).length > 0 && weather.temp !== undefined;

        if (!hasWeatherData) {
            const snapshot = await fetchWeatherSnapshot(report.latitude, report.longitude);
            if (currentReportModalRecord && currentReportModalRecord.id === report.id && currentReportModalMode === report.mode) {
                currentReportModalRecord.weather = snapshot;
                renderWeather(snapshot);
            }
            return;
        }

        renderWeather(weather);
    }

    function renderWeather(weather) {
        const locationNode = document.getElementById("report-weather-location");
        const tempNode = document.getElementById("report-weather-temp");
        const humidityNode = document.getElementById("report-weather-humidity");
        const windNode = document.getElementById("report-weather-wind");
        const rainfallNode = document.getElementById("report-weather-rainfall");

        if (locationNode) locationNode.textContent = weatherLine(weather?.location, "");
        if (tempNode) tempNode.textContent = weatherLine(weather?.temp, weather?.temp === "--" ? "" : "°C");
        if (humidityNode) humidityNode.textContent = weatherLine(weather?.humidity, weather?.humidity === "--" ? "" : "%");
        if (windNode) windNode.textContent = weatherLine(weather?.wind, weather?.wind === "--" ? "" : " km/h");
        if (rainfallNode) rainfallNode.textContent = weather?.is_down ? "Weather data unavailable" : `Rainfall: ${weatherLine(weather?.rainfall, weather?.rainfall === "--" ? "" : " mm")}`;
    }

    async function openReportModal(reportData = {}, mode) {
        const modalRoot = getModalRoot();
        if (!modalRoot) {
            return;
        }

        const activeUserRole = getCurrentUserRole();
        let resolvedMode = mode;
        const currentPath = ((window.location && window.location.pathname) || "").toLowerCase();
        const isFarmerPath = currentPath.startsWith("/farmer");

        if (!isFarmerPath && (resolvedMode === "farmer" || !resolvedMode)) {
            resolvedMode = activeUserRole !== "farmer" ? activeUserRole : "admin";
        }

        if (resolvedMode === "scan" || reportData?.mode === "scan") {
            resolvedMode = "scan";
        } else if (resolvedMode && ["agriculturist", "agri", "agri_expert"].includes(String(resolvedMode).toLowerCase())) {
            resolvedMode = "agriculturist";
        } else if (activeUserRole === "agriculturist") {
            resolvedMode = "agriculturist";
        } else if (resolvedMode && ["farmer", "admin", "lgu"].includes(String(resolvedMode).toLowerCase())) {
            resolvedMode = String(resolvedMode).toLowerCase();
        } else {
            resolvedMode = activeUserRole || "admin";
        }

        if (!isFarmerPath && resolvedMode === "farmer") {
            resolvedMode = activeUserRole !== "farmer" ? activeUserRole : "admin";
        }

        currentReportModalMode = resolvedMode;
        currentReportModalRecord = normalizeReportData({ ...reportData, mode: currentReportModalMode });

        let report = currentReportModalRecord;
        try { console.debug("[report_modal] opening report", { id: report.id, status: report.status, expertRecommendations: report.expertRecommendations }); } catch (e) { /* noop */ }

        // Immediately reveal the modal overlay
        modalRoot.classList.add("open-modal");
        modalRoot.setAttribute("aria-hidden", "false");
        setReportModalSubmissionState(false);

        const resizableContainer = document.getElementById("report-image-resizable-container");
        if (resizableContainer) {
            resizableContainer.style.width = "";
            resizableContainer.style.height = "";
            const img = resizableContainer.querySelector("img");
            if (img) {
                img.style.setProperty("width", "100%", "important");
                img.style.setProperty("height", "100%", "important");
                img.style.setProperty("max-height", "none", "important");
                img.style.setProperty("aspect-ratio", "auto", "important");
                img.style.setProperty("object-fit", "cover", "important");
            }
        }
        initResizableImageContainer();

        if (currentReportModalMode !== "farmer" || !isFarmerPath) {
            const englishLabels = {
                "modal.summary_title": "Report Summary",
                "modal.btn_close": "Close",
                "modal.btn_print": "Print report",
                "modal.status_label": "Status:",
                "modal.possible_pest_eyebrow": "POSSIBLE PEST",
                "modal.detected_pest_eyebrow": "DETECTED PEST",
                "modal.confidence_label": "Confidence:",
                "modal.pending_validation_notice": "This is not a final result and will be validated by the agriculturist.",
                "modal.farmer_notes_title": "Farmer Notes",
                "modal.farmer_notes_placeholder": "Describe what you observed on your coconut tree...",
                "modal.notes_empty": "No notes logged.",
                "modal.additional_images_title": "Additional Images",
                "modal.additional_images_empty": "No additional images uploaded.",
                "modal.expert_assessment_title": "Expert Assessment",
                "modal.expert_assessment_empty": "No expert assessment available yet.",
                "modal.farmer_label": "Farmer:",
                "modal.location_label": "Location:",
                "modal.scanned_label": "Scanned:",
                "modal.followup_section_title": "Follow-up",
                "modal.resolution_details_title": "Resolution Details",
                "modal.discussion_toggle_title": "Visit Request Discussion",
                "modal.tip_label": "Tip:",
                "modal.btn_request_reschedule": "Request Reschedule",
                "modal.discussion_closed": "The scheduling discussion has been closed.",
                "modal.visit_summary_title": "Visit Summary",
                "modal.btn_validate_correct": "Mark as Verified",
                "modal.btn_correct_result": "Re-verify Result",
                "modal.agri_verification_title": "Expert Assessment & AI Verification",
                "modal.initial_reco_title": "Initial Recommendations",
                "modal.verified_reco_title": "Recommendations",
                "modal.safe_actions_title": "Safe Precautionary Actions",
                "modal.safe_actions_notice": "You may proceed with these safe precautionary steps while waiting for final confirmation from the agriculturist.",
                "modal.initial_reco_desc": "These are general precautionary recommendations for the detected pest to help your initial decision while awaiting agriculturist verification.",
                "modal.initial_reco_subtext": "Tap the question mark icon for more details.",
                "modal.supporting_photos_title": "Supporting Photos (optional)",
                "modal.supporting_photos_prompt": "Add Extra Field Images",
                "modal.supporting_photos_subtext": "Tap to open your phone gallery directory",
                "modal.supporting_photos_error": "You can upload a maximum of 3 supporting photos only.",
                "modal.expert_assessment_issued": "Expert assessment issued.",
                "modal.initial_reco_empty": "No initial recommendations available."
            };
            modalRoot.querySelectorAll("[data-i18n]").forEach(el => {
                const key = el.getAttribute("data-i18n");
                if (englishLabels[key]) {
                    const icon = el.querySelector("i, svg, img");
                    if (icon) {
                        const iconClone = icon.cloneNode(true);
                        el.innerHTML = "";
                        el.appendChild(iconClone);
                        el.appendChild(document.createTextNode(" " + englishLabels[key]));
                    } else {
                        el.textContent = englishLabels[key];
                    }
                }
            });
        }

        const renderModalFields = () => {
            const pestTitle = document.getElementById("report-pest-title");
            const confidenceNode = document.getElementById("report-confidence");
            const primaryImage = document.getElementById("report-primary-image");
            const farmerNameNode = document.getElementById("report-farmer-name");
            const locationNode = document.getElementById("report-location-text");
            const timestampNode = document.getElementById("report-timestamp-text");
            const gpsNode = document.getElementById("report-gps-text");
            const notesInput = document.getElementById("field-notes-capture");
            const notesDisplay = document.getElementById("report-notes-display");
            const expertInput = document.getElementById("expert-notes-input");
            const expertCard = document.getElementById("report-expert-card");

            const statusKey = getStatusKey(report?.status || "");
            const assessmentAlreadyIssued = ["assessment_issued", "recommendation_issued", "waiting_for_agriculturist_confirmation", "waiting_agriculturist_confirmation", "awaiting_confirmed_schedule", "visit_requested", "visit_scheduled", "visit_completed", "final_remarks_issued", "resolved", "closed"].includes(statusKey) || (Array.isArray(report.expertRecommendations) && report.expertRecommendations.length > 0);

            const cleanPest = formatCleanPestName(report.pest);
            if (pestTitle) pestTitle.textContent = cleanPest;

            // Result Display & Verification Status Indicators
            const eyebrowPending = document.getElementById("pest-eyebrow-pending");
            const eyebrowVerified = document.getElementById("pest-eyebrow-verified");
            const pendingNotice = document.getElementById("report-pending-validation-notice");
            const confidenceRow = document.getElementById("report-confidence-row");

            if (assessmentAlreadyIssued) {
                // Verified Final Result State:
                // Show DETECTED PEST badge and remove warning notice banner
                if (eyebrowPending) setDisplay(eyebrowPending, false);
                if (eyebrowVerified) {
                    setDisplay(eyebrowVerified, true, "inline-flex");
                    eyebrowVerified.innerHTML = `<span id="pest-verified-by-text" data-i18n="modal.detected_pest_eyebrow">${t('modal.detected_pest_eyebrow', 'DETECTED PEST')}</span>`;
                }
                if (pendingNotice) setDisplay(pendingNotice, false);

                // Update confidence row into: "Verified by Agriculturist (First Name)"
                if (confidenceRow) {
                    const verifier = report.reviewer_name || "";
                    const firstName = getVerifiedFirstName(verifier);
                    const verifiedText = firstName ? `Verified by Agriculturist ${escapeHtml(firstName)}` : `Verified by Agriculturist`;
                    confidenceRow.innerHTML = `<span id="pest-verified-by-text">${verifiedText}</span>`;
                }
            } else {
                // Pending Validation State
                if (eyebrowPending) {
                    setDisplay(eyebrowPending, true, "inline-flex");
                    eyebrowPending.innerHTML = `<span data-i18n="modal.possible_pest_eyebrow">${t('modal.possible_pest_eyebrow', 'POSSIBLE PEST')}</span>`;
                }
                if (eyebrowVerified) setDisplay(eyebrowVerified, false);
                if (pendingNotice) setDisplay(pendingNotice, true, "flex");
                if (confidenceRow) {
                    confidenceRow.innerHTML = `<span data-i18n="modal.confidence_label">${t('modal.confidence_label', 'Confidence:')}</span> <span id="report-confidence">${escapeHtml(report.confidence || '--')}</span>`;
                }
            }
            
            const verifiedSelect = document.getElementById("agri-verified-pest-select");
            const customInput = document.getElementById("agri-custom-pest-input");
            const customWrap = document.getElementById("agri-custom-pest-wrap");
            if (verifiedSelect) {
                const pestName = String(report.pest || "").toLowerCase();
                if (pestName.includes("brontispa")) {
                    verifiedSelect.value = "Brontispa";
                    if (customInput) customInput.value = "";
                    if (customWrap) customWrap.style.display = "none";
                } else if (pestName.includes("rhino") || pestName.includes("beetle")) {
                    verifiedSelect.value = "Rhinoceros Beetle";
                    if (customInput) customInput.value = "";
                    if (customWrap) customWrap.style.display = "none";
                } else if (pestName.includes("healthy") || pestName.includes("malusog")) {
                    verifiedSelect.value = "Healthy Coconut Leaf";
                    if (customInput) customInput.value = "";
                    if (customWrap) customWrap.style.display = "none";
                } else if (pestName.includes("not a coconut") || pestName.includes("not coconut") || pestName.includes("hindi larawan")) {
                    verifiedSelect.value = "Not a Coconut Leaf Image";
                    if (customInput) customInput.value = "";
                    if (customWrap) customWrap.style.display = "none";
                } else if (report.pest) {
                    verifiedSelect.value = "custom";
                    if (customInput) customInput.value = report.pest;
                    if (customWrap) customWrap.style.display = "block";
                } else {
                    verifiedSelect.value = "Healthy Coconut Leaf";
                    if (customInput) customInput.value = "";
                    if (customWrap) customWrap.style.display = "none";
                }
            }

            if (farmerNameNode) farmerNameNode.textContent = report.farmer;
            if (locationNode) locationNode.textContent = report.locationText;
            if (timestampNode) timestampNode.textContent = formatTimestamp(report.timestamp);
            if (gpsNode) {
                const gpsParts = [];
                if (report.latitude !== "" && report.latitude !== null && report.longitude !== "" && report.longitude !== null) {
                    gpsParts.push(`GPS: ${report.latitude}, ${report.longitude}`);
                }
                if (report.accuracy) {
                    gpsParts.push(`Accuracy: ${report.accuracy}`);
                }
                if (report.source) {
                    gpsParts.push(`Source: ${report.source}`);
                }
                gpsNode.textContent = gpsParts.length > 0 ? gpsParts.join(" • ") : "GPS unavailable";
            }

            if (primaryImage) {
                primaryImage.src = report.primaryImage || "https://images.unsplash.com/photo-1590005354167-6da97870c913?auto=format&fit=crop&w=480&q=80";
            }

            if (notesInput) {
                notesInput.value = report.notes || "";
            }
            if (notesDisplay) {
                notesDisplay.textContent = report.notes || t("modal.notes_empty", "No notes logged.");
            }
            if (expertInput) {
                expertInput.value = "";
            }

            if (currentReportModalMode === "scan") {
                const scanPreviewGrid = document.getElementById("supporting-preview-grid");
                if (scanPreviewGrid && report.additionalImages.length === 0) {
                    renderAdditionalImages(scanPreviewGrid, []);
                }
            } else {
                renderAdditionalImages(document.getElementById("report-additional-images-grid"), report.additionalImages);
            }

            const initialCard = document.getElementById("report-initial-card");
            const safeActionsNotice = document.getElementById("report-safe-actions-notice") || document.querySelector(".safe-actions-notice-banner");
            const recoDesc = document.getElementById("report-initial-reco-desc") || document.querySelector(".initial-reco-desc-text");
            const recoHeading = document.getElementById("report-initial-reco-heading-text");

            if (currentReportModalMode === "lgu" || currentReportModalMode === "admin") {
                if (initialCard) {
                    initialCard.style.setProperty("display", "none", "important");
                }
            } else {
                if (initialCard) setDisplay(initialCard, true, "flex");
                if (assessmentAlreadyIssued) {
                    // Remove Safe Precautionary Actions notice and general safe steps description
                    if (safeActionsNotice) setDisplay(safeActionsNotice, false);
                    document.querySelectorAll(".safe-actions-notice-banner, #report-safe-actions-notice").forEach((el) => setDisplay(el, false));
                    if (recoDesc) setDisplay(recoDesc, false);
                    document.querySelectorAll(".initial-reco-desc-text, #report-initial-reco-desc").forEach((el) => setDisplay(el, false));
                    if (recoHeading) {
                        recoHeading.textContent = getVerifiedRecoTitle();
                        recoHeading.setAttribute("data-i18n", "modal.verified_reco_title");
                    }

                    // Load official complete recommendations specifically tailored to verified pest
                    const officialRecos = (Array.isArray(report.officialRecommendations) && report.officialRecommendations.length > 0)
                        ? report.officialRecommendations
                        : getOfficialRecommendationsForPest(cleanPest);
                    renderList(document.getElementById("report-initial-list"), officialRecos, t("modal.initial_reco_empty", "No recommendations available."), true, true);
                } else {
                    if (safeActionsNotice) setDisplay(safeActionsNotice, true, "flex");
                    document.querySelectorAll(".safe-actions-notice-banner, #report-safe-actions-notice").forEach((el) => setDisplay(el, true, "flex"));
                    if (recoDesc) setDisplay(recoDesc, true, "block");
                    document.querySelectorAll(".initial-reco-desc-text, #report-initial-reco-desc").forEach((el) => setDisplay(el, true, "block"));
                    if (recoHeading) {
                        recoHeading.textContent = getInitialRecoTitle();
                        recoHeading.setAttribute("data-i18n", "modal.initial_reco_title");
                    }
                    renderList(document.getElementById("report-initial-list"), report.initialRecommendations, t("modal.initial_reco_empty", "No initial recommendations available."), true, true);
                }
            }

            let expertEmptyText = t("modal.expert_assessment_empty", "No expert assessment available yet.");
            if (currentReportModalMode === "scan") {
                expertEmptyText = t("modal.expert_assessment_prompt", "Submit report for expert assessment");
            }
            renderList(document.getElementById("report-expert-list"), report.expertRecommendations, expertEmptyText, false, false);

            applyStatusStyle(report);
            applyModeState(currentReportModalMode, report);
            renderWorkflowActions(currentReportModalMode, report);
            renderVisitSummaryCard(report);
            renderResolutionDetailsCard(report);

            // Expert card visibility and input controls depend on existing assessment state
            const isAgriMode = ["agriculturist", "agri", "agri_expert"].includes(currentReportModalMode);
            if (expertCard) {
                setDisplay(expertCard, true, "block");
                const expertHelp = document.getElementById("expert-notes-help");
                const agriSubmitBtn = document.getElementById("report-agri-submit-btn");
                const issuerNote = document.getElementById("expert-assessment-issuer-note");
                const agriVerificationGroup = document.getElementById("agri-verification-group");
                const showExpertControls = isAgriMode && !assessmentAlreadyIssued;
                if (agriVerificationGroup) {
                    setDisplay(agriVerificationGroup, showExpertControls, "block");
                }
                setDisplay(expertInput, showExpertControls, "block");
                setDisplay(expertHelp, showExpertControls, "block");
                if (agriSubmitBtn) setDisplay(agriSubmitBtn, showExpertControls, "block");
                if (issuerNote) {
                    if (assessmentAlreadyIssued && (report.reviewer_name || (Array.isArray(report.expertRecommendations) && report.expertRecommendations.length > 0))) {
                        const name = report.reviewer_name || "PCA Agriculturist";
                        const pos = report.reviewer_position || "Agriculturist";
                        const off = report.reviewer_office || "";
                        let html = `Issued by ${escapeHtml(name)}<br>${escapeHtml(pos)}`;
                        if (off) html += `<br>${escapeHtml(off)}`;
                        issuerNote.innerHTML = html;
                        issuerNote.style.lineHeight = "1.4";
                        setDisplay(issuerNote, true, "block");
                    } else {
                        setDisplay(issuerNote, false);
                    }
                }
                if (showExpertControls && typeof window.setAgriValidationMode === "function") {
                    window.setAgriValidationMode("validate");
                }
            }

            // Render any farmer schedules into a dedicated display area for agriculturists
            const schedulesNode = document.getElementById("report-farmer-preferred-schedules");
            if (schedulesNode) {
                schedulesNode.innerHTML = "";
                const schedules = report.farmerSchedules || [];
                if (Array.isArray(schedules) && schedules.length) {
                    const wrapper = document.createElement('div');
                    wrapper.style.display = 'grid';
                    wrapper.style.gap = '8px';
                    const title = document.createElement('h4');
                    title.style.margin = '0';
                    title.style.fontSize = '0.98rem';
                    title.textContent = "Farmer's Preferred Schedules";
                    wrapper.appendChild(title);
                    schedules.forEach((s, idx) => {
                        const row = document.createElement('label');
                        row.style.display = 'flex';
                        row.style.alignItems = 'center';
                        row.style.gap = '8px';
                        row.style.fontSize = '0.95rem';
                        row.style.color = '#64748b';
                        row.innerHTML = `<input type="radio" name="agri-selected-schedule" value="${idx}" style="accent-color:#1d4ed8;"> ${escapeHtml(s.display)}`;
                        wrapper.appendChild(row);
                    });
                    schedulesNode.appendChild(wrapper);
                }
                // Only show this card to agriculturists when schedules exist
                setDisplay(schedulesNode, Array.isArray(schedules) && schedules.length && currentReportModalMode === 'agriculturist', 'block');
            }
        };

        try {
            renderModalFields();
        } catch (renderErr) {
            console.warn("Initial modal render encountered an error", renderErr);
        }

        // If report is missing vital metadata (or opened with partial record), dynamically fetch from API
        if (report.id && currentReportModalMode !== "scan") {
            const isPartialData = !report.farmer || report.farmer === "Farmer" || !report.pest || report.pest === "Unknown Pest" || report.confidence === "--";
            if (isPartialData) {
                try {
                    const apiRes = await fetch(`/api/reports/${encodeURIComponent(report.id)}`);
                    const apiData = await apiRes.json().catch(() => ({}));
                    if (apiRes.ok && apiData.success && apiData.report) {
                        currentReportModalRecord = normalizeReportData({
                            ...apiData.report,
                            ...reportData,
                            mode: currentReportModalMode,
                        });
                        report = currentReportModalRecord;
                        renderModalFields();
                    }
                } catch (fetchErr) {
                    console.warn("Dynamic report fetch encountered an error:", fetchErr);
                }
            }
        }

        // Fetch visit discussion messages and schedules asynchronously only if relevant
        if (report.id && currentReportModalMode !== "scan") {
            const statusKey = getStatusKey(report.status || "");
            const discussionStatuses = [
                "awaiting_confirmed_schedule",
                "visit_requested",
                "waiting_for_agriculturist_confirmation",
                "waiting_agriculturist_confirmation",
                "visit_scheduled",
                "visit_completed",
                "final_remarks_issued",
                "resolved"
            ];
            if (discussionStatuses.includes(statusKey) || report.chat_count > 0 || report.farmerFeedbackReason || report.visit_summary) {
                try {
                    await loadVisitDiscussion(report);
                    if (currentReportModalRecord?.id === report.id) {
                        renderModalFields();
                    }
                } catch (discErr) {
                    console.warn("Async visit discussion fetch failed", discErr);
                }
            }
        }

        if (shouldPollVisitDiscussion(report)) {
            startVisitDiscussionPoll(report);
        } else {
            stopVisitDiscussionPoll();
        }
    }

    window.toggleVisitDiscussion = function (event) {
        if (event) {
            if (typeof event.stopPropagation === 'function') event.stopPropagation();
            if (typeof event.preventDefault === 'function') event.preventDefault();
        }
        const report = currentReportModalRecord;
        const body = document.getElementById("visit-discussion-body");
        const toggleBtn = document.getElementById("visit-discussion-toggle");
        
        let isNowExpanded = true;
        if (body) {
            const isCurrentlyHidden = body.style.display === "none";
            isNowExpanded = isCurrentlyHidden;
            body.style.display = isNowExpanded ? "grid" : "none";
        } else if (report) {
            isNowExpanded = !Boolean(report.visitDiscussionExpanded);
        }

        if (toggleBtn) {
            toggleBtn.setAttribute("aria-expanded", isNowExpanded ? "true" : "false");
            const chevron = toggleBtn.querySelector("#visit-discussion-chevron") || toggleBtn.querySelector(".visit-discussion-chevron");
            if (chevron) {
                chevron.style.transform = `rotate(${isNowExpanded ? 90 : 0}deg)`;
            }
            const title = toggleBtn.querySelector("#visit-discussion-toggle-title");
            if (title) {
                title.style.transform = "none";
            }
        }
        if (report) {
            report.visitDiscussionExpanded = isNowExpanded;
        }
        if (!body || !toggleBtn) {
            try {
                renderVisitDiscussionCard(currentReportModalMode, report);
            } catch (renderErr) {
                console.warn("Failed to render visit discussion card on toggle:", renderErr);
            }
        } else if (isNowExpanded) {
            const messagesContainer = document.getElementById("visit-discussion-messages-container");
            if (messagesContainer) {
                requestAnimationFrame(() => {
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                });
            }
        }
    };

    window.openReportModal = openReportModal;
    window.closeReportModal = closeReportModal;
    window.openRequestRescheduleModal = openRequestRescheduleModal;
    window.openFinalizeVisitScheduleModal = openFinalizeVisitScheduleModal;
    window.resolveReportImageUrl = resolveReportImageUrl;
    window.setReportModalSubmissionState = setReportModalSubmissionState;
    window.abortReportSubmission = abortActiveReportModalSubmission;

    // Print a clean, document-style representation of the current report modal (single column)
    window.printReportModal = function () {
        try {
            const report = currentReportModalRecord || {};
            const title = (document.getElementById('report-pest-title')?.textContent || report.pest || '').trim();
            const confidence = (document.getElementById('report-confidence')?.textContent || report.confidence || '').trim();
            const imgEl = document.getElementById('report-primary-image');
            const imageSrc = imgEl?.src || report.imageSrc || report.image || '';
            const farmer = (document.getElementById('report-farmer-name')?.textContent || report.farmer || '').trim();
            const location = (document.getElementById('report-location-text')?.textContent || report.locationText || '').trim();
            const timestamp = (document.getElementById('report-timestamp-text')?.textContent || report.timestamp || '').trim();
            const notes = (document.getElementById('report-notes-display')?.textContent || report.notes || '').trim();

            // Collect recommendations text cleanly without tooltip DOM content
            let initialItems = [];
            if (Array.isArray(report.initialRecommendations) && report.initialRecommendations.length > 0) {
                initialItems = report.initialRecommendations.map(item => {
                    return typeof localizeRecommendationItem === 'function' ? localizeRecommendationItem(item) : item;
                }).filter(Boolean);
            } else {
                initialItems = Array.from(document.querySelectorAll('#report-initial-list li')).map(li => {
                    const span = li.querySelector('span');
                    return (span ? span.textContent : li.childNodes[0]?.textContent || li.textContent).trim();
                }).filter(t => t && !t.toLowerCase().includes('no initial recommendations'));
            }

            let expertItems = [];
            if (Array.isArray(report.expertRecommendations) && report.expertRecommendations.length > 0) {
                expertItems = report.expertRecommendations.map(item => String(item).trim()).filter(Boolean);
            } else {
                expertItems = Array.from(document.querySelectorAll('#report-expert-list li')).map(li => {
                    const span = li.querySelector('span');
                    return (span ? span.textContent : li.childNodes[0]?.textContent || li.textContent).trim();
                }).filter(t => t && !t.toLowerCase().includes('no expert assessment'));
            }

            const additionalImgs = Array.from(document.querySelectorAll('#report-additional-images-grid img')).map(i => i.src).filter(Boolean);

            const isHealthy = String(title || '').toLowerCase().includes('healthy') || String(title || '').toLowerCase().includes('malusog');
            const verifierName = report.reviewer_name || (document.getElementById('report-verifier-name')?.textContent || '').trim();
            const verifierPos = report.reviewer_position || 'PCA Agriculturist';
            const verifierOffice = report.reviewer_office || 'Philippine Coconut Authority';
            const isVerified = Boolean(verifierName || ['assessment_issued', 'recommendation_issued', 'resolved', 'closed'].includes(report.status));
            const statusDisplay = isVerified 
                ? (verifierName ? `Verified by Agriculturist (${verifierName})` : 'Verified by Agriculturist') 
                : 'Under Review (Pending Expert Verification)';

            const reportId = report.id || '---';
            const printTimestamp = new Date().toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            });

            const html = `<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>CocoScan Report #${escapeHtml(String(reportId))} - ${escapeHtml(title)}</title>
    <style>
        @page {
            size: A4 portrait;
            margin: 16mm 18mm;
        }
        * {
            box-sizing: border-box;
        }
        body {
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0f172a;
            background: #f1f5f9;
            margin: 0;
            padding: 32px 16px;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        .report-doc {
            max-width: 740px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 36px 42px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        }
        @media print {
            body {
                background: #ffffff;
                padding: 0;
                margin: 0;
            }
            .report-doc {
                border: none;
                box-shadow: none;
                padding: 0;
                max-width: 100%;
                border-radius: 0;
            }
            .no-print {
                display: none !important;
            }
        }
        .doc-header {
            padding-bottom: 16px;
            border-bottom: 2px solid #0f172a;
        }
        .doc-title {
            font-size: 1.5rem;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.02em;
            margin: 0;
        }
        .meta-table {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px 24px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px 20px;
            margin: 20px 0;
        }
        .meta-field {
            display: flex;
            flex-direction: column;
        }
        .meta-label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 3px;
        }
        .meta-val {
            font-size: 0.92rem;
            font-weight: 600;
            color: #0f172a;
        }
        .meta-status-tag {
            font-weight: 700;
            font-size: 0.85rem;
        }
        .meta-status-tag.verified {
            color: #166534;
        }
        .meta-status-tag.pending {
            color: #b45309;
        }
        .doc-section {
            margin-top: 22px;
            break-inside: avoid;
            page-break-inside: avoid;
        }
        .section-heading {
            font-size: 0.84rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #334155;
            margin: 0 0 10px 0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 6px;
        }
        .diagnosis-banner {
            padding: 16px 20px;
            border-radius: 8px;
            background: #f0fdf4;
            border: 1.5px solid #bbf7d0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .diagnosis-banner.pest {
            background: #fefce8;
            border-color: #fef08a;
        }
        .diagnosis-eyebrow {
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #15803d;
            margin-bottom: 3px;
        }
        .diagnosis-banner.pest .diagnosis-eyebrow {
            color: #a16207;
        }
        .diagnosis-name {
            font-size: 1.25rem;
            font-weight: 800;
            color: #14532d;
            margin: 0;
        }
        .diagnosis-banner.pest .diagnosis-name {
            color: #854d0e;
        }
        .diagnosis-confidence {
            font-size: 0.86rem;
            font-weight: 700;
            color: #166534;
            background: #ffffff;
            padding: 6px 14px;
            border-radius: 6px;
            border: 1px solid #86efac;
        }
        .diagnosis-banner.pest .diagnosis-confidence {
            color: #854d0e;
            border-color: #fde047;
        }
        .primary-image-wrap {
            width: 100%;
            margin-top: 14px;
            border-radius: 8px;
            overflow: hidden;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            text-align: center;
        }
        .primary-image-wrap img {
            width: 100%;
            max-height: 360px;
            object-fit: contain;
            display: block;
            margin: 0 auto;
            background: #f8fafc;
        }
        .image-caption {
            font-size: 0.74rem;
            color: #64748b;
            text-align: center;
            margin-top: 6px;
            font-style: italic;
        }
        .supporting-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin-top: 10px;
        }
        .supporting-item img {
            width: 100%;
            height: 100px;
            object-fit: cover;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
        }
        .notes-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 0.92rem;
            color: #334155;
            line-height: 1.55;
            white-space: pre-wrap;
        }
        .clean-reco-list {
            margin: 0;
            padding-left: 20px;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #1e293b;
        }
        .clean-reco-list li {
            margin-bottom: 6px;
        }
        .empty-note {
            font-size: 0.88rem;
            color: #64748b;
            font-style: italic;
            margin: 4px 0;
        }
        .signature-box {
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px dashed #cbd5e1;
            display: inline-block;
            min-width: 240px;
        }
        .sig-label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #64748b;
            margin-bottom: 4px;
        }
        .sig-name {
            font-weight: 800;
            color: #0f172a;
            font-size: 0.96rem;
        }
        .sig-title {
            font-size: 0.82rem;
            color: #475569;
            margin-top: 2px;
        }
        .doc-footer {
            margin-top: 36px;
            padding-top: 14px;
            border-top: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            color: #64748b;
        }
        @media (max-width: 600px) {
            .meta-table {
                grid-template-columns: 1fr;
            }
            .report-doc {
                padding: 20px 16px;
            }
        }
    </style>
</head>
<body>
    <div class="report-doc">
        <header class="doc-header">
            <h1 class="doc-title">CocoScan Diagnostic Report</h1>
        </header>

        <div class="meta-table">
            <div class="meta-field">
                <span class="meta-label">Farmer / Farm Owner</span>
                <span class="meta-val">${escapeHtml(farmer || 'Unspecified')}</span>
            </div>
            <div class="meta-field">
                <span class="meta-label">Barangay / Location</span>
                <span class="meta-val">${escapeHtml(location || 'Unspecified')}</span>
            </div>
            <div class="meta-field">
                <span class="meta-label">Date &amp; Time Scanned</span>
                <span class="meta-val">${escapeHtml(timestamp || '---')}</span>
            </div>
            <div class="meta-field">
                <span class="meta-label">Verification Status</span>
                <span class="meta-val meta-status-tag ${isVerified ? 'verified' : 'pending'}">${escapeHtml(statusDisplay)}</span>
            </div>
        </div>

        <div class="doc-section">
            <div class="diagnosis-banner ${isHealthy ? '' : 'pest'}">
                <div>
                    <div class="diagnosis-eyebrow">${isVerified ? 'Verified Classification' : 'Preliminary Detected Classification'}</div>
                    <h2 class="diagnosis-name">${escapeHtml(title || 'Unidentified Result')}</h2>
                </div>
                <div class="diagnosis-confidence">AI Confidence: ${escapeHtml(confidence || '--')}</div>
            </div>

            ${imageSrc ? `
            <div class="primary-image-wrap">
                <img src="${escapeHtml(imageSrc)}" alt="Primary leaf diagnostic scan" />
            </div>
            <div class="image-caption">Primary Field Capture &amp; Diagnostic Scan</div>` : ''}
        </div>

        ${additionalImgs.length ? `
        <div class="doc-section">
            <div class="section-heading">Supporting Field Photos (${additionalImgs.length})</div>
            <div class="supporting-grid">
                ${additionalImgs.map((src, i) => `
                    <div class="supporting-item">
                        <img src="${escapeHtml(src)}" alt="Supporting photo ${i + 1}" />
                    </div>
                `).join('')}
            </div>
        </div>` : ''}

        <div class="doc-section">
            <div class="section-heading">Farmer Field Observations</div>
            <div class="notes-box">${escapeHtml(notes) || '<em>No farmer notes recorded.</em>'}</div>
        </div>

        <div class="doc-section">
            <div class="section-heading">Initial Precautionary Recommendations</div>
            ${initialItems.length ? `
            <ol class="clean-reco-list">
                ${initialItems.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ol>` : `<p class="empty-note">No initial recommendations available.</p>`}
        </div>

        <div class="doc-section">
            <div class="section-heading">Expert Assessment &amp; Official Guidance</div>
            ${expertItems.length ? `
            <ul class="clean-reco-list" style="list-style-type: disc;">
                ${expertItems.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>` : `<p class="empty-note">No expert assessment notes recorded yet.</p>`}

            ${isVerified ? `
            <div class="signature-box">
                <div class="sig-label">Evaluated &amp; Certified By</div>
                <div class="sig-name">${escapeHtml(verifierName)}</div>
                <div class="sig-title">${escapeHtml(verifierPos)}${verifierOffice ? ` • ${escapeHtml(verifierOffice)}` : ''}</div>
            </div>` : ''}
        </div>

        <footer class="doc-footer">
            <div>Official CocoScan Diagnostic Record • Confidential Agricultural Assessment</div>
            <div>Printed on ${escapeHtml(printTimestamp)}</div>
        </footer>
    </div>
</body>
</html>`;

            // Open print window
            const w = window.open('', '_blank');
            if (!w) {
                return alert('Popup blocked — allow popups for this site to print.');
            }
            w.document.open();
            w.document.write(html);
            w.document.close();
            // wait briefly for images to load, then print
            setTimeout(() => { try { w.focus(); w.print(); } catch (e) { console.error(e); } }, 350);
        } catch (e) {
            console.error('Print error', e);
            alert('Unable to prepare print preview.');
        }
    };

    function initResizableImageContainer() {
        const container = document.getElementById("report-image-resizable-container");
        const handle = document.getElementById("report-image-resize-handle");
        if (!container || !handle) return;

        const enforceImgFill = () => {
            const img = container.querySelector("img");
            if (img) {
                img.style.setProperty("width", "100%", "important");
                img.style.setProperty("height", "100%", "important");
                img.style.setProperty("max-height", "none", "important");
                img.style.setProperty("min-height", "100%", "important");
                img.style.setProperty("aspect-ratio", "auto", "important");
                img.style.setProperty("object-fit", "cover", "important");
            }
        };

        enforceImgFill();

        if (window.ResizeObserver && !container.__roAttached) {
            container.__roAttached = true;
            try {
                const ro = new ResizeObserver(() => {
                    enforceImgFill();
                });
                ro.observe(container);
            } catch (_) {}
        }

        if (handle.__resizeAttached) return;
        handle.__resizeAttached = true;

        let isDragging = false;
        let startX = 0, startY = 0, startW = 0, startH = 0;

        const onPointerDown = (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            const rect = container.getBoundingClientRect();
            startW = rect.width;
            startH = rect.height;
            try { handle.setPointerCapture(e.pointerId); } catch (_) {}
            document.body.style.userSelect = "none";
            window.addEventListener("pointermove", onPointerMove, { passive: false });
            window.addEventListener("pointerup", onPointerUp);
            window.addEventListener("pointercancel", onPointerUp);
            if (typeof e.preventDefault === "function") e.preventDefault();
            if (typeof e.stopPropagation === "function") e.stopPropagation();
        };

        const onPointerMove = (e) => {
            if (!isDragging) return;
            const clientX = e.clientX !== undefined ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : startX);
            const clientY = e.clientY !== undefined ? e.clientY : (e.touches && e.touches[0] ? e.touches[0].clientY : startY);
            const dx = clientX - startX;
            const dy = clientY - startY;

            const parentWidth = container.parentElement ? container.parentElement.clientWidth : 360;
            const minW = 180;
            const maxW = parentWidth;
            const minH = 160;
            const maxH = 600;

            const newW = Math.min(Math.max(startW + dx, minW), maxW);
            const newH = Math.min(Math.max(startH + dy, minH), maxH);

            container.style.width = `${newW}px`;
            container.style.height = `${newH}px`;
            enforceImgFill();
        };

        const onPointerUp = (e) => {
            if (!isDragging) return;
            isDragging = false;
            document.body.style.userSelect = "";
            window.removeEventListener("pointermove", onPointerMove);
            window.removeEventListener("pointerup", onPointerUp);
            window.removeEventListener("pointercancel", onPointerUp);
            try {
                if (e && e.pointerId) handle.releasePointerCapture(e.pointerId);
            } catch (_) {}
            enforceImgFill();
        };

        handle.addEventListener("pointerdown", onPointerDown);

        // Mobile touch event support
        handle.addEventListener("touchstart", (e) => {
            if (e.touches && e.touches.length === 1) {
                const t = e.touches[0];
                onPointerDown({
                    clientX: t.clientX,
                    clientY: t.clientY,
                    pointerId: 1,
                    preventDefault: () => e.preventDefault(),
                    stopPropagation: () => e.stopPropagation()
                });
            }
        }, { passive: false });

        window.addEventListener("touchmove", (e) => {
            if (isDragging && e.touches && e.touches.length === 1) {
                const t = e.touches[0];
                onPointerMove({
                    clientX: t.clientX,
                    clientY: t.clientY
                });
                if (e.cancelable) e.preventDefault();
            }
        }, { passive: false });

        window.addEventListener("touchend", () => {
            if (isDragging) onPointerUp({});
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initResizableImageContainer);
    } else {
        initResizableImageContainer();
    }

    document.addEventListener("click", function (event) {
        const modalRoot = getModalRoot();
        if (modalRoot && modalRoot.classList.contains("open-modal") && event.target === modalRoot) {
            closeReportModal();
        }
    });

    document.addEventListener("keydown", function (event) {
        const modalRoot = getModalRoot();
        if (event.key === "Escape" && modalRoot && modalRoot.classList.contains("open-modal")) {
            closeReportModal();
        }
    });

    window.__cocoScanReportModal = {
        get currentReport() {
            return currentReportModalRecord;
        },
        get currentMode() {
            return currentReportModalMode;
        },
        closeReportModal,
    };
})();