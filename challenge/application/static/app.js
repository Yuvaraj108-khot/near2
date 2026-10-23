let channelId = localStorage.getItem("chakravyuh_channel_id") || null;
let currentTicket = null;
let currentVoucher = null;
let cachedManifestData = null;
let eventCounter = 0;

const consoleOutput = document.getElementById("console-output");

// Toast Notification
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✓" : type === "error" ? "⚠" : "ℹ";
    toast.innerHTML = `<span class="font-bold text-sm">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function logConsole(title, data) {
    eventCounter++;
    const timestamp = new Date().toISOString().substring(11, 19);
    const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
    consoleOutput.textContent += `[${timestamp}] ${title}\n${text}\n\n`;
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
    document.getElementById("log-count").textContent = `${eventCounter} events`;
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
        showToast(`Initialized Channel: ${channelId.substring(0, 14)}...`, "success");
        logConsole("CHANNEL INITIALIZED", res);
        await updateStatus();
    } catch (err) {
        showToast(err.message, "error");
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
        document.getElementById("ratio-percentage").textContent = `${Math.round(pct)}%`;

        const reserveStatusText = document.getElementById("reserve-status-text");
        const dot = document.getElementById("reserve-indicator-dot");

        if (status.reserve_balance < status.statutory_floor) {
            reserveStatusText.textContent = "Adequacy: CRITICAL DEFICIT";
            reserveStatusText.className = "font-bold text-amber-400 animate-pulse";
            dot.className = "w-2.5 h-2.5 rounded-full bg-red-500 animate-ping";
            bar.className = "bg-gradient-to-r from-red-600 via-amber-600 to-amber-500 h-full rounded-full transition-all duration-700 shadow-sm shadow-red-500/50";
        } else {
            reserveStatusText.textContent = "Adequacy: ADEQUATE";
            reserveStatusText.className = "font-medium text-emerald-400";
            dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
            bar.className = "bg-gradient-to-r from-amber-600 via-amber-500 to-amber-400 h-full rounded-full transition-all duration-700 shadow-sm shadow-amber-500/50";
        }

        // Update stage badge
        const badge = document.getElementById("stage-badge");
        badge.textContent = status.pipeline_stage;
        badge.className = `px-2.5 py-1 rounded-full text-[11px] font-bold font-mono tracking-wider ${
            status.pipeline_stage === 'IDLE' 
                ? 'bg-slate-800 text-slate-300 border border-slate-700' 
                : 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse'
        }`;

        // Update button states & previews
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

        // Style the active button with gold gradient
        btnIntake.className = btnIntake.disabled ? "btn-dark py-1.5 px-4 rounded-lg text-xs font-semibold" : "btn-gold py-1.5 px-4 rounded-lg text-xs";
        btnEarmark.className = btnEarmark.disabled ? "btn-dark py-1.5 px-4 rounded-lg text-xs font-semibold" : "btn-gold py-1.5 px-4 rounded-lg text-xs";
        btnDisburse.className = btnDisburse.disabled ? "btn-dark py-1.5 px-4 rounded-lg text-xs font-semibold" : "btn-gold py-1.5 px-4 rounded-lg text-xs";
        btnFinalize.className = btnFinalize.disabled ? "btn-dark py-1.5 px-4 rounded-lg text-xs font-semibold" : "btn-gold py-1.5 px-4 rounded-lg text-xs";

        // Update Step Cards & Radar Visualizer
        const stepCards = ["step-ring-1", "step-ring-2", "step-ring-3", "step-ring-4"];
        stepCards.forEach(id => document.getElementById(id).className = "step-card p-4");

        const radarRings = ["radar-ring-1", "radar-ring-2", "radar-ring-3", "radar-ring-4"];
        radarRings.forEach(id => {
            const el = document.getElementById(id);
            el.className.baseVal = "radar-ring";
            el.setAttribute("stroke", "#475569");
        });

        const radarLabel = document.getElementById("radar-status-label");

        if (status.pipeline_stage === "IDLE") {
            document.getElementById("step-ring-1").classList.add("active");
            document.getElementById("radar-ring-1").classList.add("active");
            document.getElementById("radar-ring-1").setAttribute("stroke", "#f59e0b");
            radarLabel.textContent = "Ring I Standby";
        } else if (status.pipeline_stage === "INTAKE_VALIDATED") {
            document.getElementById("step-ring-1").classList.add("completed");
            document.getElementById("step-ring-2").classList.add("active");
            document.getElementById("radar-ring-1").classList.add("completed");
            document.getElementById("radar-ring-2").classList.add("active");
            document.getElementById("radar-ring-2").setAttribute("stroke", "#f59e0b");
            radarLabel.textContent = "Ring II Earmark Active";
        } else if (status.pipeline_stage === "RESERVE_EARMARKED") {
            document.getElementById("step-ring-1").classList.add("completed");
            document.getElementById("step-ring-2").classList.add("completed");
            document.getElementById("step-ring-3").classList.add("active");
            document.getElementById("radar-ring-1").classList.add("completed");
            document.getElementById("radar-ring-2").classList.add("completed");
            document.getElementById("radar-ring-3").classList.add("active");
            document.getElementById("radar-ring-3").setAttribute("stroke", "#f59e0b");
            radarLabel.textContent = "Ring III Ledger Disburse";
        } else if (status.pipeline_stage === "DISBURSED") {
            document.getElementById("step-ring-1").classList.add("completed");
            document.getElementById("step-ring-2").classList.add("completed");
            document.getElementById("step-ring-3").classList.add("completed");
            document.getElementById("step-ring-4").classList.add("active");
            document.getElementById("radar-ring-1").classList.add("completed");
            document.getElementById("radar-ring-2").classList.add("completed");
            document.getElementById("radar-ring-3").classList.add("completed");
            document.getElementById("radar-ring-4").classList.add("active");
            document.getElementById("radar-ring-4").setAttribute("stroke", "#f59e0b");
            radarLabel.textContent = "Ring IV Finality Pending";
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
        showToast("Ring I: Manifest Intake Validated", "success");
        logConsole("RING I: INTAKE ACCEPTED", res);
        await updateStatus();
    } catch (err) {
        showToast(err.message, "error");
        logConsole("ERR: Intake submission failed", err.message);
    }
}

async function runEarmark() {
    try {
        const res = await apiCall("/api/pipeline/earmark", "POST", {
            channel_id: channelId,
            ticket: currentTicket
        });
        showToast("Ring II: Collateral Earmarked", "success");
        logConsole("RING II: COLLATERAL EARMARKED", res);
        await updateStatus();
    } catch (err) {
        showToast(err.message, "error");
        logConsole("ERR: Earmark failed", err.message);
    }
}

async function runDisburse() {
    try {
        const res = await apiCall("/api/pipeline/disburse", "POST", {
            channel_id: channelId,
            voucher: currentVoucher
        });
        showToast(`Ring III: Disbursed +${res.units_disbursed} SDR`, "success");
        logConsole("RING III: DISBURSEMENT COMMITTED", res);
        await updateStatus();
    } catch (err) {
        showToast(err.message, "error");
        logConsole("ERR: Disbursement failed", err.message);
    }
}

async function runFinalize() {
    try {
        const res = await apiCall("/api/receipts/finalize", "POST", {
            channel_id: channelId
        });
        showToast(`Ring IV: Batch Sealed (Cycle ${res.completed_cycle} Complete)`, "success");
        logConsole("RING IV: BATCH FINALIZED", res);
        await updateStatus();
    } catch (err) {
        showToast(err.message, "error");
        logConsole("ERR: Finalization failed", err.message);
    }
}

// Auto-run 1 full settlement cycle with visual pacing
async function runAutoCycle() {
    const btn = document.getElementById("btn-auto-cycle");
    btn.disabled = true;
    btn.textContent = "⏳ Executing Cycle...";

    try {
        showToast("Beginning 4-Ring Clearing Sequence...", "info");
        await runIntake();
        await new Promise(r => setTimeout(r, 600));
        await runEarmark();
        await new Promise(r => setTimeout(r, 600));
        await runDisburse();
        await new Promise(r => setTimeout(r, 600));
        await runFinalize();
        showToast("Settlement Cycle Completed Successfully!", "success");
    } catch (err) {
        showToast("Cycle sequence halted: " + err.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = "<span>▶</span> Auto-Run Cycle";
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
        
        const isDeficit = res.status === 'RECONCILIATION_DEFICIT_TRIGGERED';
        
        body.innerHTML = `
            <div class="p-3.5 bg-slate-950/80 border ${isDeficit ? 'border-amber-500/40' : 'border-slate-800'} rounded-xl space-y-2">
                <div class="flex justify-between items-center">
                    <span class="text-slate-400">Compliance Status:</span>
                    <strong class="${isDeficit ? 'text-amber-400 animate-pulse' : 'text-emerald-400'}">${res.status}</strong>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-slate-400">Reserve Ratio:</span>
                    <strong class="text-slate-200">${res.reserve_ratio} (Floor: ${res.statutory_floor})</strong>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-slate-400">Supervisory Assessment:</span>
                    <strong class="${isDeficit ? 'text-amber-300' : 'text-emerald-400'}">${res.status_assessment}</strong>
                </div>
            </div>
            ${res.contingency_resolution ? `
            <div class="p-4 bg-gradient-to-br from-amber-950/60 to-slate-900 border border-amber-500/50 rounded-xl space-y-2.5">
                <div class="flex items-center space-x-2 text-amber-300 font-bold uppercase text-[11px] tracking-wider">
                    <span>⚠</span> <span>Regulatory Contingency Resolution Record</span>
                </div>
                <div class="text-[11px] text-slate-300 space-y-1">
                    <div>Record URN: <span class="font-mono text-slate-200">${res.contingency_resolution.record_urn}</span></div>
                    <div>Directive: <span class="font-mono text-amber-200/90">${res.contingency_resolution.regulatory_directive}</span></div>
                </div>
                <div class="mt-2 p-3 bg-slate-950 border border-amber-500/50 rounded-lg space-y-1.5">
                    <div class="flex justify-between items-center">
                        <span class="text-amber-400 font-bold text-[11px] uppercase tracking-wider">Attestation Anchor:</span>
                        <button id="btn-copy-seal" class="text-[10px] bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 px-2 py-0.5 rounded font-mono">Copy Anchor</button>
                    </div>
                    <div id="seal-text" class="text-amber-200 select-all font-mono font-bold text-xs break-all">${res.contingency_resolution.attestation_anchor}</div>
                </div>
            </div>` : ''}
        `;

        modal.classList.remove("hidden");

        const copyBtn = document.getElementById("btn-copy-seal");
        if (copyBtn) {
            copyBtn.addEventListener("click", () => {
                const seal = document.getElementById("seal-text").textContent;
                navigator.clipboard.writeText(seal);
                showToast("Attestation Anchor copied to clipboard!", "success");
            });
        }

        await updateStatus();
    } catch (err) {
        showToast(err.message, "error");
        logConsole("ERR: Reconciliation query failed", err.message);
    }
}

async function refreshLedger() {
    if (!channelId) return;
    try {
        const entries = await apiCall(`/api/ledger/journal?channel_id=${channelId}`);
        const tbody = document.getElementById("ledger-table-body");
        if (entries.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="p-6 text-center text-slate-500">No journal postings recorded in active channel</td></tr>`;
            return;
        }
        tbody.innerHTML = entries.map(e => `
            <tr class="hover:bg-slate-900/60 transition-colors">
                <td class="p-3.5 font-semibold text-amber-300">${e.journal_id}</td>
                <td class="p-3.5">${e.cycle_number}</td>
                <td class="p-3.5 text-slate-400 text-[11px]">${e.voucher_ref}</td>
                <td class="p-3.5 text-emerald-400 font-bold">+${e.units.toFixed(2)} SDR</td>
                <td class="p-3.5 text-slate-500">${new Date(e.posted_at * 1000).toLocaleTimeString()}</td>
                <td class="p-3.5 text-slate-500 text-[10px]">${e.entry_hash.substring(0, 16)}...</td>
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
            tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-500">No batch certificates sealed yet</td></tr>`;
            return;
        }
        tbody.innerHTML = certs.map(c => `
            <tr class="hover:bg-slate-900/60 transition-colors">
                <td class="p-3.5 font-semibold text-slate-200">${c.certificate_id}</td>
                <td class="p-3.5">${c.cycle_number}</td>
                <td class="p-3.5 text-amber-300 font-bold">${c.total_cleared.toFixed(2)} SDR</td>
                <td class="p-3.5 text-slate-500">${new Date(c.issued_at * 1000).toLocaleTimeString()}</td>
                <td class="p-3.5 text-slate-500 text-[10px]">${c.integrity_hash.substring(0, 16)}...</td>
            </tr>
        `).join("");
    } catch (err) {}
}

