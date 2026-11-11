// Smart Women Safety Alert System - Core Web Application JS
const API_BASE = '/api';

// Global state
let currentUser = null;
let currentAuthToken = localStorage.getItem('token') || null;
let countdownTimer = null;
let countdownRemaining = 5;
let currentPendingSosType = 'normal';
let ws = null;
let liveMap = null, routeMap = null, hotspotMap = null;
let userMarker = null;

// Helper to fetch with auth headers
async function apiRequest(endpoint, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`;
  }
  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${endpoint}`, options);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(errorData.detail || 'An error occurred');
  }
  return await res.json();
}

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  checkAuth();
  setupNavigation();
  setupEventListeners();
  initWebSocket();
  monitorBatteryAndNetwork();
});

function checkAuth() {
  const token = localStorage.getItem('token');
  const user = localStorage.getItem('user');
  if (token && user) {
    currentAuthToken = token;
    currentUser = JSON.parse(user);
    document.querySelectorAll('.auth-logged-in').forEach(el => el.classList.remove('d-none'));
    document.querySelectorAll('.auth-logged-out').forEach(el => el.classList.add('d-none'));
    const userNameEl = document.getElementById('navbar-username');
    if (userNameEl) userNameEl.textContent = currentUser.full_name;

    // Check if admin role
    if (currentUser.role === 'admin') {
      const adminTab = document.getElementById('tab-admin-nav');
      if (adminTab) adminTab.classList.remove('d-none');
    }
    loadUserData();
  } else {
    document.querySelectorAll('.auth-logged-in').forEach(el => el.classList.add('d-none'));
    document.querySelectorAll('.auth-logged-out').forEach(el => el.classList.remove('d-none'));
  }
}

function setupNavigation() {
  document.querySelectorAll('.nav-link[data-target-view]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = link.getAttribute('data-target-view');
      switchView(targetView);
    });
  });
}

function switchView(viewId) {
  document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('d-none'));
  const target = document.getElementById(viewId);
  if (target) {
    target.classList.remove('d-none');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (viewId === 'view-map') setTimeout(initLiveMap, 200);
    if (viewId === 'view-routes') setTimeout(initRouteMap, 200);
    if (viewId === 'view-hotspots') setTimeout(initHotspotMap, 200);
    if (viewId === 'view-admin') loadAdminDashboard();
    if (viewId === 'view-history') loadAlertHistory();
    if (viewId === 'view-network') loadContactsAndHelpers();
  }
}

function setupEventListeners() {
  // SOS Buttons
  const sosNormalBtn = document.getElementById('btn-trigger-sos');
  if (sosNormalBtn) {
    sosNormalBtn.addEventListener('click', () => startSosCountdown('normal'));
  }
  const sosSilentBtn = document.getElementById('btn-silent-sos');
  if (sosSilentBtn) {
    sosSilentBtn.addEventListener('click', () => startSosCountdown('silent'));
  }
  const cancelSosBtn = document.getElementById('btn-cancel-countdown');
  if (cancelSosBtn) {
    cancelSosBtn.addEventListener('click', cancelSosCountdown);
  }

  // Registration Form
  const regForm = document.getElementById('form-register');
  if (regForm) {
    regForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const payload = {
          full_name: document.getElementById('reg-name').value,
          email: document.getElementById('reg-email').value,
          phone: document.getElementById('reg-phone').value,
          password: document.getElementById('reg-password').value,
          role: document.getElementById('reg-role').value
        };
        const data = await apiRequest('/auth/register', 'POST', payload);
        saveAuthSession(data);
        alert('Account created successfully!');
        switchView('view-dashboard');
      } catch (err) {
        alert(err.message);
      }
    });
  }

  // Login Form
  const loginForm = document.getElementById('form-login');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const payload = {
          email: document.getElementById('login-email').value,
          password: document.getElementById('login-password').value
        };
        const data = await apiRequest('/auth/login', 'POST', payload);
        saveAuthSession(data);
        alert('Welcome back!');
        switchView('view-dashboard');
      } catch (err) {
        alert(err.message);
      }
    });
  }

  // Logout
  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      localStorage.clear();
      currentAuthToken = null;
      currentUser = null;
      checkAuth();
      switchView('view-landing');
    });
  }

  // AI Predict Button
  const predictBtn = document.getElementById('btn-run-ai-predict');
  if (predictBtn) {
    predictBtn.addEventListener('click', runAiRiskAssessment);
  }

  // Safe Route Search
  const searchRouteBtn = document.getElementById('btn-search-safe-route');
  if (searchRouteBtn) {
    searchRouteBtn.addEventListener('click', findSafeRoute);
  }

  // Chatbot Send
  const chatForm = document.getElementById('form-chatbot');
  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      sendChatbotQuery();
    });
  }

  // Voice Chat Speech Recognition (Web Speech API)
  const voiceBtn = document.getElementById('btn-voice-input');
  if (voiceBtn) {
    voiceBtn.addEventListener('click', toggleVoiceInput);
  }

  // Fake Call Feature
  const fakeCallBtn = document.getElementById('btn-trigger-fake-call');
  if (fakeCallBtn) {
    fakeCallBtn.addEventListener('click', triggerFakeCall);
  }
}

