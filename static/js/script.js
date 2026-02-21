/* =========================================================================
   ClinIQ Frontend — Claude-Inspired UI with Confidence Indicators
   ========================================================================= */

const API = '/api/v1';
let currentUser = null;
let authToken = null;
let userDepartments = [];
let allDepartments = [];
let selectedQueryDepts = new Set();
let chatHistoryStore = []; // [{id, title, ts}]

// ── DOM Refs ──
const loginPage = document.getElementById('loginPage');
const mainApp = document.getElementById('mainApp');
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const uploadList = document.getElementById('uploadList');
const questionInput = document.getElementById('questionInput');
const chatMessages = document.getElementById('chatMessages');
const chatEmpty = document.getElementById('chatEmpty');
const sendBtn = document.getElementById('sendBtn');
const notification = document.getElementById('notification');
const chatHistoryList = document.getElementById('chatHistoryList');

// =========================================================================
// AUTH
// =========================================================================

(function init() {
    const saved = localStorage.getItem('cliniq_token');
    const savedUser = localStorage.getItem('cliniq_user');
    if (saved && savedUser) {
        authToken = saved;
        currentUser = JSON.parse(savedUser);
        showApp();
    }
})();

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    loginError.classList.add('hidden');
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch(`${API}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }
        const data = await res.json();
        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('cliniq_token', authToken);
        localStorage.setItem('cliniq_user', JSON.stringify(currentUser));
        showApp();
    } catch (err) {
        loginError.textContent = err.message;
        loginError.classList.remove('hidden');
    }
});

function logout() {
    localStorage.removeItem('cliniq_token');
    localStorage.removeItem('cliniq_user');
    authToken = null;
    currentUser = null;
    mainApp.classList.add('hidden');
    loginPage.classList.remove('hidden');
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
}

function authHeaders() { return { 'Authorization': `Bearer ${authToken}` }; }
function authJsonHeaders() { return { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' }; }

async function showApp() {
    loginPage.classList.add('hidden');
    mainApp.classList.remove('hidden');

    // Nav user
    const name = currentUser.full_name || currentUser.username;
    document.getElementById('navUser').textContent = name;
    const letter = name.charAt(0).toUpperCase();
    document.getElementById('userAvatarLetter').textContent = letter;

    const roleBadge = document.getElementById('navRole');
    roleBadge.textContent = currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);
    roleBadge.className = `role-badge role-${currentUser.role}`;

    // Admin button
    const adminBtn = document.getElementById('adminToggleBtn');
    adminBtn.style.display = currentUser.role === 'admin' ? 'flex' : 'none';

    await loadDepartments();
}

// =========================================================================
// DEPARTMENTS
// =========================================================================

async function loadDepartments() {
    try {
        const res = await fetch(`${API}/departments`, { headers: authHeaders() });
        if (!res.ok) throw new Error('Failed to load departments');
        const data = await res.json();
        userDepartments = data.departments;
        allDepartments = data.all_departments;

        // Upload dropdown
        const sel = document.getElementById('uploadDept');
        sel.innerHTML = userDepartments.map(d =>
            `<option value="${d}">${d.charAt(0).toUpperCase() + d.slice(1)}</option>`
        ).join('');

        // Sidebar dept filter chips
        const filter = document.getElementById('deptFilter');
        filter.innerHTML = userDepartments.map(d =>
            `<button class="dept-chip active" data-dept="${d}" onclick="toggleDeptChip(this)">${d.charAt(0).toUpperCase() + d.slice(1)}</button>`
        ).join('');
        selectedQueryDepts = new Set(userDepartments);

        // Admin checkboxes
        const checkboxArea = document.getElementById('deptCheckboxes');
        if (checkboxArea) {
            checkboxArea.innerHTML =
                allDepartments.map(d =>
                    `<label class="cb-item"><input type="checkbox" value="${d}" checked> ${d.charAt(0).toUpperCase() + d.slice(1)}</label>`
                ).join('');
        }
    } catch (err) {
        console.error(err);
    }
}

function toggleDeptChip(btn) {
    const dept = btn.dataset.dept;
    if (selectedQueryDepts.has(dept)) {
        selectedQueryDepts.delete(dept);
        btn.classList.remove('active');
    } else {
        selectedQueryDepts.add(dept);
        btn.classList.add('active');
    }
}

// =========================================================================
// FILE UPLOAD
// =========================================================================

fileInput.addEventListener('change', handleFileSelect);

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});

function handleFileSelect(e) {
    if (e.target.files.length) {
        const file = e.target.files[0];
        previewFile(file);
        uploadFile(file);
    }
}

function previewFile(file) {
    const preview = document.getElementById('imagePreview');
    const img = document.getElementById('previewImg');
    const name = document.getElementById('previewName');
    if (file.type.startsWith('image/')) {
        img.src = URL.createObjectURL(file);
        name.textContent = file.name;
        preview.classList.remove('hidden');
    } else {
        preview.classList.add('hidden');
    }
}

async function uploadFile(file) {
    const department = document.getElementById('uploadDept').value;
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:0.78rem;">${file.name}</span>
        <span class="dept-tag">${department}</span>
        <span class="file-status">Uploading…</span>
    `;
    uploadList.prepend(item);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('department', department);

    try {
        const res = await fetch(`${API}/ingest`, {
            method: 'POST',
            headers: authHeaders(),
            body: formData,
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Upload failed');
        }
        const data = await res.json();
        const status = item.querySelector('.file-status');
        status.textContent = `✓ ${data.chunks_count} chunks`;
        status.style.color = 'var(--emerald)';
        showNotification(`✓ ${file.name} indexed to ${department}`);
    } catch (err) {
        const status = item.querySelector('.file-status');
        status.textContent = 'Error';
        status.style.color = 'var(--rose)';
        showNotification(err.message);
    }
    document.getElementById('imagePreview').classList.add('hidden');
}

// =========================================================================
// CHAT
// =========================================================================

function handleEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
    }
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

