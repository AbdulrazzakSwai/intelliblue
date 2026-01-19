document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const roleLabel = document.getElementById('current-role-label');
    const views = {
        analyst: document.getElementById('view-analyst'),
        admin: document.getElementById('view-admin')
    };
    const navItems = document.querySelectorAll('.nav-links li');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const attachBtn = document.getElementById('attach-btn');
    const fileInput = document.getElementById('file-upload');
    const uploadedFilesList = document.getElementById('uploaded-files-list');
    
    const modalBackdrop = document.getElementById('modal-backdrop');
    const closeModalBtn = document.querySelector('.close-modal');
    const cancelDownloadBtn = document.getElementById('cancel-download');
    const confirmDownloadBtn = document.getElementById('confirm-download');
    const logoutBtn = document.getElementById('logout-btn');
    themeToggle.addEventListener('click', () => {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', newTheme);
        themeToggle.innerHTML = newTheme === 'light' ? '<span class="icon">🌓</span>' : '<span class="icon">☀️</span>';
    });
    const TROJAN_SCENARIO_RESPONSE = `
    <strong>CRITICAL THREAT DETECTED</strong><br><br>
    I have analyzed the uploaded log file and correlated it with threat intelligence feeds. <br>
    <strong>Incident Type:</strong> Trojan.Win32.Emotet<br>
    <strong>Severity:</strong> <span style="color:var(--danger)">High</span><br><br>
    
    <strong>Key Findings:</strong>
    <ul>
        <li>Host <strong>FINANCE-PC-04</strong> initiated abnormal outbound connections.</li>
        <li>Destination IP: <span class="code-block">45.33.2.1</span> (Known C2 Server).</li>
        <li>Process: <span class="code-block">svcshost.exe</span> (Masquerading as svchost.exe).</li>
    </ul><br>
    
    <strong>Recommended Actions:</strong>
    <ol>
        <li>Isolate FINANCE-PC-04 from the network immediately.</li>
        <li>Block IP 45.33.2.1 at the perimeter firewall.</li>
        <li>Terminate process ID 3421.</li>
        <li>Run full endpoint scan for persistence mechanisms.</li>
    </ol>
    <br>
    <button class="btn-confirm dynamic-report-btn" style="margin-top:10px;">Generate Incident Report</button>
    `;

    const DEFAULT_GREETING = "I am IntelliBlue, how can I help you?";
    setTimeout(() => {
        addBotMessage(DEFAULT_GREETING, true);
    }, 500);

    function addUserMessage(text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message user';
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    function addBotMessage(htmlContent, animate = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot';
        chatMessages.appendChild(msgDiv); 
        scrollToBottom();

        if (animate) {
            msgDiv.classList.add('typing-content');
            
            if (htmlContent.includes('<')) {
                 msgDiv.classList.add('report-message');

                msgDiv.innerHTML = '<span class="icon">⏳</span> Analyzing...';
                
                setTimeout(() => {
                    msgDiv.innerHTML = '';
                    typeHtmlMessage(msgDiv, htmlContent);
                }, 1500);
            } else {
                let i = 0;
                msgDiv.textContent = '';
                const typeInterval = setInterval(() => {
                    msgDiv.textContent += htmlContent.charAt(i);
                    i++;
                    scrollToBottom();
                    if (i >= htmlContent.length) {
                        clearInterval(typeInterval);
                        msgDiv.classList.remove('typing-content');
                    }
                }, 30);
            }
        } else {
            msgDiv.innerHTML = htmlContent;
        }
    }

    function typeHtmlMessage(element, html) {
        element.innerHTML = html;
        
        const queue = [];
        function traverse(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                if (node.nodeValue.trim().length > 0) {
                     queue.push({ type: 'text', node: node, content: node.nodeValue });
                     node.nodeValue = '';
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                queue.push({ type: 'element_start', node: node });
                node.style.display = 'none';
                
                Array.from(node.childNodes).forEach(child => traverse(child));
            }
        }
        
        Array.from(element.childNodes).forEach(child => traverse(child));
        
        let index = 0;
        function processQueue() {
            if (index >= queue.length) {
                element.classList.remove('typing-content');
                return;
            }
            
            const item = queue[index];
            
            if (item.type === 'element_start') {
                item.node.style.display = '';
                index++;
                setTimeout(processQueue, 15);
            } else if (item.type === 'text') {
                let charIndex = 0;
                const text = item.content;
                
                function typeChar() {
                    if (charIndex < text.length) {
                        item.node.nodeValue += text.charAt(charIndex);
                        charIndex++;
                        scrollToBottom();
                        setTimeout(typeChar, 10); 
                    } else {
                        index++;
                        processQueue();
                    }
                }
                typeChar();
            }
        }
        
        processQueue();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function handleInput() {
        const text = chatInput.value.trim();
        if (!text) return;

        addUserMessage(text);
        chatInput.value = '';
        setTimeout(() => {
            addBotMessage(TROJAN_SCENARIO_RESPONSE, true);
        }, 500);
    }

    sendBtn.addEventListener('click', handleInput);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleInput();
    });
    attachBtn.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length > 0) {
            const fileName = fileInput.files[0].name;
            addUserMessage(`Uploaded file: ${fileName}`);
            updateUploadedFilesList(fileName);
            fileInput.value = '';
            setTimeout(() => {
                addBotMessage(TROJAN_SCENARIO_RESPONSE, true);
            }, 500);
        }
    });

    function updateUploadedFilesList(fileName) {
        const placeholder = uploadedFilesList.querySelector('li .alert-meta');
        if (placeholder && placeholder.textContent.includes('No files uploaded')) {
            uploadedFilesList.innerHTML = '';
        }

        const li = document.createElement('li');
        li.className = 'alert-item';
        const timeOffset = "Just now"; 

        li.innerHTML = `
             <div class="alert-marker" style="background-color: var(--info);"></div>
             <div class="alert-content">
                <span class="alert-title">${fileName}</span>
                <span class="alert-meta">Size: Simulated â€¢ ${timeOffset}</span>
            </div>
        `;
        uploadedFilesList.insertBefore(li, uploadedFilesList.firstChild);
    }
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('dynamic-report-btn')) {
             modalBackdrop.classList.remove('hidden');
        }
    });

    closeModalBtn.addEventListener('click', closeDtModal);
    cancelDownloadBtn.addEventListener('click', closeDtModal);
    modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop) closeDtModal();
    });

    function closeDtModal() {
        modalBackdrop.classList.add('hidden');
    }

    confirmDownloadBtn.addEventListener('click', () => {
        const link = document.createElement('a');
        link.href = 'assets/IntelliBlue_Report.pdf';
        link.download = 'IntelliBlue_Incident_Report_INC-2024-001.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        closeDtModal();
        setTimeout(() => {
            addBotMessage("Report downloaded successfully.");
        }, 1000);
    });
    logoutBtn.addEventListener('click', () => {
        document.body.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f4f7fa;flex-direction:column;"><h2>Logged Out</h2><p>Reload page to restart demo.</p></div>';
    });

});

