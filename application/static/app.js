let channelId = localStorage.getItem("chakravyuh_channel_id") || null;
let currentTicket = null;
let currentVoucher = null;
let cachedManifestData = null;

const consoleOutput = document.getElementById("console-output");

function logConsole(title, data) {
    const timestamp = new Date().toISOString().substring(11, 19);
    const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
    consoleOutput.textContent += `[${timestamp}] ${title}\n${text}\n\n`;
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

async function apiCall(endpoint, method = "GET", body = null) {
    const options = {
        method,
        headers: { "Content-Type": "application/json" }
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    const res = await fetch(endpoint, options);
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.detail?.message || data.detail || `HTTP Error ${res.status}`);
    }
    return data;
}

async function fetchManifest() {
    try {
        const data = await apiCall("/api/instructions/manifest");
        cachedManifestData = data;
        document.getElementById("manifest-viewer").textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        logConsole("ERR: Failed to load manifest", err.message);
    }
}

async function openNewChannel() {
    try {
        const res = await apiCall("/api/channel/open", "POST", { participant_urn: "urn:vyuha:participant:browser-node" });
        channelId = res.channel_id;
        localStorage.setItem("chakravyuh_channel_id", channelId);
        logConsole("CHANNEL INITIALIZED", res);
        await updateStatus();
    } catch (err) {
        logConsole("ERR: Failed to open channel", err.message);
    }
}

async function updateStatus() {
    if (!channelId) return;

    try {
        const status = await apiCall(`/api/channel/status?channel_id=${channelId}`);
        document.getElementById("channel-id-display").textContent = status.channel_id;
        document.getElementById("cycle-display").textContent = status.current_cycle;
        document.getElementById("balance-display").textContent = `${status.channel_balance.toFixed(2)} SDR`;
        document.getElementById("reserve-text").textContent = status.reserve_balance.toFixed(2);

        // Update reserve progress gauge
        const pct = Math.max(0, Math.min(100, (status.reserve_balance / 1000.0) * 100));
        const bar = document.getElementById("reserve-bar");
        bar.style.width = `${pct}%`;

        const reserveStatusText = document.getElementById("reserve-status-text");
        if (status.reserve_balance < status.statutory_floor) {
            reserveStatusText.textContent = "Adequacy Margin: CRITICAL DEFICIT";
            reserveStatusText.className = "text-amber-500 font-semibold animate-pulse";
            bar.className = "bg-gradient-to-r from-red-600 to-amber-600 h-full rounded-full transition-all duration-500";
        } else {
            reserveStatusText.textContent = "Adequacy Margin: ADEQUATE";
            reserveStatusText.className = "text-emerald-400 font-medium";
            bar.className = "bg-gradient-to-r from-amber-600 to-amber-400 h-full rounded-full transition-all duration-500";
        }

        // Update stage badge
        const badge = document.getElementById("stage-badge");
        badge.textContent = status.pipeline_stage;
        badge.className = `badge badge-${status.pipeline_stage === 'IDLE' ? 'idle' : 'active'}`;

        // Update button states
        currentTicket = status.active_ticket;
        currentVoucher = status.active_voucher;

        document.getElementById("ticket-preview").textContent = currentTicket ? `Ticket: ${currentTicket}` : "Ticket: None";
        document.getElementById("voucher-preview").textContent = currentVoucher ? `Voucher: ${currentVoucher}` : "Voucher: None";

        const btnIntake = document.getElementById("btn-action-intake");
        const btnEarmark = document.getElementById("btn-action-earmark");
        const btnDisburse = document.getElementById("btn-action-disburse");
        const btnFinalize = document.getElementById("btn-action-finalize");

        btnIntake.disabled = status.pipeline_stage !== "IDLE";
        btnEarmark.disabled = status.pipeline_stage !== "INTAKE_VALIDATED";
        btnDisburse.disabled = status.pipeline_stage !== "RESERVE_EARMARKED";
        btnFinalize.disabled = status.pipeline_stage !== "DISBURSED";

        // Highlight ring cards
        const rings = ["ring-1-card", "ring-2-card", "ring-3-card", "ring-4-card"];
        rings.forEach(id => document.getElementById(id).className = "ring-card");

        if (status.pipeline_stage === "IDLE") {
            document.getElementById("ring-1-card").classList.add("ring-active");
        } else if (status.pipeline_stage === "INTAKE_VALIDATED") {
            document.getElementById("ring-1-card").classList.add("ring-done");
            document.getElementById("ring-2-card").classList.add("ring-active");
        } else if (status.pipeline_stage === "RESERVE_EARMARKED") {
            document.getElementById("ring-1-card").classList.add("ring-done");
            document.getElementById("ring-2-card").classList.add("ring-done");
            document.getElementById("ring-3-card").classList.add("ring-active");
        } else if (status.pipeline_stage === "DISBURSED") {
            document.getElementById("ring-1-card").classList.add("ring-done");
            document.getElementById("ring-2-card").classList.add("ring-done");
            document.getElementById("ring-3-card").classList.add("ring-done");
            document.getElementById("ring-4-card").classList.add("ring-active");
        }

        await refreshLedger();
        await refreshReceipts();
    } catch (err) {
        logConsole("ERR: Failed to update status", err.message);
    }
}

