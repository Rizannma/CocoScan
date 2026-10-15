(() => {
    if (window.CocoScanRefresh) return;

    const pendingWrites = new Set();
    const originalFetch = window.fetch.bind(window);
    const safeMethods = new Set(['GET', 'HEAD', 'OPTIONS']);
    const confirmationMessage = 'You have an action currently stashed or processing. Are you sure you want to refresh and discard pending changes?';
    let refreshInProgress = false;

    window.fetch = function (input, init) {
        const requestMethod = input instanceof Request ? input.method : 'GET';
        const method = String(init?.method || requestMethod).toUpperCase();
        const request = originalFetch(input, init);
        if (safeMethods.has(method)) return request;

        let trackedRequest;
        trackedRequest = Promise.resolve(request).finally(() => pendingWrites.delete(trackedRequest));
        pendingWrites.add(trackedRequest);
        return trackedRequest;
    };

    function isVisible(element) {
        if (!element || element.hidden) return false;
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && style.visibility !== 'hidden' && element.getClientRects().length > 0;
    }

    const pendingQueues = () => [
        window.pendingExecutionQueue,
        window.pendingExecutions,
        window.stashedActions,
        window.__cocoScanPendingActions
    ];

    function queueEntries(queue) {
        if (Array.isArray(queue)) return queue;
        if (queue instanceof Set) return Array.from(queue);
        if (queue instanceof Map) return Array.from(queue.values());
        if (queue && typeof queue === 'object') return Object.values(queue);
        return Number.isFinite(queue) && queue > 0 ? [queue] : [];
    }

    function hasPendingQueue() {
        return pendingQueues().some(queue => queueEntries(queue).length > 0);
    }

    function getPendingTimer() {
        if (window.pendingExecutionTimeout !== undefined) return window.pendingExecutionTimeout;
        try {
            return typeof pendingExecutionTimeout === 'undefined' ? null : pendingExecutionTimeout;
        } catch (_error) {
            return null;
        }
    }

    function hasPendingTimer() {
        const timer = getPendingTimer();
        return timer !== undefined && timer !== null;
    }

    function hasOpenConfirmation() {
        return Array.from(document.querySelectorAll(
            '.modal-overlay-container.active, [role="dialog"][aria-modal="true"], .confirmation-modal.active'
        )).some(isVisible);
    }

    function hasVisibleUndoToast() {
        return Array.from(document.querySelectorAll(
            '.undo-toast-wrapper.visible, .undo-toast.active, [data-undo-pending="true"]'
        )).some(isVisible);
    }

    function hasActiveBackgroundWork() {
        return pendingWrites.size > 0 || Boolean(window.__cocoScanActiveProcess) ||
            Boolean(document.querySelector('[data-processing="true"], [data-submitting="true"], .btn-loading'));
    }

    function hasPendingWork() {
        return hasActiveBackgroundWork() || hasPendingQueue() || hasPendingTimer() ||
            hasOpenConfirmation() || hasVisibleUndoToast();
    }

    async function flushPendingQueue() {
        const flushHook = window.flushPendingExecutionQueue || window.flushPendingActions || window.commitStashedActions;
        if (typeof flushHook === 'function') {
            await flushHook();
        } else {
            const queues = Array.from(new Set(pendingQueues().filter(Boolean)));
            for (const queue of queues) {
                for (const operation of queueEntries(queue)) {
                const commit = typeof operation === 'function'
                    ? operation
                    : operation?.commit || operation?.execute;
                if (typeof commit !== 'function') {
                    throw new Error('A queued action cannot be safely committed. Finish it before refreshing.');
                }
                await commit.call(operation);
                }
            }
        }

        for (const queue of new Set(pendingQueues().filter(Boolean))) {
            if (Array.isArray(queue)) queue.length = 0;
            else if (queue instanceof Set || queue instanceof Map) queue.clear();
            else if (typeof queue === 'object') {
                Object.keys(queue).forEach(key => delete queue[key]);
            }
        }
    }

    async function waitForBackgroundWork() {
        const deadline = Date.now() + 15000;
        while (hasActiveBackgroundWork()) {
            if (Date.now() >= deadline) {
                throw new Error('A background save is still running. Wait for it to finish before refreshing.');
            }
            await new Promise(resolve => window.setTimeout(resolve, 100));
        }
    }

    function closeTransientUi() {
        document.querySelectorAll('.modal-overlay-container.active, .confirmation-modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
        document.querySelectorAll('.undo-toast-wrapper.visible, .undo-toast.active, [data-undo-pending="true"]').forEach(toast => {
            toast.classList.remove('visible', 'active');
            toast.setAttribute('aria-hidden', 'true');
        });
    }

    async function refreshPage(button) {
        if (refreshInProgress) return;
        if (hasPendingWork() && !window.confirm(confirmationMessage)) return;

        refreshInProgress = true;
        if (button) button.disabled = true;
        try {
            await flushPendingQueue();
            if (hasPendingTimer()) {
                window.clearTimeout(getPendingTimer());
                if ('pendingExecutionTimeout' in window) window.pendingExecutionTimeout = null;
                try {
                    if (typeof pendingExecutionTimeout !== 'undefined') pendingExecutionTimeout = null;
                } catch (_error) {}
            }
            const commitUndo = window.commitPendingUndo;
            if (typeof commitUndo === 'function') await commitUndo();
            await waitForBackgroundWork();
            closeTransientUi();

            const icon = button?.querySelector('i');
            if (icon) {
                icon.classList.add('fa-spin');
                await new Promise(resolve => window.setTimeout(resolve, 450));
            }
            const url = new URL(window.location.href);
            url.searchParams.set('_r', Date.now());
            window.location.replace(url.toString());
        } catch (error) {
            refreshInProgress = false;
            if (button) button.disabled = false;
            window.alert(error.message || 'Unable to safely refresh while an action is pending.');
        }
    }

    window.CocoScanRefresh = { pendingWrites, refresh: refreshPage };
    window.spinAndRefresh = refreshPage;
})();
