document.addEventListener('DOMContentLoaded', () => {
    const adminLoginOverlay = document.getElementById('adminLoginOverlay');
    const adminPasswordInput = document.getElementById('adminPasswordInput');
    const btnLogin = document.getElementById('btnLogin');
    const loginErrorMsg = document.getElementById('loginErrorMsg');
    const loginErrorText = document.getElementById('loginErrorText');
    const btnLogout = document.getElementById('btnLogout');

    const keyPrefix = document.getElementById('keyPrefix');
    const keyCount = document.getElementById('keyCount');
    const keyNote = document.getElementById('keyNote');
    const btnGenerateKeys = document.getElementById('btnGenerateKeys');

    const keysTbody = document.getElementById('keysTbody');
    const btnRefreshKeys = document.getElementById('btnRefreshKeys');
    const btnExportTxt = document.getElementById('btnExportTxt');

    let currentPassword = localStorage.getItem('admin_password') || '';

    if (currentPassword) {
        verifyPassword(currentPassword);
    }

    btnLogin.addEventListener('click', () => {
        const pass = adminPasswordInput.value.trim();
        if (!pass) return;
        verifyPassword(pass);
    });

    adminPasswordInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') btnLogin.click();
    });

    btnLogout.addEventListener('click', () => {
        localStorage.removeItem('admin_password');
        currentPassword = '';
        adminLoginOverlay.classList.remove('hidden');
    });

    async function verifyPassword(pass) {
        try {
            const res = await fetch('/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: pass })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Hatalı şifre!");

            // Auth success
            currentPassword = pass;
            localStorage.setItem('admin_password', pass);
            adminLoginOverlay.classList.add('hidden');
            loginErrorMsg.classList.add('hidden');
            loadKeysList();
        } catch (err) {
            loginErrorText.textContent = err.message;
            loginErrorMsg.classList.remove('hidden');
            localStorage.removeItem('admin_password');
        }
    }

    btnGenerateKeys.addEventListener('click', async () => {
        if (!currentPassword) return;

        const prefix = keyPrefix.value;
        const count = parseInt(keyCount.value) || 1;
        const note = keyNote.value.trim();

        btnGenerateKeys.disabled = true;

        try {
            const res = await fetch('/api/admin/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    password: currentPassword,
                    count: count,
                    prefix: prefix,
                    note: note
                })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Lisans üretilemedi.");

            keyNote.value = '';
            loadKeysList();
        } catch (err) {
            alert(err.message);
        } finally {
            btnGenerateKeys.disabled = false;
        }
    });

    btnRefreshKeys.addEventListener('click', loadKeysList);

    async function loadKeysList() {
        if (!currentPassword) return;

        try {
            const res = await fetch('/api/admin/keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: currentPassword })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Lisanslar çekilemedi.");

            renderKeysTable(data.keys || []);
        } catch (err) {
            console.error("Lisanslar yüklenemedi:", err);
        }
    }

    function renderKeysTable(keys) {
        keysTbody.innerHTML = '';
        if (keys.length === 0) {
            keysTbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">
                        Henüz üretilmiş lisans anahtarı bulunmuyor.
                    </td>
                </tr>
            `;
            return;
        }

        keys.forEach(k => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>${k.key}</code></td>
                <td><span style="background: rgba(99,102,241,0.2); color:#a5b4fc; padding:2px 8px; border-radius:4px; font-size:0.8rem; font-weight:600;">${k.prefix}</span></td>
                <td style="color: #e2e8f0; font-size: 0.9rem;">${k.note || '-'}</td>
                <td style="color: var(--text-muted); font-size: 0.85rem;">${k.created_at_str || '-'}</td>
                <td>
                    <button class="btn-secondary btn-sm copy-key-btn" data-key="${k.key}">
                        <i class="fa-regular fa-copy"></i> Kopyala
                    </button>
                </td>
            `;

            tr.querySelector('.copy-key-btn').addEventListener('click', (e) => {
                const btn = e.currentTarget;
                navigator.clipboard.writeText(k.key);
                btn.innerHTML = '<i class="fa-solid fa-check"></i> Kopyalandı';
                setTimeout(() => {
                    btn.innerHTML = '<i class="fa-regular fa-copy"></i> Kopyala';
                }, 2000);
            });

            keysTbody.appendChild(tr);
        });
    }

    btnExportTxt.addEventListener('click', async () => {
        if (!currentPassword) return;

        try {
            const res = await fetch('/api/admin/keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: currentPassword })
            });

            const data = await res.json();
            const keys = data.keys || [];

            if (keys.length === 0) {
                alert("İndirilecek lisans anahtarı bulunmuyor.");
                return;
            }

            let txtContent = "MediaDownloader PRO - Uretilen Lisans Anahtarlari\n";
            txtContent += "===============================================\n\n";
            keys.forEach(k => {
                txtContent += `${k.key} | ${k.prefix} | ${k.note || 'Not Yok'} | ${k.created_at_str}\n`;
            });

            const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `MediaDownloader_Lisanslar_${new Date().toISOString().slice(0,10)}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            alert("İndirme hatası: " + err.message);
        }
    });
});