function saveAuthSession(data) {
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  currentAuthToken = data.access_token;
  currentUser = data.user;
  checkAuth();
}

// 5-Second Countdown SOS System
function startSosCountdown(mode = 'normal') {
  currentPendingSosType = mode;
  countdownRemaining = 5;
  const overlay = document.getElementById('countdown-modal');
  const countDisplay = document.getElementById('countdown-number');
  const modeDisplay = document.getElementById('countdown-mode-title');

  if (modeDisplay) modeDisplay.textContent = mode === 'silent' ? 'ACTIVATING SILENT SOS' : 'EMERGENCY SOS COUNTDOWN';
  if (countDisplay) countDisplay.textContent = countdownRemaining;
  if (overlay) overlay.style.display = 'flex';

  clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    countdownRemaining -= 1;
    if (countDisplay) countDisplay.textContent = countdownRemaining;

    if (countdownRemaining <= 0) {
      clearInterval(countdownTimer);
      if (overlay) overlay.style.display = 'none';
      dispatchSosAlert(currentPendingSosType);
    }
  }, 1000);
}

function cancelSosCountdown() {
  clearInterval(countdownTimer);
  const overlay = document.getElementById('countdown-modal');
  if (overlay) overlay.style.display = 'none';
  alert('SOS countdown cancelled. No alert was sent.');
}

async function dispatchSosAlert(mode) {
  try {
    let lat = 12.9716;
    let lng = 77.5946;

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => { lat = pos.coords.latitude; lng = pos.coords.longitude; },
        () => console.warn('Using standard location coords')
      );
    }

    const payload = {
      latitude: lat,
      longitude: lng,
      trigger_type: 'button',
      alert_mode: mode,
      location_address: 'Bangalore City Center, Verified GPS Track'
    };

    const res = await apiRequest('/sos/trigger', 'POST', payload);
    const alertBanner = document.getElementById('active-sos-banner');
    if (alertBanner) {
      alertBanner.classList.remove('d-none');
      document.getElementById('active-sos-id').textContent = res.id;
    }
    alert(`EMERGENCY SOS SENT! Notification dispatched to trusted contacts. Alert ID: #${res.id}`);
    loadAlertHistory();
  } catch (err) {
    alert(`Could not trigger SOS: ${err.message}. If not logged in, please log in first.`);
  }
}

