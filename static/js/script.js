/* =========================================================================
   ClinIQ Frontend — Auth, Department-Scoped Upload & Query, Admin Panel
   ========================================================================= */

const API = '/api/v1';
let currentUser = null;
let authToken = null;
let userDepartments = [];
let allDepartments = [];
let selectedQueryDepts = new Set();

// ── DOM Refs ──
const loginModal = document.getElementById('loginModal');
const mainApp = document.getElementById('mainApp');
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const uploadList = document.getElementById('uploadList');
const questionInput = document.getElementById('questionInput');
const chatHistory = document.getElementById('chatHistory');
const sendBtn = document.getElementById('sendBtn');
const notification = document.getElementById('notification');

// =========================================================================
// AUTH
// =========================================================================

// Check for existing token on load
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
    loginModal.classList.remove('hidden');
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
}

function authHeaders() {
    return {
        'Authorization': `Bearer ${authToken}`,
    };
}

function authJsonHeaders() {
    return {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
    };
}

async function showApp() {
    loginModal.classList.add('hidden');
    mainApp.classList.remove('hidden');

    // Update nav
    document.getElementById('navUser').textContent = currentUser.full_name || currentUser.username;
    const roleBadge = document.getElementById('navRole');
    roleBadge.textContent = currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);
    roleBadge.className = `role-badge role-${currentUser.role}`;

    // Show/hide admin button
    const adminBtn = document.getElementById('adminToggleBtn');
    adminBtn.style.display = currentUser.role === 'admin' ? '' : 'none';

    // Load departments
    await loadDepartments();
}

