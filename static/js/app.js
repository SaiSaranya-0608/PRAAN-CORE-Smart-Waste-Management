// ==========================================
// Global State & DOM Elements
// ==========================================
let currentUser = null;
let currentRole = null;

// DOM elements
const loginScreen = document.getElementById('login-screen');
const adminPortal = document.getElementById('admin-portal');
const userPortal = document.getElementById('user-portal');
const authMain = document.getElementById('auth-main');
const authAdmin = document.getElementById('auth-admin');
const authUser = document.getElementById('auth-user');

// Helper: Show toast notification
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.borderLeftColor = isError ? '#e74c3c' : '#2ecc71';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 4000);
}

// Helper: Show warning modal
function showWarningModal(messages) {
    const container = document.getElementById('warning-messages-container');
    container.innerHTML = messages.map(m => `<p>⚠️ ${m}</p>`).join('');
    document.getElementById('warning-modal').classList.add('active');
}

// ==========================================
// Authentication
// ==========================================
async function checkAuthStatus() {
    try {
        const res = await fetch('/api/auth/status');
        const data = await res.json();
        if (data.logged_in) {
            currentUser = data.username;
            currentRole = data.role;
            if (currentRole === 'admin') {
                loginScreen.classList.remove('active');
                adminPortal.classList.add('active');
                loadAdminDashboard();
            } else if (currentRole === 'user') {
                loginScreen.classList.remove('active');
                userPortal.classList.add('active');
                document.querySelector('#user-portal .display-username').innerText = currentUser;
                loadUserDashboard();
            }
        }
    } catch (err) {
        console.error('Auth check failed', err);
    }
}

