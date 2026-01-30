const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const uploadList = document.getElementById('uploadList');
const questionInput = document.getElementById('questionInput');
const chatHistory = document.getElementById('chatHistory');
const sendBtn = document.getElementById('sendBtn');
const notification = document.getElementById('notification');

/* --- File Upload Handling --- */

fileInput.addEventListener('change', handleFileSelect);
dropZone.addEventListener('click', () => fileInput.click()); // Allow clicking container

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length) uploadFile(files[0]);
});

function handleFileSelect(e) {
    if (e.target.files.length) uploadFile(e.target.files[0]);
}

async function uploadFile(file) {
    // Show UI item
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <span>${file.name}</span>
        <span class="file-status">Uploading...</span>
    `;
    uploadList.prepend(item);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/v1/ingest', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Upload failed');

        const data = await res.json();
        item.querySelector('.file-status').textContent = `Indexed (${data.chunks_count} chunks)`;
        item.querySelector('.file-status').style.color = '#34d399'; // Success green
        showNotification(`Success: ${file.name} ingested.`);
    } catch (err) {
        item.querySelector('.file-status').textContent = 'Error';
        item.querySelector('.file-status').style.color = '#f87171'; // Error red
        showNotification(err.message);
    }
}

/* --- Chat Handling --- */

function handleEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
    }
}

async function sendQuery() {
    const text = questionInput.value.trim();
    if (!text) return;

    // Add User Message
    addMessage(text, 'user');
    questionInput.value = '';

    // Loading State
    const loadingId = addMessage('Thinking...', 'system', true);
    sendBtn.disabled = true;

    try {
        const res = await fetch('/api/v1/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text })
        });

        const data = await res.json();

        // Remove loading
        document.getElementById(loadingId).remove();

        // Format answer with markdown and highlight references
        // We replace [Ref X] with a styled span
        let formattedAnswer = marked.parse(data.answer);
        formattedAnswer = formattedAnswer.replace(/\[Ref (\d+)\]/g, '<span class="citation-ref" title="Source available below">[Ref $1]</span>');

        // Append Sources
        if (data.sources && data.sources.length > 0) {
            formattedAnswer += '<hr style="border:0; border-top:1px solid rgba(255,255,255,0.1); margin: 1em 0;">';
            formattedAnswer += '<small style="color:var(--text-secondary)"><strong>Sources:</strong><br>';
            data.sources.forEach((src, idx) => {
                const loc = src.page ? `Page ${src.page}` : (src.metadata.sheet_name ? `Sheet: ${src.metadata.sheet_name}` : 'Unknown');
                formattedAnswer += `[Ref ${idx + 1}] ${src.source} (${loc})<br>`;
            });
            formattedAnswer += '</small>';
        }

        addMessage(formattedAnswer, 'system', false, true);

    } catch (err) {
        document.getElementById(loadingId).remove();
        addMessage('Sorry, something went wrong. Please try again.', 'system');
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

    const avatar = sender === 'user' ? 'U' : 'AI';

    let contentHtml = isHtml ? text : text.replace(/\n/g, '<br>');
    if (isLoading) contentHtml = '<span class="pulse">...</span>';

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
                Chat cleared. Ready for new questions.
            </div>
        </div>
    `;
}

function showNotification(msg) {
    notification.textContent = msg;
    notification.classList.remove('hidden');
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}