async function loadDepartments() {
    try {
        const res = await fetch(`${API}/departments`, { headers: authHeaders() });
        if (!res.ok) throw new Error('Failed to load departments');
        const data = await res.json();
        userDepartments = data.departments;
        allDepartments = data.all_departments;

        // Populate upload dropdown
        const sel = document.getElementById('uploadDept');
        sel.innerHTML = userDepartments.map(d =>
            `<option value="${d}">${d.charAt(0).toUpperCase() + d.slice(1)}</option>`
        ).join('');

        // Populate query filter chips
        const filter = document.getElementById('deptFilter');
        filter.innerHTML = '<span class="filter-label">Search in:</span>' +
            userDepartments.map(d =>
                `<button class="dept-chip active" data-dept="${d}" onclick="toggleDeptChip(this)">${d.charAt(0).toUpperCase() + d.slice(1)}</button>`
            ).join('');

        // All selected by default
        selectedQueryDepts = new Set(userDepartments);

        // Populate admin create-user dept checkboxes
        const checkboxArea = document.getElementById('deptCheckboxes');
        if (checkboxArea) {
            checkboxArea.innerHTML = '<label class="cb-label">Departments:</label>' +
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

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
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
        const url = URL.createObjectURL(file);
        img.src = url;
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
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <span>${file.name}</span>
        <span class="dept-tag">${department}</span>
        <span class="file-status">Uploading...</span>
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
        status.textContent = `✓ ${data.chunks_count} chunks (${data.modality})`;
        status.style.color = '#34d399';
        showNotification(`✓ ${file.name} indexed to ${department}`);
    } catch (err) {
        const status = item.querySelector('.file-status');
        status.textContent = 'Error';
        status.style.color = '#f87171';
        showNotification(err.message);
    }

    // Reset preview
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

async function sendQuery() {
    const text = questionInput.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    questionInput.value = '';

    const loadingId = addMessage('Thinking...', 'system', true);
    sendBtn.disabled = true;

    const departments = [...selectedQueryDepts];

    try {
        const res = await fetch(`${API}/query`, {
            method: 'POST',
            headers: authJsonHeaders(),
            body: JSON.stringify({ question: text, departments }),
        });

        const data = await res.json();
        document.getElementById(loadingId).remove();

        if (!res.ok) throw new Error(data.detail || 'Query failed');

        let formattedAnswer = marked.parse(data.answer);
        formattedAnswer = formattedAnswer.replace(/\[Ref (\d+)\]/g,
            '<span class="citation-ref" title="Source available below">[Ref $1]</span>');

        // Departments searched badge
        if (data.departments_searched && data.departments_searched.length > 0) {
            formattedAnswer = `<div class="searched-depts">Searched: ${data.departments_searched.map(d =>
                `<span class="dept-chip-sm">${d}</span>`).join('')}</div>` + formattedAnswer;
        }

        // Append sources
        if (data.sources && data.sources.length > 0) {
            formattedAnswer += '<hr style="border:0; border-top:1px solid rgba(255,255,255,0.1); margin: 1em 0;">';
            formattedAnswer += '<small style="color:var(--text-secondary)"><strong>Sources:</strong><br>';
            data.sources.forEach((src, idx) => {
                const loc = src.page ? `Page ${src.page}` : (src.metadata.sheet_name ? `Sheet: ${src.metadata.sheet_name}` : '');
                const dept = src.metadata.department ? ` [${src.metadata.department}]` : '';
                formattedAnswer += `[Ref ${idx + 1}] ${src.source}${dept} ${loc}<br>`;
            });
            formattedAnswer += '</small>';
        }

        addMessage(formattedAnswer, 'system', false, true);

    } catch (err) {
        document.getElementById(loadingId)?.remove();
        addMessage('Sorry, something went wrong: ' + err.message, 'system');
        console.error(err);
    } finally {
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

function addMessage(text, sender, isLoading = false, isHtml = false) {
    const id = 'msg-' + Date.now();
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.id = id;

    const avatar = sender === 'user' ? (currentUser?.full_name?.[0] || 'U') : 'AI';
    let contentHtml = isHtml ? text : text.replace(/\n/g, '<br>');
    if (isLoading) contentHtml = '<span class="pulse">Searching across departments...</span>';

    div.innerHTML = `
        <div class="avatar">${avatar}</div>
        <div class="content">${contentHtml}</div>
    `;

    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return id;
}

function clearChat() {
    chatHistory.innerHTML = `
        <div class="message system">
            <div class="avatar">AI</div>
            <div class="content">
                Chat cleared. Ready for new questions. Your departments: ${[...selectedQueryDepts].join(', ')}.
            </div>
        </div>
    `;
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
                    <strong>${u.full_name || u.username}</strong>
                    <span class="role-badge role-${u.role}">${u.role}</span>
                </div>
                <div class="user-depts">${u.departments.join(', ')}</div>
                ${u.role !== 'admin' ? `<button class="btn-ghost btn-sm-danger" onclick="deleteUser('${u.username}')">✕</button>` : ''}
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
    }
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
                <div class="stat-bar"><div class="stat-fill" style="width: ${Math.min(count * 2, 100)}%"></div></div>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
    }
}

async function createUser() {
    const username = document.getElementById('newUsername').value.trim();
    const fullName = document.getElementById('newFullName').value.trim();
    const password = document.getElementById('newPassword').value;
    const role = document.getElementById('newRole').value;

    const checkboxes = document.querySelectorAll('#deptCheckboxes input[type=checkbox]:checked');
    const departments = [...checkboxes].map(cb => cb.value);

    if (!username || !password) {
        showNotification('Username and password required');
        return;
    }

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
    } catch (err) {
        showNotification(err.message);
    }
}

async function deleteUser(username) {
    if (!confirm(`Delete user '${username}'?`)) return;
    try {
        const res = await fetch(`${API}/admin/users/${username}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!res.ok) throw new Error('Failed');
        showNotification(`User '${username}' deleted`);
        loadUsers();
    } catch (err) {
        showNotification(err.message);
    }
}

// =========================================================================
// UTILS
// =========================================================================

function showNotification(msg) {
    notification.textContent = msg;
    notification.classList.remove('hidden');
    setTimeout(() => notification.classList.add('hidden'), 3500);
}
