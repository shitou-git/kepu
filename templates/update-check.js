(function() {
    const CACHE_KEY = 'kepu_content_cache';
    const VERSION_KEY = 'kepu_version';
    const UPDATE_INTERVAL = 1000 * 60 * 60;

    let hasUpdate = false;
    let currentVersion = null;

    async function getOnlineVersion() {
        try {
            const response = await fetch('https://shitou-git.github.io/kepu/config.json');
            if (response.ok) {
                const config = await response.json();
                return config.version;
            }
        } catch (e) {
            console.log('无法检测在线版本', e);
        }
        return null;
    }

    async function getLocalVersion() {
        if (typeof Capacitor !== 'undefined' && Capacitor.Plugins.Preferences) {
            try {
                const res = await Capacitor.Plugins.Preferences.get({ key: VERSION_KEY });
                return res.value || null;
            } catch (e) {}
        }
        return localStorage.getItem(VERSION_KEY);
    }

    async function saveVersion(version) {
        if (typeof Capacitor !== 'undefined' && Capacitor.Plugins.Preferences) {
            try {
                await Capacitor.Plugins.Preferences.set({ key: VERSION_KEY, value: version });
            } catch (e) {}
        }
        localStorage.setItem(VERSION_KEY, version);
    }

    function showUpdateToast() {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--primary);
            color: white;
            padding: 12px 24px;
            border-radius: 24px;
            box-shadow: var(--shadow);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideUp 0.3s ease-out;
        `;
        toast.innerHTML = `
            <span>📢</span>
            <span>发现新内容！正在刷新...</span>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    function showOfflineToast() {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--text-light);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            box-shadow: var(--shadow);
            z-index: 1000;
            font-size: 0.9em;
            animation: slideUp 0.3s ease-out;
        `;
        toast.textContent = '📡 离线模式，显示缓存内容';
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 2500);
    }

    async function checkUpdate() {
        const onlineVersion = await getOnlineVersion();
        const localVersion = await getLocalVersion();

        if (!onlineVersion) {
            showOfflineToast();
            return;
        }

        if (!localVersion) {
            await saveVersion(onlineVersion);
            return;
        }

        if (onlineVersion !== localVersion) {
            hasUpdate = true;
            currentVersion = onlineVersion;
            showUpdateToast();

            setTimeout(() => {
                window.location.reload(true);
            }, 1500);
        }
    }

    async function init() {
        const lastCheck = localStorage.getItem('kepu_last_check');
        const now = Date.now();

        if (!lastCheck || now - parseInt(lastCheck) > UPDATE_INTERVAL) {
            localStorage.setItem('kepu_last_check', now.toString());
            await checkUpdate();
        }
    }

    init();

    window.KepuUpdate = {
        check: checkUpdate,
        hasUpdate: () => hasUpdate,
        version: () => currentVersion
    };
})();