async function runIntake() {
    if (!cachedManifestData) await fetchManifest();
    try {
        const payload = {
            channel_id: channelId,
            manifest: cachedManifestData.manifest,
            authority_key: cachedManifestData.authority_key,
            signature: cachedManifestData.signature
        };
        const res = await apiCall("/api/pipeline/intake", "POST", payload);
        logConsole("RING I: INTAKE ACCEPTED", res);
        await updateStatus();
    } catch (err) {
        logConsole("ERR: Intake submission failed", err.message);
    }
}

async function runEarmark() {
    try {
        const res = await apiCall("/api/pipeline/earmark", "POST", {
            channel_id: channelId,
            ticket: currentTicket
        });
        logConsole("RING II: COLLATERAL EARMARKED", res);
        await updateStatus();
    } catch (err) {
        logConsole("ERR: Earmark failed", err.message);
    }
}

async function runDisburse() {
    try {
        const res = await apiCall("/api/pipeline/disburse", "POST", {
            channel_id: channelId,
            voucher: currentVoucher
        });
        logConsole("RING III: DISBURSEMENT COMMITTED", res);
        await updateStatus();
    } catch (err) {
        logConsole("ERR: Disbursement failed", err.message);
    }
}

async function runFinalize() {
    try {
        const res = await apiCall("/api/receipts/finalize", "POST", {
            channel_id: channelId
        });
        logConsole("RING IV: BATCH FINALIZED", res);
        await updateStatus();
    } catch (err) {
        logConsole("ERR: Finalization failed", err.message);
    }
}

async function runReconcile() {
    try {
        const res = await apiCall("/api/channel/reconcile", "POST", {
            channel_id: channelId
        });
        logConsole("SUPERVISORY RECONCILIATION RESULT", res);
        
        // Show modal with supervisory assessment
        const modal = document.getElementById("modal-container");
        const body = document.getElementById("modal-body");
        body.innerHTML = `
            <div class="p-3 bg-slate-950 border border-slate-800 rounded">
                <div>Status: <strong class="${res.status === 'RECONCILIATION_COMPLIANT' ? 'text-emerald-400' : 'text-amber-400'}">${res.status}</strong></div>
                <div>Reserve Ratio: <strong>${res.reserve_ratio}</strong> (Statutory Floor: ${res.statutory_floor})</div>
                <div>Assessment: <strong>${res.status_assessment}</strong></div>
            </div>
            ${res.contingency_resolution ? `
            <div class="p-3 bg-amber-950/40 border border-amber-600/50 rounded space-y-1">
                <div class="text-amber-300 font-bold uppercase text-[11px]">Contingency Resolution Record:</div>
                <div class="break-all">Record URN: <span class="text-slate-300">${res.contingency_resolution.record_urn}</span></div>
                <div class="break-all">Directive: <span class="text-slate-300">${res.contingency_resolution.regulatory_directive}</span></div>
                <div class="break-all mt-2 p-2 bg-slate-950 border border-amber-500/40 rounded">
                    <span class="text-amber-400 font-bold">Attestation Anchor:</span>
                    <div class="text-amber-200 select-all font-mono font-bold mt-1 text-xs">${res.contingency_resolution.attestation_anchor}</div>
                </div>
            </div>` : ''}
        `;
        modal.classList.remove("hidden");
        await updateStatus();
    } catch (err) {
        logConsole("ERR: Reconciliation query failed", err.message);
    }
}