async function login(username, password, role) {
    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Welcome, ${username}!`);
            currentUser = username;
            currentRole = data.role;
            loginScreen.classList.remove('active');
            if (data.role === 'admin') {
                adminPortal.classList.add('active');
                loadAdminDashboard();
            } else {
                userPortal.classList.add('active');
                document.querySelector('#user-portal .display-username').innerText = username;
                loadUserDashboard();
            }
        } else {
            showToast(data.message, true);
        }
    } catch (err) {
        showToast('Server error. Try again.', true);
    }
}

async function register(username, password) {
    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Registration successful! Please login.');
            // Switch back to login
            document.querySelectorAll('#auth-user .nav-auth-back').forEach(btn => btn.click());
        } else {
            showToast(data.message, true);
        }
    } catch (err) {
        showToast('Server error.', true);
    }
}

function logout() {
    fetch('/api/logout', { method: 'POST' }).then(() => {
        currentUser = null;
        currentRole = null;
        loginScreen.classList.add('active');
        adminPortal.classList.remove('active');
        userPortal.classList.remove('active');
        showToast('Logged out.');
    }).catch(() => showToast('Logout failed', true));
}

// ==========================================
// Admin Dashboard Functions
// ==========================================
async function loadAdminDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        const stats = data.stats;
        document.getElementById('stat-treasury').innerHTML = `₹${stats.treasury.toFixed(2)}`;
        document.getElementById('stat-profit').innerHTML = `₹${(stats.revenue - stats.expense).toFixed(2)}`;
        document.getElementById('stat-total-waste').innerHTML = `${stats.total_waste} kg`;
        document.getElementById('stat-active-bins').innerHTML = `${stats.active_bins}/${stats.total_bins}`;
        
        const logsList = document.getElementById('session-logs-list');
        logsList.innerHTML = data.session_logs.map(log => `<li>${log}</li>`).join('');
        
        // Load other sections
        loadBinsTable();
        loadFleetTable();
        loadFacilities();
        loadWeatherTable();
        loadAreasForSelectors();
    } catch (err) {
        console.error('Dashboard load error', err);
    }
}

async function loadBinsTable() {
    try {
        const res = await fetch('/api/bins');
        const data = await res.json();
        const tbody = document.getElementById('bins-table-body');
        tbody.innerHTML = data.bins.map(b => `
            <tr>
                <td>${b.id}</td>
                <td>${b.area}</td>
                <td>${b.source}</td>
                <td>${b.fill}/${b.max_limit} kg</td>
                <td>${b.overflow} kg</td>
                <td>${b.contaminated ? 'Yes' : 'No'}</td>
                <td>${b.active_vehicle}</td>
            </tr>
        `).join('');
    } catch(err) { console.error(err); }
}

async function loadFleetTable() {
    try {
        const res = await fetch('/api/fleet');
        const data = await res.json();
        const tbody = document.getElementById('fleet-table-body');
        tbody.innerHTML = data.fleet.map(v => `
            <tr>
                <td>${v.id}</td>
                <td>${v.type}</td>
                <td>${v.area}</td>
                <td>${v.fuel}%</td>
                <td>${v.health}%</td>
                <td>${v.broken ? 'Yes' : 'No'}</td>
                <td>${v.role}</td>
            </tr>
        `).join('');
    } catch(err) { console.error(err); }
}

async function loadFacilities() {
    try {
        const res = await fetch('/api/facilities');
        const data = await res.json();
        const container = document.getElementById('facilities-container');
        container.innerHTML = data.facilities.map(f => `
            <div class="facility-card">
                <h4>${f.name}</h4>
                <div>Waste: ${f.waste_types.join(', ')}</div>
                <div>Load: ${f.current_load} / ${f.capacity} kg</div>
                <div class="load-bar"><div class="load-fill" style="width:${(f.current_load/f.capacity)*100}%"></div></div>
                <div>Storage: ${f.temporary_storage} kg</div>
                <div>Cost: ₹${f.cost_per_kg}/kg</div>
                <div>Status: <span class="${f.status === 'OPEN' ? 'text-success' : 'text-danger'}">${f.status}</span></div>
                <button class="btn btn-danger clear-facility-btn" data-facility="${f.raw_name}" style="margin-top:0.5rem; padding:0.4rem;">Clear Plant</button>
            </div>
        `).join('');
        document.querySelectorAll('.clear-facility-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const facility = btn.dataset.facility;
                document.getElementById('modal-facility-name').innerText = facility;
                document.getElementById('clear-modal').classList.add('active');
                document.getElementById('confirm-clear').onclick = () => clearFacility(facility);
            });
        });
    } catch(err) { console.error(err); }
}

async function clearFacility(facility) {
    try {
        const res = await fetch('/api/facilities/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ facility })
        });
        const data = await res.json();
        showToast(data.message, !data.success);
        document.getElementById('clear-modal').classList.remove('active');
        loadFacilities();
    } catch(err) { showToast('Error clearing facility', true); }
}

async function loadWeatherTable() {
    try {
        const res = await fetch('/api/weather');
        const data = await res.json();
        const tbody = document.getElementById('weather-table-body');
        tbody.innerHTML = data.areas.map(a => `
            <tr>
                <td>${a.area}</td>
                <td>${a.condition}</td>
                <td>${a.rain} mm</td>
                <td>${a.wind} km/h</td>
                <td>${a.temp} °C</td>
                <td class="${a.traffic === 'VERY HIGH' ? 'text-danger' : ''}">${a.traffic}</td>
                <td>${a.road_closed ? 'CLOSED' : 'Open'}</td>
            </tr>
        `).join('');
        document.getElementById('btn-toggle-weather').innerHTML = `Weather Mode: ${data.mode}`;
    } catch(err) { console.error(err); }
}

async function loadAreasForSelectors() {
    try {
        const res = await fetch('/api/bins');
        const data = await res.json();
        const areas = data.areas;
        const zoneSelect = document.getElementById('zone-select');
        const singleBinAreaSelect = document.getElementById('single-bin-area-select');
        const injectArea = document.getElementById('inject-area');
        zoneSelect.innerHTML = '<option value="">Select Area...</option>' + areas.map(a => `<option value="${a}">${a}</option>`).join('');
        singleBinAreaSelect.innerHTML = '<option value="">Select Area...</option>' + areas.map(a => `<option value="${a}">${a}</option>`).join('');
        injectArea.innerHTML = '<option value="">Select Area...</option>' + areas.map(a => `<option value="${a}">${a}</option>`).join('');
        
        singleBinAreaSelect.onchange = async () => {
            const area = singleBinAreaSelect.value;
            if (!area) return;
            const binsRes = await fetch('/api/bins');
            const binsData = await binsRes.json();
            const bins = binsData.bins.filter(b => b.area === area);
            const binSelect = document.getElementById('single-bin-select');
            binSelect.innerHTML = '<option value="">Select Bin...</option>' + bins.map(b => `<option value="${b.id}">${b.id} (${b.fill}/${b.max_limit} kg)</option>`).join('');
        };
        injectArea.onchange = async () => {
            const area = injectArea.value;
            if (!area) return;
            const binsRes = await fetch('/api/bins');
            const binsData = await binsRes.json();
            const bins = binsData.bins.filter(b => b.area === area);
            const binSelect = document.getElementById('inject-bin');
            binSelect.innerHTML = '<option value="">Select Bin...</option>' + bins.map(b => `<option value="${b.id}">${b.id} (${b.fill}/${b.max_limit} kg)</option>`).join('');
            const allowedInfo = document.getElementById('inject-allowed-info');
            if (bins[0]) allowedInfo.innerText = `Allowed: ${bins[0].allowed_waste.join(', ')}`;
        };
    } catch(err) { console.error(err); }
}

// Dispatch actions
async function priorityClear() {
    try {
        const res = await fetch('/api/dispatch/priority', { method: 'POST' });
        const data = await res.json();
        showToast(data.message, !data.success);
        loadBinsTable();
        loadAdminDashboard();
    } catch(err) { showToast('Error', true); }
}

async function singleBinClear() {
    const binId = document.getElementById('single-bin-select').value;
    if (!binId) { showToast('Select a bin', true); return; }
    try {
        const res = await fetch('/api/dispatch/bin', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ bin_id: binId }) });
        const data = await res.json();
        showToast(data.message, !data.success);
        loadBinsTable();
        loadAdminDashboard();
    } catch(err) { showToast('Error', true); }
}

async function zoneClear() {
    const area = document.getElementById('zone-select').value;
    const mode = document.getElementById('zone-mode-select').value;
    if (!area) { showToast('Select an area', true); return; }
    try {
        const res = await fetch('/api/dispatch/zone', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ area, mode }) });
        const data = await res.json();
        showToast(data.message, !data.success);
        loadBinsTable();
        loadAdminDashboard();
    } catch(err) { showToast('Error', true); }
}

async function citySweep() {
    const mode = document.getElementById('sweep-mode-select').value;
    const reroute = (mode === 'reroute');
    try {
        const res = await fetch('/api/dispatch/sweep', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reroute }) });
        const data = await res.json();
        showToast(data.message, !data.success);
        loadBinsTable();
        loadAdminDashboard();
    } catch(err) { showToast('Error', true); }
}

async function addAdmin() {
    const username = document.getElementById('new-admin-user').value.trim();
    const password = document.getElementById('new-admin-pass').value.trim();
    if (!username || !password) { showToast('Fill both fields', true); return; }
    try {
        const res = await fetch('/api/admin/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
        const data = await res.json();
        showToast(data.message, !data.success);
        if (data.success) {
            document.getElementById('new-admin-user').value = '';
            document.getElementById('new-admin-pass').value = '';
        }
    } catch(err) { showToast('Error', true); }
}

// Fleet actions (global app.postFleetAction already defined in HTML, but we'll redefine)
window.app = window.app || {};
app.postFleetAction = async (action) => {
    try {
        const res = await fetch('/api/fleet/action', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action }) });
        const data = await res.json();
        showToast(data.message, !data.success);
        loadFleetTable();
        loadAdminDashboard();
    } catch(err) { showToast('Error', true); }
};

// Clear logs
document.getElementById('btn-clear-logs')?.addEventListener('click', async () => {
    await fetch('/api/logs/clear', { method: 'POST' });
    showToast('Logs cleared');
    loadAdminDashboard();
});

// Toggle weather mode
document.getElementById('btn-toggle-weather')?.addEventListener('click', async () => {
    await fetch('/api/weather/toggle', { method: 'POST' });
    loadWeatherTable();
});

// Inject waste modal
document.getElementById('btn-open-inject')?.addEventListener('click', () => {
    document.getElementById('inject-modal').classList.add('active');
});
document.getElementById('btn-submit-inject')?.addEventListener('click', async () => {
    const area = document.getElementById('inject-area').value;
    const binId = document.getElementById('inject-bin').value;
    const wtype = document.getElementById('inject-wtype').value.trim().toUpperCase();
    const qty = parseFloat(document.getElementById('inject-qty').value);
    if (!area || !binId || !wtype || isNaN(qty) || qty <= 0) {
        showToast('Fill all fields correctly', true);
        return;
    }
    try {
        const res = await fetch('/api/bins/inject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ area, bin_id: binId, wtype, qty })
        });
        const data = await res.json();
        if (data.warnings && data.warnings.length) {
            showWarningModal(data.warnings);
        } else {
            showToast(data.message, !data.success);
        }
        document.getElementById('inject-modal').classList.remove('active');
        loadBinsTable();
        loadAdminDashboard();
    } catch(err) { showToast('Error', true); }
});

// ==========================================
// User Dashboard
// ==========================================
async function loadUserDashboard() {
    try {
        const res = await fetch('/api/user/info');
        const data = await res.json();
        if (data.success) {
            document.getElementById('user-penalty-amount').innerHTML = `₹${data.penalty}`;
            const payBtn = document.getElementById('btn-user-pay');
            if (data.penalty > 0) payBtn.style.display = 'block';
            else payBtn.style.display = 'none';
        }
    } catch(err) { console.error(err); }
}

document.getElementById('btn-user-pay')?.addEventListener('click', async () => {
    try {
        const res = await fetch('/api/user/pay', { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
        loadUserDashboard();
    } catch(err) { showToast('Error', true); }
});

document.getElementById('btn-user-inject-open')?.addEventListener('click', () => {
    document.getElementById('inject-modal').classList.add('active');
});

// ==========================================
// Navigation & UI Events
// ==========================================
// Auth navigation
document.getElementById('nav-admin-login')?.addEventListener('click', () => {
    authMain.style.display = 'none';
    authAdmin.style.display = 'block';
});
document.getElementById('nav-user-login')?.addEventListener('click', () => {
    authMain.style.display = 'none';
    authUser.style.display = 'block';
});
document.querySelectorAll('.nav-auth-back').forEach(btn => {
    btn.addEventListener('click', () => {
        authAdmin.style.display = 'none';
        authUser.style.display = 'none';
        authMain.style.display = 'block';
    });
});

document.getElementById('btn-login-admin')?.addEventListener('click', () => {
    const username = document.getElementById('admin-username').value.trim();
    const password = document.getElementById('admin-password').value.trim();
    login(username, password, 'admin');
});
document.getElementById('btn-login-user')?.addEventListener('click', () => {
    const username = document.getElementById('user-username').value.trim();
    const password = document.getElementById('user-password').value.trim();
    login(username, password, 'user');
});
document.getElementById('btn-register-user')?.addEventListener('click', () => {
    const username = document.getElementById('user-username').value.trim();
    const password = document.getElementById('user-password').value.trim();
    register(username, password);
});

document.querySelectorAll('.btn-logout').forEach(btn => {
    btn.addEventListener('click', logout);
});

// Sidebar navigation
document.querySelectorAll('.nav-item').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = link.dataset.target;
        document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active'));
        document.getElementById(target).classList.add('active');
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        link.classList.add('active');
    });
});

// Dispatch buttons
document.getElementById('btn-priority-clear')?.addEventListener('click', priorityClear);
document.getElementById('btn-single-bin-clear')?.addEventListener('click', singleBinClear);
document.getElementById('btn-zone-clear')?.addEventListener('click', zoneClear);
document.getElementById('btn-full-sweep')?.addEventListener('click', citySweep);
document.getElementById('btn-add-admin')?.addEventListener('click', addAdmin);

// Cancel clear modal
document.getElementById('cancel-clear')?.addEventListener('click', () => {
    document.getElementById('clear-modal').classList.remove('active');
});

// Close warning modal on acknowledge
document.querySelector('#warning-modal .btn-danger')?.addEventListener('click', () => {
    document.getElementById('warning-modal').classList.remove('active');
});

// Initial auth check
checkAuthStatus();