async function loadDirectory() {
    try {
        const members = await apiCall("/api/directory/list");
        const grid = document.getElementById("directory-grid");
        grid.innerHTML = members.map(m => `
            <div class="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2 hover:border-slate-700 transition-all">
                <div class="flex justify-between items-center">
                    <span class="font-mono text-xs font-bold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">${m.code}</span>
                    <span class="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full font-mono">${m.status}</span>
                </div>
                <div class="text-xs text-slate-200 font-semibold">${m.institution_name}</div>
                <div class="text-[11px] text-slate-400 font-mono">${m.routing_urn}</div>
                <div class="text-[11px] text-slate-500 pt-2 border-t border-slate-800/80 flex justify-between">
                    <span>${m.tier}</span>
                    <span class="font-mono text-slate-400">${m.settlement_currency}</span>
                </div>
            </div>
        `).join("");
    } catch (err) {}
}

// Event Listeners
document.getElementById("btn-open-channel").addEventListener("click", openNewChannel);
document.getElementById("btn-refresh").addEventListener("click", () => {
    updateStatus();
    showToast("Telemetry Refreshed", "info");
});
document.getElementById("btn-action-intake").addEventListener("click", runIntake);
document.getElementById("btn-action-earmark").addEventListener("click", runEarmark);
document.getElementById("btn-action-disburse").addEventListener("click", runDisburse);
document.getElementById("btn-action-finalize").addEventListener("click", runFinalize);
document.getElementById("btn-auto-cycle").addEventListener("click", runAutoCycle);
document.getElementById("btn-reconcile").addEventListener("click", runReconcile);
document.getElementById("btn-clear-log").addEventListener("click", () => {
    consoleOutput.textContent = "";
    eventCounter = 0;
    document.getElementById("log-count").textContent = "0 events";
});
document.getElementById("modal-close").addEventListener("click", () => document.getElementById("modal-container").classList.add("hidden"));
document.getElementById("modal-ok").addEventListener("click", () => document.getElementById("modal-container").classList.add("hidden"));

document.getElementById("btn-copy-manifest").addEventListener("click", () => {
    if (cachedManifestData) {
        navigator.clipboard.writeText(JSON.stringify(cachedManifestData, null, 2));
        showToast("Raw sovereign manifest copied to clipboard", "success");
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
