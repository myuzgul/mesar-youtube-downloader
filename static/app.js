document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const urlInput = document.getElementById('urlInput');
    const btnPaste = document.getElementById('btnPaste');
    const btnAnalyze = document.getElementById('btnAnalyze');
    const btnAnalyzeText = document.getElementById('btnAnalyzeText');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    const resultCard = document.getElementById('resultCard');
    const videoThumbnail = document.getElementById('videoThumbnail');
    const videoDuration = document.getElementById('videoDuration');
    const videoTitle = document.getElementById('videoTitle');
    const videoUploader = document.getElementById('videoUploader');
    const videoViews = document.getElementById('videoViews');

    const presetsGrid = document.getElementById('presetsGrid');
    const customFormatsContainer = document.getElementById('customFormatsContainer');
    const customFormatsTbody = document.getElementById('customFormatsTbody');
    const selectedFormatTitle = document.getElementById('selectedFormatTitle');
    const btnStartDownload = document.getElementById('btnStartDownload');

    const progressCard = document.getElementById('progressCard');
    const progressStatusTitle = document.getElementById('progressStatusTitle');
    const progressFileName = document.getElementById('progressFileName');
    const progressPercentBadge = document.getElementById('progressPercentBadge');
    const progressBarFill = document.getElementById('progressBarFill');
    const statDownloaded = document.getElementById('statDownloaded');
    const statSpeed = document.getElementById('statSpeed');
    const statEta = document.getElementById('statEta');
    const statusSpinner = document.getElementById('statusSpinner');
    const downloadCompleteBox = document.getElementById('downloadCompleteBox');

    const btnOpenFolder = document.getElementById('btnOpenFolder');
    const btnAdminPanel = document.getElementById('btnAdminPanel');
    const btnOpenCompletedFolder = document.getElementById('btnOpenCompletedFolder');
    const btnRefreshHistory = document.getElementById('btnRefreshHistory');
    const historyList = document.getElementById('historyList');

    if (btnAdminPanel) {
        btnAdminPanel.addEventListener('click', () => {
            window.open('/admin', '_blank');
        });
    }

    // Credit & License Elements
    const creditBadge = document.getElementById('creditBadge');
    const creditStatusText = document.getElementById('creditStatusText');
    const licenseBadge = document.getElementById('licenseBadge');
    const licenseStatusText = document.getElementById('licenseStatusText');
    const licenseModal = document.getElementById('licenseModal');
    const hwidValue = document.getElementById('hwidValue');
    const btnCopyHWID = document.getElementById('btnCopyHWID');
    const licenseKeyInput = document.getElementById('licenseKeyInput');
    const btnActivateLicense = document.getElementById('btnActivateLicense');
    const licenseError = document.getElementById('licenseError');
    const licenseErrorText = document.getElementById('licenseErrorText');

    // Out of Credits Modal Elements
    const outOfCreditsModal = document.getElementById('outOfCreditsModal');
    const btnBuyLicense = document.getElementById('btnBuyLicense');
    const modalLicenseKeyInput = document.getElementById('modalLicenseKeyInput');
    const btnModalActivate = document.getElementById('btnModalActivate');
    const modalLicenseError = document.getElementById('modalLicenseError');
    const modalLicenseErrorText = document.getElementById('modalLicenseErrorText');

    // State Variables
    let currentVideoInfo = null;
    let selectedPresetId = 'best';
    let selectedCustomFormatId = null;
    let activeFilter = 'all';
    let isLicenseActivated = false;
    let freeCreditsRemaining = 10;

    // License & Credit Check
    async function checkLicenseStatus() {
        try {
            const res = await fetch('/api/license/status');
            const data = await res.json();
            updateCreditUI(data);
        } catch (err) {
            console.error("Lisans ve kredi durumu kontrol edilemedi:", err);
        }
    }

    function updateCreditUI(data) {
        if (!data) return;
        hwidValue.textContent = data.hwid || 'HWID-0000-0000-0000';
        isLicenseActivated = data.activated;
        freeCreditsRemaining = data.free_credits_remaining !== undefined ? data.free_credits_remaining : 10;

        if (data.activated) {
            creditBadge.classList.add('hidden');
            licenseBadge.className = 'license-badge activated';
            licenseStatusText.textContent = 'PRO Lisanslı';
            licenseModal.classList.add('hidden');
            outOfCreditsModal.classList.add('hidden');
        } else {
            creditBadge.classList.remove('hidden');
            creditStatusText.textContent = `Kalan Hak: ${freeCreditsRemaining} / ${data.max_credits || 10}`;

            if (freeCreditsRemaining > 5) {
                creditBadge.className = 'credit-badge credit-green';
            } else if (freeCreditsRemaining > 0) {
                creditBadge.className = 'credit-badge credit-orange';
            } else {
                creditBadge.className = 'credit-badge credit-red';
            }

            licenseBadge.className = 'license-badge unactivated';
            licenseStatusText.textContent = 'Ücretsiz Sürüm';

            if (freeCreditsRemaining <= 0) {
                outOfCreditsModal.classList.remove('hidden');
            }
        }
    }

    licenseBadge.addEventListener('click', () => {
        licenseModal.classList.remove('hidden');
    });

    btnCopyHWID.addEventListener('click', () => {
        navigator.clipboard.writeText(hwidValue.textContent);
        btnCopyHWID.innerHTML = '<i class="fa-solid fa-check"></i>';
        setTimeout(() => {
            btnCopyHWID.innerHTML = '<i class="fa-regular fa-copy"></i>';
        }, 2000);
    });

    btnActivateLicense.addEventListener('click', async () => {
        const key = licenseKeyInput.value.trim();
        if (!key) {
            showLicenseError("Lütfen lisans anahtarınızı girin.");
            return;
        }

        btnActivateLicense.disabled = true;
        hideLicenseError();

        try {
            const res = await fetch('/api/license/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key })
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || "Lisans doğrulanamadı.");
            }

            // Success
            isLicenseActivated = true;
            checkLicenseStatus();
        } catch (err) {
            showLicenseError(err.message);
        } finally {
            btnActivateLicense.disabled = false;
        }
    });

    // Out of Credits Modal Handlers
    creditBadge.addEventListener('click', () => {
        if (!isLicenseActivated && freeCreditsRemaining <= 0) {
            outOfCreditsModal.classList.remove('hidden');
        } else if (!isLicenseActivated) {
            licenseModal.classList.remove('hidden');
        }
    });

    const btnModalBuyFromLicense = document.getElementById('btnModalBuyFromLicense');
    if (btnModalBuyFromLicense) {
        btnModalBuyFromLicense.addEventListener('click', () => {
            window.open('https://www.shopier.com/mesarajans/49988395', '_blank');
        });
    }

    if (btnBuyLicense) {
        btnBuyLicense.addEventListener('click', () => {
            window.open('https://www.shopier.com/mesarajans/49988395', '_blank');
        });
    }

    btnModalActivate.addEventListener('click', async () => {
        const key = modalLicenseKeyInput.value.trim();
        if (!key) {
            modalLicenseErrorText.textContent = "Lütfen lisans anahtarınızı girin.";
            modalLicenseError.classList.remove('hidden');
            return;
        }

        btnModalActivate.disabled = true;
        modalLicenseError.classList.add('hidden');

        try {
            const res = await fetch('/api/license/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key })
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || "Lisans doğrulanamadı.");
            }

            // Success
            isLicenseActivated = true;
            outOfCreditsModal.classList.add('hidden');
            checkLicenseStatus();
        } catch (err) {
            modalLicenseErrorText.textContent = err.message;
            modalLicenseError.classList.remove('hidden');
        } finally {
            btnModalActivate.disabled = false;
        }
    });

    function showLicenseError(msg) {
        licenseErrorText.textContent = msg;
        licenseError.classList.remove('hidden');
    }

    function hideLicenseError() {
        licenseError.classList.add('hidden');
    }

    // Clipboard Paste Handler
    btnPaste.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                urlInput.value = text.trim();
                hideError();
            }
        } catch (err) {
            console.log("Panoya erişilemedi: ", err);
        }
    });

    // Analyze URL Handler
    btnAnalyze.addEventListener('click', analyzeUrl);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') analyzeUrl();
    });

    async function analyzeUrl() {
        if (!isLicenseActivated && freeCreditsRemaining <= 0) {
            outOfCreditsModal.classList.remove('hidden');
            return;
        }

        const url = urlInput.value.trim();
        if (!url) {
            showError("Lütfen geçerli bir YouTube URL'si girin.");
            return;
        }

        hideError();
        setAnalyzeLoading(true);
        resultCard.classList.add('hidden');
        progressCard.classList.add('hidden');

        try {
            const res = await fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || "Video bilgileri alınamadı.");
            }

            currentVideoInfo = data;
            renderVideoInfo(data);
            resultCard.classList.remove('hidden');

        } catch (err) {
            showError(err.message);
        } finally {
            setAnalyzeLoading(false);
        }
    }

    function renderVideoInfo(info) {
        videoThumbnail.src = info.thumbnail || '';
        videoDuration.textContent = info.duration_str || '00:00';
        videoTitle.textContent = info.title || 'Video';
        videoUploader.textContent = info.uploader || 'Kanal';
        videoViews.textContent = info.view_count_str || '';

        // Reset Selection
        selectedPresetId = 'best';
        selectedCustomFormatId = null;
        renderPresets(info.presets);
        renderCustomFormats(info.raw_formats);
        updateSelectedSummary("En Yüksek Kalite (Otomatik)");
    }

    function renderPresets(presets) {
        presetsGrid.innerHTML = '';

        const filtered = presets.filter(p => {
            if (activeFilter === 'video') return p.type === 'video';
            if (activeFilter === 'audio') return p.type === 'audio';
            return true;
        });

        filtered.forEach(preset => {
            const card = document.createElement('div');
            card.className = `preset-card ${preset.id === selectedPresetId ? 'selected' : ''}`;
            card.dataset.id = preset.id;

            card.innerHTML = `
                <div class="preset-top">
                    <span class="preset-title">${preset.title}</span>
                    <span class="badge">${preset.tag}</span>
                </div>
                <div class="preset-desc">${preset.desc}</div>
            `;

            card.addEventListener('click', () => {
                document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                selectedPresetId = preset.id;
                selectedCustomFormatId = null;
                updateSelectedSummary(preset.title);
            });

            presetsGrid.appendChild(card);
        });
    }

    function renderCustomFormats(formats) {
        customFormatsTbody.innerHTML = '';
        const sorted = formats.filter(f => f.height || f.acodec !== 'none').slice(-20).reverse();

        sorted.forEach(f => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>${f.format_id}</code></td>
                <td>${f.resolution}</td>
                <td>${f.fps ? f.fps + ' fps' : '-'}</td>
                <td>${f.ext.toUpperCase()}</td>
                <td>${f.filesize_str}</td>
                <td>
                    <button class="btn-secondary btn-sm select-custom-btn" data-id="${f.format_id}">
                        Seç
                    </button>
                </td>
            `;

            tr.querySelector('.select-custom-btn').addEventListener('click', () => {
                document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
                selectedPresetId = 'custom';
                selectedCustomFormatId = f.format_id;
                updateSelectedSummary(`Özel Format: ${f.format_id} (${f.resolution})`);
            });

            customFormatsTbody.appendChild(tr);
        });
    }

    // Filter Tab Handlers
    document.querySelectorAll('.tab-btn').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeFilter = tab.dataset.filter;

            if (activeFilter === 'custom') {
                presetsGrid.classList.add('hidden');
                customFormatsContainer.classList.remove('hidden');
            } else {
                presetsGrid.classList.remove('hidden');
                customFormatsContainer.classList.add('hidden');
                if (currentVideoInfo) renderPresets(currentVideoInfo.presets);
            }
        });
    });

    function updateSelectedSummary(text) {
        selectedFormatTitle.textContent = text;
    }

    // Download Handler via WebSocket
    btnStartDownload.addEventListener('click', startDownload);

    function startDownload() {
        if (!isLicenseActivated && freeCreditsRemaining <= 0) {
            outOfCreditsModal.classList.remove('hidden');
            return;
        }

        if (!currentVideoInfo) return;

        progressCard.classList.remove('hidden');
        downloadCompleteBox.classList.add('hidden');
        statusSpinner.classList.remove('hidden');
        progressStatusTitle.textContent = "İndirme Başlatılıyor...";
        progressFileName.textContent = currentVideoInfo.title;
        progressPercentBadge.textContent = "0%";
        progressBarFill.style.width = "0%";
        statDownloaded.textContent = "0 MB / 0 MB";
        statSpeed.textContent = "--- MB/s";
        statEta.textContent = "---";

        progressCard.scrollIntoView({ behavior: 'smooth' });

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/download`;
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            socket.send(JSON.stringify({
                url: currentVideoInfo.url,
                preset_id: selectedPresetId,
                custom_format_id: selectedCustomFormatId
            }));
        };

        socket.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.credits) {
                updateCreditUI(msg.credits);
            }

            if (msg.code === 'OUT_OF_CREDITS') {
                statusSpinner.classList.add('hidden');
                outOfCreditsModal.classList.remove('hidden');
                return;
            }

            if (msg.status === 'starting') {
                progressStatusTitle.textContent = "Bağlantı Kuruldu...";
            } 
            else if (msg.status === 'downloading') {
                progressStatusTitle.textContent = "Akış İndiriliyor...";
                if (msg.filename) progressFileName.textContent = msg.filename;
                
                const pct = msg.percent || 0;
                progressPercentBadge.textContent = `${pct}%`;
                progressBarFill.style.width = `${pct}%`;

                statDownloaded.textContent = `${msg.downloaded_str || '0 MB'} / ${msg.total_str || '0 MB'}`;
                statSpeed.textContent = msg.speed_str || '---';
                statEta.textContent = msg.eta_str || '---';
            } 
            else if (msg.status === 'processing') {
                progressStatusTitle.textContent = "FFmpeg İle Birleştiriliyor...";
                progressBarFill.style.width = "100%";
                progressPercentBadge.textContent = "99%";
            } 
            else if (msg.status === 'completed') {
                progressStatusTitle.textContent = "İndirme Tamamlandı!";
                progressPercentBadge.textContent = "100%";
                progressBarFill.style.width = "100%";
                statusSpinner.classList.add('hidden');
                downloadCompleteBox.classList.remove('hidden');

                loadHistory();
            } 
            else if (msg.status === 'error') {
                progressStatusTitle.textContent = "Hata Oluştu!";
                statusSpinner.classList.add('hidden');
                showError(msg.message);
            }
        };

        socket.onerror = (err) => {
            console.error("WebSocket Hatası:", err);
            progressStatusTitle.textContent = "Bağlantı Hatası!";
            statusSpinner.classList.add('hidden');
        };
    }

    // Open Downloads Folder
    btnOpenFolder.addEventListener('click', openDownloadsFolder);
    btnOpenCompletedFolder.addEventListener('click', openDownloadsFolder);

    async function openDownloadsFolder() {
        try {
            await fetch('/api/open-downloads-folder', { method: 'POST' });
        } catch (err) {
            console.error("Klasör açılamadı: ", err);
        }
    }

    // Load History
    btnRefreshHistory.addEventListener('click', loadHistory);

    async function loadHistory() {
        try {
            const res = await fetch('/api/downloads-list');
            const data = await res.json();
            
            if (data.files && data.files.length > 0) {
                historyList.innerHTML = '';
                data.files.forEach(f => {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    item.innerHTML = `
                        <div>
                            <div class="file-name"><i class="fa-regular fa-file-video"></i> ${f.name}</div>
                            <div class="file-meta">${f.created_at} • ${f.size_str}</div>
                        </div>
                    `;
                    historyList.appendChild(item);
                });
            } else {
                historyList.innerHTML = '<div class="empty-history">Henüz bu oturumda indirilmiş bir dosya yok.</div>';
            }
        } catch (err) {
            console.error("Geçmiş yüklenemedi:", err);
        }
    }

    function setAnalyzeLoading(loading) {
        if (loading) {
            btnAnalyze.disabled = true;
            btnAnalyzeText.textContent = "Analiz Ediliyor...";
        } else {
            btnAnalyze.disabled = false;
            btnAnalyzeText.textContent = "Formatları Getir";
        }
    }

    function showError(msg) {
        errorText.textContent = msg;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.classList.add('hidden');
    }

    // Initial load
    checkLicenseStatus();
    loadHistory();
});