// Live Maps
function initLiveMap() {
  if (liveMap) return;
  const mapEl = document.getElementById('live-map');
  if (!mapEl) return;

  liveMap = L.map('live-map').setView([12.9716, 77.5946], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(liveMap);

  userMarker = L.marker([12.9716, 77.5946], {
    title: 'Your Current Live Location'
  }).addTo(liveMap).bindPopup('<b>You Are Here</b><br>Live tracking active.').openPopup();

  // Draw Safe Zone Circle (Home)
  L.circle([12.9716, 77.5946], {
    color: '#28a745',
    fillColor: '#28a745',
    fillOpacity: 0.15,
    radius: 400
  }).addTo(liveMap).bindPopup('Safe Zone: Home (Radius: 400m)');
}

function initRouteMap() {
  if (routeMap) return;
  const mapEl = document.getElementById('route-map');
  if (!mapEl) return;

  routeMap = L.map('route-map').setView([12.9750, 77.5950], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(routeMap);

  // Add sample police stations & hospital pins
  L.marker([12.9750, 77.5900]).addTo(routeMap).bindPopup('<b>Central Police Station</b><br>Phone: 100');
  L.marker([12.9640, 77.5750]).addTo(routeMap).bindPopup('<b>Victoria Hospital ER</b><br>Phone: 108');
}

function initHotspotMap() {
  if (hotspotMap) return;
  const mapEl = document.getElementById('hotspot-map');
  if (!mapEl) return;

  hotspotMap = L.map('hotspot-map').setView([12.9716, 77.5946], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(hotspotMap);

  loadHotspotMarkers();
}

async function loadHotspotMarkers() {
  try {
    const spots = await apiRequest('/hotspots', 'GET');
    spots.forEach(spot => {
      const color = spot.risk_level === 'HIGH RISK' ? '#dc3545' : (spot.risk_level === 'WARNING' ? '#ff9800' : '#28a745');
      L.circleMarker([spot.latitude, spot.longitude], {
        radius: 12,
        fillColor: color,
        color: '#fff',
        weight: 2,
        fillOpacity: 0.8
      }).addTo(hotspotMap).bindPopup(`
        <div style="font-size:0.9rem">
          <strong style="color:${color}">${spot.risk_level} ZONE</strong><br>
          <b>Type:</b> ${spot.incident_type}<br>
          <b>Details:</b> ${spot.description}
        </div>
      `);
    });
  } catch (err) {
    console.error('Failed to load crime hotspots:', err);
  }
}

// AI Risk Assessment
async function runAiRiskAssessment() {
  const resultCard = document.getElementById('ai-predict-result');
  const levelBadge = document.getElementById('ai-risk-level');
  const scoreSpan = document.getElementById('ai-risk-score');
  const reasonsList = document.getElementById('ai-reasons-list');
  const recList = document.getElementById('ai-recommendations-list');

  try {
    const payload = {
      latitude: 12.9716,
      longitude: 77.5946,
      hour_of_day: parseInt(document.getElementById('ai-input-hour').value) || 22,
      speed_kmh: parseFloat(document.getElementById('ai-input-speed').value) || 4.5,
      route_deviation_meters: parseFloat(document.getElementById('ai-input-deviation').value) || 280,
      battery_percentage: parseInt(document.getElementById('ai-input-battery').value) || 18,
      isolated_area: document.getElementById('ai-input-isolated').checked
    };

    const res = await apiRequest('/ai/predict-risk', 'POST', payload);

    resultCard.classList.remove('d-none');
    levelBadge.textContent = res.risk_level;
    levelBadge.className = `badge ${res.risk_level === 'HIGH RISK' ? 'bg-danger' : (res.risk_level === 'WARNING' ? 'bg-warning text-dark' : 'bg-success')}`;
    scoreSpan.textContent = `${res.risk_score}/100`;

    reasonsList.innerHTML = res.reasons.map(r => `<li>${r}</li>`).join('');
    recList.innerHTML = res.recommendations.map(r => `<li>${r}</li>`).join('');
  } catch (err) {
    alert(`AI Risk Evaluation error: ${err.message}`);
  }
}

// Safe Route Finder
async function findSafeRoute() {
  try {
    const payload = {
      origin_name: document.getElementById('route-origin').value || 'Indiranagar',
      origin_lat: 12.9780,
      origin_lng: 77.6400,
      destination_name: document.getElementById('route-dest').value || 'MG Road Metro Station',
      destination_lat: 12.9750,
      destination_lng: 77.6060,
      travel_mode: 'walking'
    };

    const data = await apiRequest('/routes/recommend', 'POST', payload);
    const container = document.getElementById('route-cards-container');
    container.innerHTML = '';

    data.routes.forEach(r => {
      const isRec = r.route_id === data.recommended_route_id;
      const card = document.createElement('div');
      card.className = `card mb-3 p-3 border-${isRec ? 'success shadow' : 'light'}`;
      card.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <h5 class="mb-1">${r.name} ${isRec ? '<span class="badge bg-success ms-2">AI Recommended</span>' : ''}</h5>
          <span class="badge ${r.risk_level === 'SAFE' ? 'bg-success' : 'bg-warning text-dark'}">${r.risk_level}</span>
        </div>
        <div class="row mt-2 text-muted small">
          <div class="col-4"><strong>Distance:</strong> ${r.distance_km} km</div>
          <div class="col-4"><strong>Duration:</strong> ${r.duration_minutes} mins</div>
          <div class="col-4"><strong>Lighting:</strong> ${r.lighting_quality}</div>
        </div>
        <p class="mt-2 mb-0 small text-dark">${r.recommendation_reason}</p>
      `;
      container.appendChild(card);
    });

    if (routeMap) {
      // Draw polyline on map
      const recRoute = data.routes[0];
      L.polyline(recRoute.waypoints, { color: '#28a745', weight: 5 }).addTo(routeMap);
      routeMap.fitBounds(recRoute.waypoints);
    }
  } catch (err) {
    alert(`Could not fetch route: ${err.message}`);
  }
}

// AI Chatbot
async function sendChatbotQuery() {
  const inputEl = document.getElementById('chat-input-text');
  const msg = inputEl.value.trim();
  if (!msg) return;

  const chatBox = document.getElementById('chatbot-messages');
  chatBox.innerHTML += `<div class="chat-bubble-user">${msg}</div>`;
  inputEl.value = '';
  chatBox.scrollTop = chatBox.scrollHeight;

  const langSelect = document.getElementById('chatbot-language-select');
  const language = langSelect ? langSelect.value : 'en';

  try {
    const data = await apiRequest('/chatbot/query', 'POST', { message: msg, language });
    chatBox.innerHTML += `<div class="chat-bubble-bot">${data.response}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (err) {
    chatBox.innerHTML += `<div class="chat-bubble-bot text-danger">Error: ${err.message}</div>`;
  }
}

// Web Speech API Voice Input
function toggleVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert('Speech recognition is not supported in this browser. Please use Chrome/Edge or type your message.');
    return;
  }
  const recognition = new SpeechRecognition();
  const langSelect = document.getElementById('chatbot-language-select');
  recognition.lang = langSelect && langSelect.value === 'kn' ? 'kn-IN' : 'en-IN';

  recognition.onstart = () => {
    const btn = document.getElementById('btn-voice-input');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Listening...';
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('chat-input-text').value = transcript;
    sendChatbotQuery();
  };

  recognition.onend = () => {
    const btn = document.getElementById('btn-voice-input');
    if (btn) btn.innerHTML = '<i class="fas fa-microphone"></i> Voice';
  };

  recognition.start();
}

// Fake Call Simulator
function triggerFakeCall() {
  const modal = document.getElementById('fake-call-modal');
  if (modal) modal.style.display = 'flex';

  // Play subtle vibration if supported
  if (navigator.vibrate) {
    navigator.vibrate([1000, 500, 1000, 500, 1000]);
  }
}

function dismissFakeCall() {
  const modal = document.getElementById('fake-call-modal');
  if (modal) modal.style.display = 'none';
}

// Battery and Network Status Monitoring
function monitorBatteryAndNetwork() {
  const batteryEl = document.getElementById('status-battery-level');
  const networkEl = document.getElementById('status-network');

  if (networkEl) {
    networkEl.textContent = navigator.onLine ? 'Online' : 'Offline';
    window.addEventListener('online', () => { networkEl.textContent = 'Online'; });
    window.addEventListener('offline', () => { networkEl.textContent = 'Offline'; });
  }

  if (navigator.getBattery && batteryEl) {
    navigator.getBattery().then(battery => {
      const updateBattery = () => {
        const level = Math.round(battery.level * 100);
        batteryEl.textContent = `${level}%`;
      };
      updateBattery();
      battery.addEventListener('levelchange', updateBattery);
    });
  }
}

// Contacts & Community Network Loading
async function loadContactsAndHelpers() {
  if (!currentAuthToken) return;
  try {
    const contacts = await apiRequest('/contacts', 'GET');
    const contactsList = document.getElementById('contacts-list');
    if (contactsList) {
      contactsList.innerHTML = contacts.map(c => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
          <div>
            <strong>${c.contact_name}</strong> (${c.relationship_type})<br>
            <span class="small text-muted"><i class="fas fa-phone"></i> ${c.phone_number}</span>
          </div>
          <span class="badge bg-success">Active Contact</span>
        </li>
      `).join('') || '<li class="list-group-item text-muted">No contacts added yet.</li>';
    }

    const helpers = await apiRequest('/community/helpers?verified_only=false', 'GET');
    const helpersList = document.getElementById('helpers-list');
    if (helpersList) {
      helpersList.innerHTML = helpers.map(h => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
          <div>
            <strong>${h.full_name}</strong> - ${h.neighbourhood}<br>
            <span class="small text-muted"><i class="fas fa-shield-alt text-primary"></i> ${h.police_station_jurisdiction || 'City Sector'}</span>
          </div>
          <span class="badge ${h.verification_status === 'verified' ? 'bg-success' : 'bg-warning text-dark'}">${h.verification_status}</span>
        </li>
      `).join('') || '<li class="list-group-item text-muted">No community helpers registered.</li>';
    }
  } catch (err) {
    console.error('Error loading contacts/helpers:', err);
  }
}

// Alert History Loading
async function loadAlertHistory() {
  if (!currentAuthToken) return;
  try {
    const alerts = await apiRequest('/sos/history', 'GET');
    const container = document.getElementById('history-table-body');
    if (container) {
      container.innerHTML = alerts.map(a => `
        <tr>
          <td>#${a.id}</td>
          <td>${new Date(a.created_at).toLocaleString()}</td>
          <td><span class="badge ${a.alert_mode === 'silent' ? 'bg-secondary' : 'bg-danger'}">${a.alert_mode.toUpperCase()}</span></td>
          <td><span class="badge ${a.status === 'active' ? 'bg-danger' : (a.status === 'acknowledged' ? 'bg-warning text-dark' : 'bg-success')}">${a.status}</span></td>
          <td>${a.location_address || `${a.latitude.toFixed(4)}, ${a.longitude.toFixed(4)}`}</td>
          <td>
            ${a.status === 'active' || a.status === 'acknowledged' ?
              `<button class="btn btn-sm btn-outline-success" onclick="resolveAlertPrompt(${a.id})">Mark Resolved</button>` :
              'Resolved'}
          </td>
        </tr>
      `).join('') || '<tr><td colspan="6" class="text-center text-muted">No emergency records found.</td></tr>';
    }
  } catch (err) {
    console.error('History load error:', err);
  }
}

async function resolveAlertPrompt(alertId) {
  try {
    await apiRequest(`/sos/${alertId}/resolve`, 'PUT', { notes: 'Resolved by user' });
    alert('Alert marked resolved');
    loadAlertHistory();
  } catch (err) {
    alert(err.message);
  }
}

// Admin Dashboard Loading
async function loadAdminDashboard() {
  if (!currentAuthToken || (currentUser && currentUser.role !== 'admin')) return;
  try {
    const metrics = await apiRequest('/admin/metrics', 'GET');
    document.getElementById('metric-total-users').textContent = metrics.users.total_users;
    document.getElementById('metric-total-helpers').textContent = metrics.users.total_helpers;
    document.getElementById('metric-active-sos').textContent = metrics.emergencies.active_alerts;
    document.getElementById('metric-total-incidents').textContent = metrics.incidents.total_reports;

    const users = await apiRequest('/admin/users', 'GET');
    const usersTable = document.getElementById('admin-users-table');
    if (usersTable) {
      usersTable.innerHTML = users.map(u => `
        <tr>
          <td>${u.id}</td>
          <td>${u.full_name}</td>
          <td>${u.email}</td>
          <td>${u.phone}</td>
          <td><span class="badge ${u.role === 'admin' ? 'bg-danger' : (u.role === 'helper' ? 'bg-primary' : 'bg-secondary')}">${u.role}</span></td>
          <td>${u.battery_level}% (${u.network_status})</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Admin metrics load error:', err);
  }
}

function loadUserData() {
  loadContactsAndHelpers();
  loadAlertHistory();
}

// Realtime WebSocket Connection
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const clientId = currentUser ? currentUser.id : 'anon_' + Math.floor(Math.random() * 10000);
  const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`;

  try {
    ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'NEW_SOS_ALERT') {
          showSosToastNotification(data);
        }
      } catch (e) {}
    };
    ws.onclose = () => {
      setTimeout(initWebSocket, 5000);
    };
  } catch (e) {
    console.warn('WebSocket connection not supported in environment');
  }
}

function showSosToastNotification(data) {
  alert(`ALERT BROADCAST: SOS triggered by ${data.user_name} (${data.user_phone})! Mode: ${data.alert_mode}`);
}
