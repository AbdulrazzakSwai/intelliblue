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
    
    const fpModal = document.getElementById('false-positive-modal');
    const closeFpModalBtn = document.querySelector('.close-modal-fp');
    const cancelFpBtn = document.getElementById('cancel-fp');
    const submitFpBtn = document.getElementById('submit-fp');
    const fpDetails = document.getElementById('fp-details');

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
    <div style="margin-top:10px;">
        <button class="btn-confirm dynamic-report-btn">Generate Incident Report</button>
        <button class="btn-escalate dynamic-escalate-btn">Escalate to Tier 2</button>
    </div>
    `;

    const DEFAULT_GREETING = "I am IntelliBlue, please upload your security files so that I can analyze them.";
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
                    typeHtmlMessage(msgDiv, htmlContent, () => {
                        let btnContainer = msgDiv.querySelector('div[style*="margin-top"]');
                        if (!btnContainer) {
                            btnContainer = document.createElement('div');
                            btnContainer.style.marginTop = '10px';
                            msgDiv.appendChild(btnContainer);
                        }
                        const fpBtn = document.createElement('button');
                        fpBtn.className = 'btn-false-positive';
                        fpBtn.textContent = 'False Positive';
                        btnContainer.appendChild(fpBtn);
                        scrollToBottom();
                    });
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

    function typeHtmlMessage(element, html, onComplete) {
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
                if (onComplete) onComplete();
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
        if (e.target.classList.contains('btn-false-positive')) {
             fpModal.classList.remove('hidden');
        }
        if (e.target.classList.contains('dynamic-escalate-btn')) {
             e.target.disabled = true;
             e.target.textContent = "Escalating...";
             addUserMessage("Action: Escalate to Tier 2");
             setTimeout(() => {
                 addBotMessage("<strong>Escalation Successful</strong><br>Ticket <strong>#ESC-8842</strong> has been created and assigned to the Tier 2 SOC queue. An analyst will review this incident shortly.", true);
             }, 800);
        }
    });

    function closeFpModal() {
        fpModal.classList.add('hidden');
        fpDetails.value = '';
    }

    if (closeFpModalBtn) closeFpModalBtn.addEventListener('click', closeFpModal);
    if (cancelFpBtn) cancelFpBtn.addEventListener('click', closeFpModal);
    if (fpModal) {
        fpModal.addEventListener('click', (e) => {
            if (e.target === fpModal) closeFpModal();
        });
    }

    if (submitFpBtn) {
        submitFpBtn.addEventListener('click', () => {
            const reason = fpDetails.value.trim();
            if (!reason) {
                alert('Please provide a reason.');
                return;
            }
            closeFpModal();
            addUserMessage(`False Positive Report: ${reason}`);
            setTimeout(() => {
                addBotMessage("Thank you. This analysis has been flagged as a false positive and sent for review.", false);
            }, 800);
        });
    }

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

    const aboutBtn = document.getElementById('about-btn');
    const aboutModal = document.getElementById('about-modal');
    const closeAboutBtn = document.getElementById('close-about-modal');

    if (aboutBtn && aboutModal) {
        aboutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            aboutModal.classList.remove('hidden');
        });
    }

    function closeAboutModalFunc() {
        if (aboutModal) aboutModal.classList.add('hidden');
    }

    if (closeAboutBtn) {
        closeAboutBtn.addEventListener('click', closeAboutModalFunc);
    }

    if (aboutModal) {
        aboutModal.addEventListener('click', (e) => {
            if (e.target === aboutModal) closeAboutModalFunc();
        });
    }

    logoutBtn.addEventListener('click', () => {
        document.body.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f4f7fa;flex-direction:column;"><h2>Logged Out</h2><p>Reload page to restart demo.</p></div>';
    });

    const canvas = document.getElementById('bg-particles');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particlesArray;

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            init();
        });

        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.directionX = (Math.random() * 0.4) - 0.2;
                this.directionY = (Math.random() * 0.4) - 0.2;
                this.size = Math.random() * 3 + 1.5;
                this.color = 'rgba(37, 99, 235, 0.9)'; 
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
                ctx.fillStyle = this.color;
                ctx.fill();
            }
            update() {
                if (this.x > canvas.width || this.x < 0) {
                    this.directionX = -this.directionX;
                }
                if (this.y > canvas.height || this.y < 0) {
                    this.directionY = -this.directionY;
                }
                this.x += this.directionX;
                this.y += this.directionY;
                this.draw();
            }
        }

        function init() {
            particlesArray = [];
            let numberOfParticles = (canvas.height * canvas.width) / 9000;
            for (let i = 0; i < numberOfParticles; i++) {
                particlesArray.push(new Particle());
            }
        }

        function animate() {
            requestAnimationFrame(animate);
            ctx.clearRect(0, 0, innerWidth, innerHeight);
            
            for (let i = 0; i < particlesArray.length; i++) {
                particlesArray[i].update();
            }
            connect();
        }

        function connect() {
            let opacityValue = 1;
            for (let a = 0; a < particlesArray.length; a++) {
                for (let b = a; b < particlesArray.length; b++) {
                    let distance = ((particlesArray[a].x - particlesArray[b].x) * (particlesArray[a].x - particlesArray[b].x)) + 
                                   ((particlesArray[a].y - particlesArray[b].y) * (particlesArray[a].y - particlesArray[b].y));
                    if (distance < (canvas.width/7) * (canvas.height/7)) {
                        opacityValue = 1 - (distance/20000);
                        ctx.strokeStyle = 'rgba(37, 99, 235,' + opacityValue * 0.5 + ')';
                        ctx.lineWidth = 1.5;
                        ctx.beginPath();
                        ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
                        ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
                        ctx.stroke();
                    }
                }
            }
        }

        init();
        animate();
    }

});