function usesuggestion(btn) {
    questionInput.value = btn.textContent;
    questionInput.focus();
    autoResize(questionInput);
}

async function sendQuery() {
    const text = questionInput.value.trim();
    if (!text) return;

    // Hide empty state
    chatEmpty.style.display = 'none';

    // User message
    appendUserMessage(text);
    questionInput.value = '';
    questionInput.style.height = 'auto';

    // Typing indicator
    const thinkingId = appendThinkingIndicator();
    sendBtn.disabled = true;

    const departments = [...selectedQueryDepts];

    try {
        const res = await fetch(`${API}/query`, {
            method: 'POST',
            headers: authJsonHeaders(),
            body: JSON.stringify({ question: text, departments }),
        });
        const data = await res.json();
        document.getElementById(thinkingId)?.remove();

        if (!res.ok) throw new Error(data.detail || 'Query failed');

        // Add to sidebar history
        addToHistory(text);

        appendAIMessage(data);

    } catch (err) {
        document.getElementById(thinkingId)?.remove();
        appendErrorMessage(err.message);
    } finally {
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

// ─── Message renderers ───────────────────────────────────────────────────

function appendUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `<div class="msg-bubble">${escapeHtml(text)}</div>`;
    chatMessages.appendChild(div);
    scrollToBottom();
}

function appendThinkingIndicator() {
    const id = 'thinking-' + Date.now();
    const div = document.createElement('div');
    div.className = 'message system';
    div.id = id;
    div.innerHTML = `
        <div class="msg-row">
            <div class="ai-avatar">AI</div>
            <div class="msg-content">
                <div class="thinking-row">
                    <div class="thinking-dots"><span></span><span></span><span></span></div>
                    Searching across departments…
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
    return id;
}

function appendAIMessage(data) {
    const {
        answer,
        sources = [],
        departments_searched = [],
        hallucination_score = 'yes',
        confidence_score = 0,
        response_type = 'answer',
        options = [],
    } = data;

    // Dept searched badges
    let deptsHtml = '';
    if (departments_searched.length > 0) {
        deptsHtml = `<div class="searched-depts">
            <span style="font-size:0.7rem;color:var(--text-muted);margin-right:0.3rem;">Searched:</span>
            ${departments_searched.map(d => `<span class="dept-chip-sm">${d}</span>`).join('')}
        </div>`;
    }

    // Decide which panel to render
    let panelHtml;
    if (response_type === 'clarification' && options.length > 0) {
        // ── Clarification mode: show clickable option cards ──
        panelHtml = buildClarificationPanel(options);
        const div = document.createElement('div');
        div.className = 'message system';
        div.innerHTML = `
            <div class="msg-row">
                <div class="ai-avatar">AI</div>
                <div class="msg-content">
                    ${deptsHtml}
                    <div class="msg-content-inner">${escapeHtml(answer)}</div>
                    ${panelHtml}
                </div>
            </div>
        `;
        chatMessages.appendChild(div);
    } else {
        // ── Normal answer: parse markdown + show confidence panel ──
        let html = marked.parse(answer);
        html = html.replace(/\[Ref (\d+)\]/g,
            '<span class="citation-ref" title="Source reference">[Ref $1]</span>');
        panelHtml = buildConfidencePanel(hallucination_score, confidence_score, sources);
        const div = document.createElement('div');
        div.className = 'message system';
        div.innerHTML = `
            <div class="msg-row">
                <div class="ai-avatar">AI</div>
                <div class="msg-content">
                    ${deptsHtml}
                    <div class="msg-content-inner">${html}</div>
                    ${panelHtml}
                </div>
            </div>
        `;
        chatMessages.appendChild(div);
    }

    scrollToBottom();
}

function appendErrorMessage(msg) {
    const div = document.createElement('div');
    div.className = 'message system';
    div.innerHTML = `
        <div class="msg-row">
            <div class="ai-avatar" style="background:var(--rose);">!</div>
            <div class="msg-content">
                <div class="msg-content-inner" style="color:var(--rose);">
                    Something went wrong: ${escapeHtml(msg)}
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
}

// ─── Clarification Panel ─────────────────────────────────────────────────

function buildClarificationPanel(options) {
    const arrowSvg = `<svg class="option-card-arrow" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>`;
    const cards = options.map(opt => `
        <button class="option-card" onclick="selectOption(this)" data-option="${escapeHtml(opt)}">
            ${arrowSvg}
            ${escapeHtml(opt)}
        </button>`).join('');

    return `
        <div class="clarification-panel">
            <p class="clarification-intro">Pick the option that best matches your question, or rephrase below:</p>
            <div class="option-cards">${cards}</div>
        </div>`;
}

function selectOption(btn) {
    const option = btn.dataset.option;
    // Highlight the selected card
    btn.closest('.option-cards').querySelectorAll('.option-card').forEach(c => {
        c.style.opacity = '0.45';
        c.disabled = true;
    });
    btn.style.opacity = '1';
    btn.style.borderColor = 'var(--primary)';
    btn.style.background = 'color-mix(in srgb, var(--primary) 10%, transparent)';

    // Fill the textarea and auto-send
    questionInput.value = option;
    autoResize(questionInput);
    setTimeout(() => sendQuery(), 180);  // slight delay so user sees the selection
}

function buildConfidencePanel(hallucinationScore, confidenceScore, sources) {
    const isGrounded = hallucinationScore === 'yes';

    // Convert 0-1 score to percentage. If score looks like a raw distance metric
    // (ChromaDB returns L2 distances where lower = better), cap at 1.
    let pct = Math.round(Math.min(confidenceScore, 1) * 100);
    // Determine confidence tier for bar color
    const tier = pct >= 70 ? 'high' : pct >= 40 ? 'medium' : 'low';

    const badgeClass = isGrounded ? 'grounded' : 'unverified';
    const badgeIcon = isGrounded
        ? `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>`
        : `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
    const badgeLabel = isGrounded ? 'Grounded' : 'Unverified';

    // Sources list
    let sourcesHtml = '';
    if (sources.length > 0) {
        const items = sources.map((src, i) => {
            const loc = src.page ? `p.${src.page}` : (src.metadata?.sheet_name ? src.metadata.sheet_name : '');
            const dept = src.metadata?.department || '';
            const score = typeof src.score === 'number' ? `${Math.round(src.score * 100)}%` : '';
            const label = [src.source, loc].filter(Boolean).join(' · ');
            return `
                <div class="source-item">
                    <span class="source-num">${i + 1}</span>
                    <span class="source-text" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
                    ${dept ? `<span class="source-dept">${dept}</span>` : ''}
                    ${score ? `<span class="source-score">${score}</span>` : ''}
                </div>`;
        }).join('');

        sourcesHtml = `
            <div class="sources-wrap">
                <button class="sources-toggle" onclick="toggleSources(this)">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                    ${sources.length} source${sources.length !== 1 ? 's' : ''}
                </button>
                <div class="sources-list" style="display:none;">${items}</div>
            </div>`;
    }

    return `
        <div class="confidence-panel">
            <div class="confidence-header">
                <span class="grounding-badge ${badgeClass}">${badgeIcon} ${badgeLabel}</span>
                <span class="confidence-label">Confidence</span>
            </div>
            <div class="confidence-bar-wrap">
                <div class="confidence-bar">
                    <div class="confidence-fill ${tier}" style="width:${pct}%"></div>
                </div>
                <span class="confidence-pct">${pct}%</span>
            </div>
            ${sourcesHtml}
        </div>`;
}

function toggleSources(btn) {
    btn.classList.toggle('open');
    const list = btn.nextElementSibling;
    list.style.display = list.style.display === 'none' ? 'flex' : 'none';
    list.style.flexDirection = 'column';
}

// =========================================================================
// SIDEBAR HISTORY
// =========================================================================

function addToHistory(question) {
    const entry = {
        id: Date.now(),
        title: question.length > 40 ? question.slice(0, 40) + '…' : question,
        ts: new Date(),
    };
    chatHistoryStore.unshift(entry);
    renderHistorySidebar();
}

function renderHistorySidebar() {
    if (chatHistoryStore.length === 0) {
        chatHistoryList.innerHTML = '';
        return;
    }

    // Group: Today vs Earlier
    const now = new Date();
    const today = chatHistoryStore.filter(e => isToday(e.ts, now));
    const older = chatHistoryStore.filter(e => !isToday(e.ts, now));

    let html = '';
    if (today.length > 0) {
        html += `<div class="history-group">
            <div class="history-group-label">Today</div>
            ${today.map(e => historyItem(e)).join('')}
        </div>`;
    }
    if (older.length > 0) {
        html += `<div class="history-group">
            <div class="history-group-label">Earlier</div>
            ${older.map(e => historyItem(e)).join('')}
        </div>`;
    }
    chatHistoryList.innerHTML = html;
}

function historyItem(e) {
    return `<div class="history-item" title="${escapeHtml(e.title)}">
        <span class="history-item-dot"></span>
        ${escapeHtml(e.title)}
    </div>`;
}

function isToday(date, now) {
    return date.getFullYear() === now.getFullYear() &&
        date.getMonth() === now.getMonth() &&
        date.getDate() === now.getDate();
}

// =========================================================================
// CLEAR CHAT
// =========================================================================

function clearChat() {
    chatMessages.innerHTML = '';
    chatEmpty.style.display = '';
}

// =========================================================================
// KB PANEL (drawer)
// =========================================================================

function toggleKbPanel() {
    document.getElementById('kbPanel').classList.toggle('open');
}

// =========================================================================
// ADMIN PANEL
// =========================================================================

function toggleAdminPanel() {
    const panel = document.getElementById('adminPanel');
    panel.classList.toggle('hidden');
    if (!panel.classList.contains('hidden')) {
        loadUsers();
        loadDeptStats();
    }
}

async function loadUsers() {
    try {
        const res = await fetch(`${API}/admin/users`, { headers: authHeaders() });
        if (!res.ok) throw new Error('Failed');
        const users = await res.json();
        const list = document.getElementById('userList');
        list.innerHTML = users.map(u => `
            <div class="user-row">
                <div>
                    <strong style="font-size:0.8rem;">${escapeHtml(u.full_name || u.username)}</strong>
                    <span class="role-badge role-${u.role}">${u.role}</span>
                </div>
                <div class="user-depts">${u.departments.join(', ')}</div>
                ${u.role !== 'admin' ? `<button class="btn-icon btn-sm-danger" onclick="deleteUser('${u.username}')">✕</button>` : ''}
            </div>`).join('');
    } catch (err) { console.error(err); }
}

async function loadDeptStats() {
    try {
        const res = await fetch(`${API}/departments/stats`, { headers: authHeaders() });
        if (!res.ok) throw new Error('Failed');
        const stats = await res.json();
        const el = document.getElementById('deptStats');
        el.innerHTML = Object.entries(stats).map(([dept, count]) => `
            <div class="stat-row">
                <span class="stat-dept">${dept.charAt(0).toUpperCase() + dept.slice(1)}</span>
                <span class="stat-count">${count} docs</span>
                <div class="stat-bar"><div class="stat-fill" style="width:${Math.min(count * 2, 100)}%"></div></div>
            </div>`).join('');
    } catch (err) { console.error(err); }
}

async function createUser() {
    const username = document.getElementById('newUsername').value.trim();
    const fullName = document.getElementById('newFullName').value.trim();
    const password = document.getElementById('newPassword').value;
    const role = document.getElementById('newRole').value;
    const checkboxes = document.querySelectorAll('#deptCheckboxes input[type=checkbox]:checked');
    const departments = [...checkboxes].map(cb => cb.value);

    if (!username || !password) { showNotification('Username and password required'); return; }

    try {
        const res = await fetch(`${API}/auth/register`, {
            method: 'POST',
            headers: authJsonHeaders(),
            body: JSON.stringify({ username, password, full_name: fullName, role, departments }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed');
        }
        showNotification(`✓ User '${username}' created`);
        document.getElementById('newUsername').value = '';
        document.getElementById('newFullName').value = '';
        document.getElementById('newPassword').value = '';
        loadUsers();
    } catch (err) { showNotification(err.message); }
}

async function deleteUser(username) {
    if (!confirm(`Delete user '${username}'?`)) return;
    try {
        const res = await fetch(`${API}/admin/users/${username}`, {
            method: 'DELETE', headers: authHeaders(),
        });
        if (!res.ok) throw new Error('Failed');
        showNotification(`User '${username}' deleted`);
        loadUsers();
    } catch (err) { showNotification(err.message); }
}

// =========================================================================
// UTILS
// =========================================================================

function scrollToBottom() {
    const area = document.getElementById('chatArea');
    area.scrollTop = area.scrollHeight;
}

function showNotification(msg) {
    notification.textContent = msg;
    notification.classList.remove('hidden');
    setTimeout(() => notification.classList.add('hidden'), 3500);
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
