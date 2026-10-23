let currentToken = localStorage.getItem("solver_token") || null;
let currentAccountId = null;

document.addEventListener("DOMContentLoaded", () => {
    if (currentToken) {
        verifySession();
    } else {
        showAuth();
    }
});

function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
    };
}

async function verifySession() {
    try {
        const res = await fetch("/api/account/profile", { headers: getHeaders() });
        if (res.ok) {
            const data = await res.json();
            currentAccountId = data.account_id;
            showConsole(data);
        } else {
            resetSession();
        }
    } catch (e) {
        console.error("Verification failed", e);
        resetSession();
    }
}

async function registerSolver() {
    const name = document.getElementById("solverNameInput").value || "AlphaSolver";
    try {
        const res = await fetch("/api/account/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ solver_name: name })
        });
        if (res.ok) {
            const data = await res.json();
            currentToken = data.token;
            localStorage.setItem("solver_token", currentToken);
            currentAccountId = data.account_id;
            verifySession();
        } else {
            alert("Failed to initialize solver account.");
        }
    } catch (e) {
        alert("Registration network error.");
    }
}

function resumeSession() {
    const token = document.getElementById("resumeTokenInput").value.trim();
    if (!token) return;
    currentToken = token;
    localStorage.setItem("solver_token", currentToken);
    verifySession();
}

function resetSession() {
    currentToken = null;
    currentAccountId = null;
    localStorage.removeItem("solver_token");
    showAuth();
}

function showAuth() {
    document.getElementById("authSection").style.display = "block";
    document.getElementById("mainConsole").style.display = "none";
    document.getElementById("topMetrics").style.display = "none";
}

function showConsole(profile) {
    document.getElementById("authSection").style.display = "none";
    document.getElementById("mainConsole").style.display = "block";
    document.getElementById("topMetrics").style.display = "flex";
    updateProfileUI(profile);
    loadOrders();
}

function updateProfileUI(p) {
    document.getElementById("dispAccountId").innerText = p.account_id;
    document.getElementById("dispBalance").innerText = `${p.balance.toFixed(2)} CR`;
    document.getElementById("dispReserve").innerText = `${p.reserve_balance.toFixed(2)} CR`;
    document.getElementById("auditReserve").innerText = `${p.reserve_balance.toFixed(2)} CR`;

    const statusBadge = document.getElementById("dispSolvencyStatus");
    const auditStatus = document.getElementById("auditStatus");

    if (p.reserve_balance < p.solvency_floor) {
        statusBadge.className = "badge badge-danger";
        statusBadge.innerText = "CRITICAL DEFICIT";
        auditStatus.className = "badge badge-danger";
        auditStatus.innerText = "CRITICAL DEFICIT";
    } else {
        statusBadge.className = "badge badge-success";
        statusBadge.innerText = "COMPLIANT";
        auditStatus.className = "badge badge-success";
        auditStatus.innerText = "COMPLIANT";
    }
}

async function refreshTelemetry() {
    if (!currentToken) return;
    try {
        const res = await fetch("/api/account/profile", { headers: getHeaders() });
        if (res.ok) {
            const data = await res.json();
            updateProfileUI(data);
        }
    } catch (e) {
        console.error(e);
    }
}

function switchTab(tab) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

    const activeBtn = Array.from(document.querySelectorAll(".tab-btn")).find(b => b.innerText.toLowerCase().includes(tab));
    if (activeBtn) activeBtn.classList.add("active");

    const targetPane = document.getElementById(`tab-${tab}`);
    if (targetPane) targetPane.classList.add("active");

    if (tab === "orders") loadOrders();
    if (tab === "quotes") loadQuotes();
    if (tab === "settlements") loadSettlements();
    if (tab === "receipts") loadReceipts();
    if (tab === "ledger") loadLedger();
    if (tab === "reconciliation") loadReconciliation();
}

