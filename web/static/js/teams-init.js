/**
 * Teams JS SDK initialization for IECC Portal.
 * Handles: context detection, Share to Stage, and embedded URL propagation.
 */
(async function teamsInit() {
    if (typeof microsoftTeams === 'undefined') return;

    try {
        await microsoftTeams.app.initialize();
    } catch (e) {
        console.warn('Teams SDK init failed (not in Teams?):', e);
        // Hide Teams-specific UI when not in Teams iframe
        var toolbar = document.getElementById('teams-toolbar');
        if (toolbar) toolbar.style.display = 'none';
        return;
    }

    var context;
    try {
        context = await microsoftTeams.app.getContext();
    } catch (e) {
        console.warn('Could not get Teams context:', e);
        return;
    }

    var frameContext = context.page ? context.page.frameContext : '';
    console.log('Teams frame context:', frameContext);

    // --- Side Panel: show Share to Stage button ---
    if (frameContext === 'sidePanel') {
        var shareBtn = document.getElementById('teams-share-btn');
        var stopBtn = document.getElementById('teams-stop-btn');

        // Check if user has permission to share to stage
        try {
            microsoftTeams.meeting.getAppContentStageSharingCapabilities(
                function(err, result) {
                    if (result && result.doesAppHaveSharePermission && shareBtn) {
                        shareBtn.style.display = 'inline-block';
                    }
                }
            );
        } catch (e) {
            console.warn('Could not check sharing capabilities:', e);
        }

        // Check if already sharing
        try {
            microsoftTeams.meeting.getAppContentStageSharingState(
                function(err, result) {
                    if (result && result.isAppSharing) {
                        if (shareBtn) shareBtn.style.display = 'none';
                        if (stopBtn) stopBtn.style.display = 'inline-block';
                    }
                }
            );
        } catch (e) { /* ignore */ }
    }

    // --- Meeting Stage: initialize as stage view ---
    if (frameContext === 'meetingStage') {
        // Hide share/stop buttons on stage (only relevant in side panel)
        var shareBtn = document.getElementById('teams-share-btn');
        var stopBtn = document.getElementById('teams-stop-btn');
        if (shareBtn) shareBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'none';
        // Update toolbar text
        var toolbarText = document.querySelector('.teams-toolbar-text');
        if (toolbarText) toolbarText.textContent += ' (Stage View)';
    }

    // Propagate ?embedded=teams to all links and forms on the page
    teamsEmbedLinks();

    // Re-propagate after HTMX swaps (dynamic content)
    document.body.addEventListener('htmx:afterSwap', function() {
        teamsEmbedLinks();
    });
})();


/**
 * Share current meeting's Go Live view to the Teams meeting stage.
 */
function teamsShareToStage() {
    // Find the meeting ID from the current page URL
    var match = window.location.pathname.match(/\/meeting\/(\d+)\//);
    if (!match) {
        console.error('Could not determine meeting ID from URL');
        return;
    }
    var meetingId = match[1];
    var stageUrl = window.location.origin + '/meeting/' + meetingId + '/go-live?embedded=teams';

    microsoftTeams.meeting.shareAppContentToStage(
        function(err, result) {
            if (result) {
                console.log('Shared to stage:', stageUrl);
                var shareBtn = document.getElementById('teams-share-btn');
                var stopBtn = document.getElementById('teams-stop-btn');
                if (shareBtn) shareBtn.style.display = 'none';
                if (stopBtn) stopBtn.style.display = 'inline-block';
            }
            if (err) {
                console.error('Share to stage failed:', JSON.stringify(err));
                alert('Could not share to stage. You may need presenter permissions.');
            }
        },
        stageUrl
    );
}


/**
 * Stop sharing app content to stage.
 */
function teamsStopSharing() {
    microsoftTeams.meeting.stopSharingAppContentToStage(
        function(err, result) {
            if (result) {
                var shareBtn = document.getElementById('teams-share-btn');
                var stopBtn = document.getElementById('teams-stop-btn');
                if (shareBtn) shareBtn.style.display = 'inline-block';
                if (stopBtn) stopBtn.style.display = 'none';
            }
        }
    );
}


/**
 * Append ?embedded=teams (or &embedded=teams) to all links and form actions
 * on the page so navigation within the iframe stays in Teams mode.
 */
function teamsEmbedLinks() {
    // Links
    document.querySelectorAll('a[href]').forEach(function(a) {
        var href = a.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('http')) return;
        if (href.indexOf('embedded=teams') === -1) {
            a.setAttribute('href', href + (href.indexOf('?') >= 0 ? '&' : '?') + 'embedded=teams');
        }
    });

    // Forms
    document.querySelectorAll('form[action]').forEach(function(form) {
        var action = form.getAttribute('action');
        if (!action || action.startsWith('http')) return;
        if (action.indexOf('embedded=teams') === -1) {
            form.setAttribute('action', action + (action.indexOf('?') >= 0 ? '&' : '?') + 'embedded=teams');
        }
    });

    // HTMX hx-post / hx-get attributes
    document.querySelectorAll('[hx-post], [hx-get]').forEach(function(el) {
        ['hx-post', 'hx-get'].forEach(function(attr) {
            var url = el.getAttribute(attr);
            if (url && url.indexOf('embedded=teams') === -1) {
                el.setAttribute(attr, url + (url.indexOf('?') >= 0 ? '&' : '?') + 'embedded=teams');
            }
        });
    });
}