async function refreshLedger() {
    if (!channelId) return;
    try {
        const entries = await apiCall(`/api/ledger/journal?channel_id=${channelId}`);
        const tbody = document.getElementById("ledger-table-body");
        if (entries.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-500">No journal postings recorded</td></tr>`;
            return;
        }
        tbody.innerHTML = entries.map(e => `
            <tr class="hover:bg-slate-900/60">
                <td class="p-3 font-semibold text-amber-300">${e.journal_id}</td>
                <td class="p-3">${e.cycle_number}</td>
                <td class="p-3 text-slate-400">${e.voucher_ref}</td>
                <td class="p-3 text-emerald-400 font-bold">+${e.units.toFixed(2)} SDR</td>
                <td class="p-3 text-slate-500">${new Date(e.posted_at * 1000).toLocaleTimeString()}</td>
                <td class="p-3 text-slate-500 font-mono text-[10px]">${e.entry_hash.substring(0, 16)}...</td>
            </tr>
        `).join("");
    } catch (err) {}
}

async function refreshReceipts() {
    if (!channelId) return;
    try {
        const certs = await apiCall(`/api/receipts/list?channel_id=${channelId}`);
        const tbody = document.getElementById("receipts-table-body");
        if (certs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-500">No batch certificates sealed</td></tr>`;
            return;
        }
        tbody.innerHTML = certs.map(c => `
            <tr class="hover:bg-slate-900/60">
                <td class="p-3 font-semibold text-slate-200">${c.certificate_id}</td>
                <td class="p-3">${c.cycle_number}</td>
                <td class="p-3 text-amber-300 font-bold">${c.total_cleared.toFixed(2)} SDR</td>
                <td class="p-3 text-slate-500">${new Date(c.issued_at * 1000).toLocaleTimeString()}</td>
                <td class="p-3 text-slate-500 font-mono text-[10px]">${c.integrity_hash.substring(0, 16)}...</td>
            </tr>
        `).join("");
    } catch (err) {}
}

async function loadDirectory() {
    try {
        const members = await apiCall("/api/directory/list");
        const grid = document.getElementById("directory-grid");
        grid.innerHTML = members.map(m => `
            <div class="p-4 bg-slate-950/60 border border-slate-800 rounded-lg space-y-1">
                <div class="flex justify-between items-center">
                    <span class="font-mono text-xs font-bold text-amber-300">${m.code}</span>
                    <span class="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded">${m.status}</span>
                </div>
                <div class="text-xs text-slate-200 font-semibold">${m.institution_name}</div>
                <div class="text-[11px] text-slate-400 font-mono">${m.routing_urn}</div>
                <div class="text-[11px] text-slate-500 pt-1 border-t border-slate-800 flex justify-between">
                    <span>${m.tier}</span>
                    <span>${m.settlement_currency}</span>
                </div>
            </div>
        `).join("");
    } catch (err) {}
}

// Event Listeners
document.getElementById("btn-open-channel").addEventListener("click", openNewChannel);
document.getElementById("btn-refresh").addEventListener("click", updateStatus);
document.getElementById("btn-action-intake").addEventListener("click", runIntake);
document.getElementById("btn-action-earmark").addEventListener("click", runEarmark);
document.getElementById("btn-action-disburse").addEventListener("click", runDisburse);
document.getElementById("btn-action-finalize").addEventListener("click", runFinalize);
document.getElementById("btn-reconcile").addEventListener("click", runReconcile);
document.getElementById("btn-clear-log").addEventListener("click", () => consoleOutput.textContent = "");
document.getElementById("modal-close").addEventListener("click", () => document.getElementById("modal-container").classList.add("hidden"));
document.getElementById("modal-ok").addEventListener("click", () => document.getElementById("modal-container").classList.add("hidden"));

document.getElementById("btn-copy-manifest").addEventListener("click", () => {
    if (cachedManifestData) {
        navigator.clipboard.writeText(JSON.stringify(cachedManifestData, null, 2));
        logConsole("INFO", "Raw manifest copied to clipboard");
    }
});

// Tab Switcher
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => {
            b.classList.remove("active", "text-amber-400", "border-b-2", "border-amber-400");
            b.classList.add("text-slate-400");
        });
        btn.classList.add("active", "text-amber-400", "border-b-2", "border-amber-400");
        btn.classList.remove("text-slate-400");

        document.querySelectorAll(".tab-content").forEach(tc => tc.classList.add("hidden"));
        const tabId = btn.getAttribute("data-tab");
        document.getElementById(tabId).classList.remove("hidden");
    });
});

// Initialization
window.addEventListener("DOMContentLoaded", async () => {
    await fetchManifest();
    await loadDirectory();
    if (channelId) {
        await updateStatus();
    } else {
        await openNewChannel();
    }
});