async function loadOrders() {
    const res = await fetch("/api/orders", { headers: getHeaders() });
    if (!res.ok) return;
    const orders = await res.json();
    const tbody = document.getElementById("ordersTableBody");
    tbody.innerHTML = "";

    orders.forEach(o => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="mono">${o.order_id}</td>
            <td><strong>${o.pair}</strong></td>
            <td class="mono">${o.nominal_size.toFixed(2)}</td>
            <td class="mono">${o.base_rate.toFixed(4)}</td>
            <td class="mono">${o.target_fee_bps} bps</td>
            <td><span class="badge ${o.status === 'OPEN' ? 'badge-success' : 'badge-warning'}">${o.status}</span></td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="openQuoteModal('${o.order_id}', ${o.base_rate}, ${o.target_fee_bps})">
                    Submit Quote
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function openQuoteModal(orderId, rate, spread) {
    document.getElementById("modalOrderId").value = orderId;
    document.getElementById("modalTitle").innerText = `Submit Quote for ${orderId}`;
    document.getElementById("modalRate").value = rate;
    document.getElementById("modalSpread").value = spread;
    document.getElementById("modalAlloc").value = "100.0";
    document.getElementById("quoteModal").classList.add("active");
}

async function submitQuote() {
    const order_id = document.getElementById("modalOrderId").value;
    const rate = parseFloat(document.getElementById("modalRate").value);
    const spread_bps = parseInt(document.getElementById("modalSpread").value);
    const allocation_pct = parseFloat(document.getElementById("modalAlloc").value);

    try {
        const res = await fetch("/api/quotes", {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ order_id, rate, spread_bps, allocation_pct })
        });
        const data = await res.json();
        if (res.ok) {
            closeModal("quoteModal");
            switchTab("quotes");
        } else {
            alert(data.detail || "Failed to create quote.");
        }
    } catch (e) {
        alert("Submission failed.");
    }
}

async function loadQuotes() {
    const res = await fetch("/api/quotes", { headers: getHeaders() });
    if (!res.ok) return;
    const quotes = await res.json();
    const tbody = document.getElementById("quotesTableBody");
    tbody.innerHTML = "";

    quotes.forEach(q => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="mono">${q.quote_id}</td>
            <td class="mono">${q.order_id}</td>
            <td class="mono">Rev #${q.current_revision}</td>
            <td class="mono highlight">${q.quote_ref || '—'}</td>
            <td class="mono">${q.rate.toFixed(4)}</td>
            <td class="mono">${q.spread_bps} bps</td>
            <td class="mono">${q.payout_amount.toFixed(2)} CR</td>
            <td><span class="badge ${q.state === 'ACTIVE' ? 'badge-success' : 'badge-warning'}">${q.state}</span></td>
            <td>
                <div style="display: flex; gap: 6px;">
                    <button class="btn btn-primary btn-sm" onclick="executeSettlement('${q.quote_ref}')">Settle</button>
                    <button class="btn btn-secondary btn-sm" onclick="openAdjustModal('${q.quote_id}')">Adjust</button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function openAdjustModal(quoteId) {
    document.getElementById("adjustQuoteId").value = quoteId;
    document.getElementById("adjustModal").classList.add("active");
}

async function submitAdjustment() {
    const quoteId = document.getElementById("adjustQuoteId").value;
    const rateDelta = parseFloat(document.getElementById("adjustRateDelta").value) || 0.0;
    const spreadDelta = parseInt(document.getElementById("adjustSpreadDelta").value) || 0;
    const alloc = parseFloat(document.getElementById("adjustAlloc").value) || 100.0;

    try {
        const res = await fetch(`/api/quotes/${quoteId}/adjust`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ rate_delta: rateDelta, spread_delta: spreadDelta, allocation_pct: alloc })
        });
        const data = await res.json();
        if (res.ok) {
            closeModal("adjustModal");
            loadQuotes();
        } else {
            alert(data.detail || "Adjustment failed.");
        }
    } catch (e) {
        alert("Adjustment network error.");
    }
}

async function executeSettlement(quoteRef) {
    if (!quoteRef) return;
    try {
        const res = await fetch("/api/settlements", {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ quote_ref: quoteRef })
        });
        const data = await res.json();
        if (res.ok) {
            refreshTelemetry();
            switchTab("settlements");
        } else {
            alert(data.detail || "Settlement failed.");
        }
    } catch (e) {
        alert("Settlement error.");
    }
}

async function loadSettlements() {
    const res = await fetch("/api/settlements", { headers: getHeaders() });
    if (!res.ok) return;
    const settlements = await res.json();
    const tbody = document.getElementById("settlementsTableBody");
    tbody.innerHTML = "";

    settlements.forEach(s => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="mono">${s.settlement_id}</td>
            <td class="mono">${s.order_id}</td>
            <td class="mono highlight">${s.quote_ref}</td>
            <td class="mono" style="font-size:0.75rem; color:var(--text-muted);">${s.settlement_identity.substring(0, 16)}...</td>
            <td class="mono">${s.amount.toFixed(2)} CR</td>
            <td><span class="badge badge-success">${s.state}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="sealReceipt('${s.settlement_id}')">
                    Seal Receipt
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function sealReceipt(settlementId) {
    try {
        const res = await fetch("/api/receipts", {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ settlement_id: settlementId })
        });
        const data = await res.json();
        if (res.ok) {
            refreshTelemetry();
            switchTab("receipts");
        } else {
            alert(data.detail || "Receipt issuance failed.");
        }
    } catch (e) {
        alert("Receipt request error.");
    }
}

async function loadReceipts() {
    const res = await fetch("/api/receipts", { headers: getHeaders() });
    if (!res.ok) return;
    const receipts = await res.json();
    const tbody = document.getElementById("receiptsTableBody");
    tbody.innerHTML = "";

    receipts.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="mono">${r.receipt_id}</td>
            <td class="mono">${r.quote_id}</td>
            <td class="mono">${r.order_id}</td>
            <td class="mono" style="font-size:0.75rem; color:var(--text-muted);">${r.receipt_identity.substring(0, 16)}...</td>
            <td class="mono">${r.amount.toFixed(2)} CR</td>
            <td><span class="badge badge-success">${r.status}</span></td>
            <td style="font-size:0.78rem; color:var(--text-muted);">${r.issued_at.replace("T", " ").substring(0, 19)}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadLedger() {
    const res = await fetch("/api/ledger", { headers: getHeaders() });
    if (!res.ok) return;
    const entries = await res.json();
    const tbody = document.getElementById("ledgerTableBody");
    tbody.innerHTML = "";

    entries.forEach(e => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="mono">${e.entry_id}</td>
            <td class="mono">${e.settlement_id}</td>
            <td class="mono">${e.quote_ref}</td>
            <td class="mono" style="color:var(--accent-red);">${e.debit_account}</td>
            <td class="mono" style="color:var(--accent-green);">${e.credit_account}</td>
            <td class="mono">${e.amount.toFixed(2)} CR</td>
            <td class="mono">${e.reserve_after.toFixed(2)} CR</td>
            <td style="font-size:0.78rem; color:var(--text-muted);">${e.created_at.replace("T", " ").substring(0, 19)}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadReconciliation() {
    const res = await fetch("/api/reconciliation/status", { headers: getHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("auditReserve").innerText = `${data.current_reserve.toFixed(2)} CR`;
    document.getElementById("auditDisbursed").innerText = `${data.total_disbursed.toFixed(2)} CR`;

    const statusBadge = document.getElementById("auditStatus");
    if (data.solvency_status === "CRITICAL_DEFICIT") {
        statusBadge.className = "badge badge-danger";
        statusBadge.innerText = "CRITICAL DEFICIT";
    } else {
        statusBadge.className = "badge badge-success";
        statusBadge.innerText = "COMPLIANT";
    }
}

async function triggerAudit() {
    try {
        const res = await fetch("/api/reconciliation/audit", {
            method: "POST",
            headers: getHeaders()
        });
        const data = await res.json();
        const output = document.getElementById("certificateOutput");
        output.innerText = JSON.stringify(data.certificate, null, 2);
        refreshTelemetry();
        loadReconciliation();
    } catch (e) {
        alert("Reconciliation audit error.");
    }
}

function closeModal(id) {
    document.getElementById(id).classList.remove("active");
}
