// #region *** DOM references                           ***********
let currentInsideScreen = 'home';
let selectedIndex = 0;
let modalFocusIndex = 0;
let settingsWS = null;
let focusIndex = -1;
let snoozeInterval = null
// helpertje
async function refreshAll() {
  refreshInsideSettingsScreen();
  refreshWeather();
  initName();
  updateClock();
  loadAlarms();
  loadDashboard();
  loadLogs();
}

function getFocusableElements() {
  const modals = document.querySelectorAll('.modal-overlay');

  if (modals.length) {
    const modal = modals[modals.length - 1];
    return modal.querySelectorAll('button,input,.difficulty-option,.day-sphere,.network-row');
  }

  switch (currentInsideScreen) {
    case 'alarms': return document.querySelectorAll('#alarms-screen button');
    case 'settings': return document.querySelectorAll('#settings-screen button');
    default: return [];
  }
}

// #endregion

// #region *** Callback-Visualisation - show___         ***********
async function loadLogs() {
  const response = await fetch('/api/v1/logs/');
  const data = await response.json();

  const container = document.getElementById('system-logs');
  if (!container) return;

  container.innerHTML = '';

  data.logs.forEach(log => {
    container.insertAdjacentHTML('beforeend', `
      <div class="log-entry">
        ${log.source} | ${log.message}
      </div>
    `);
  });
}

async function refreshWeather() {
  let networkConfig = {};
  let weatherConfig = {};

  const weatherCard = document.querySelector(".weather");
  const weatherCity = document.getElementById("weather-city");
  const weatherWind = document.getElementById("weather-wind");
  const weatherCode = document.getElementById("weather-code");
  const weatherTemp = document.getElementById("weather-temp");

  if (!weatherCard && !weatherCity && !weatherWind && !weatherCode && !weatherTemp) {
    return;
  }

  try {
    const response = await fetch("/api/v1/settings/network");
    networkConfig = await response.json();
  } catch (error) {
    console.error(error);
    return;
  }

  if (networkConfig.network_mode === "ap") {
    if (weatherCard) {
      weatherCard.innerHTML = `
        <span>
          could not load
        </span>
        <span>
          network disabled
        </span>
      `;
    }

    if (weatherCity) weatherCity.textContent = "network disabled";
    if (weatherWind) weatherWind.textContent = "-";
    if (weatherCode) weatherCode.textContent = "-";
    if (weatherTemp) weatherTemp.textContent = "-";

    return;
  }

  try {
    const response = await fetch("/api/v1/settings/weather");
    weatherConfig = await response.json();
  } catch (error) {
    console.error(error);
    return;
  }

  if (weatherConfig.weather !== "on") {
    if (weatherCard) {
      weatherCard.style.display = "none";
    }

    if (weatherCity) weatherCity.textContent = "-";
    if (weatherWind) weatherWind.textContent = "-";
    if (weatherCode) weatherCode.textContent = "-";
    if (weatherTemp) weatherTemp.textContent = "-";

    return;
  }

  if (weatherCard) {
    weatherCard.style.display = "";
  }

  let weatherDetails = {};

  try {
    const response = await fetch("/api/v1/settings/weather-details");
    weatherDetails = await response.json();
  } catch (error) {
    console.error(error);
    return;
  }

  const location = weatherDetails.weather_details;

  try {
    const geoResponse = await fetch(
      `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(location)}&count=1`
    );
    const geoData = await geoResponse.json();

    if (!geoData.results?.length) return;

    const { latitude, longitude } = geoData.results[0];

    const weatherResponse = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,weather_code,wind_speed_10m`
    );
    const weatherData = await weatherResponse.json();

    const city = geoData.results[0];

    const weatherCodes = {
      0: "Clear",
      1: "Mainly clear",
      2: "Partly cloudy",
      3: "Overcast",
      45: "Fog",
      48: "Depositing rime fog",
      51: "Light drizzle",
      53: "Moderate drizzle",
      55: "Dense drizzle",
      61: "Light rain",
      63: "Moderate rain",
      65: "Heavy rain",
      71: "Light snow",
      73: "Moderate snow",
      75: "Heavy snow",
      95: "Thunderstorm"
    };

    const wind = `${weatherData.current.wind_speed_10m} km/h`;
    const code = weatherCodes[weatherData.current.weather_code] ?? "Unknown";
    const temp = `${weatherData.current.temperature_2m}°C`;

    if (weatherCard) {
      weatherCard.innerHTML = `
        <span id="wind">
          ${wind}
        </span><br>
        <span id="weather-icon">
          ${code} · ${temp}
        </span><br>
        <span id="location-info">
          ${city.name}
        </span>
      `;
    }

    if (weatherCity) weatherCity.textContent = city.name;
    if (weatherWind) weatherWind.textContent = wind;
    if (weatherCode) weatherCode.textContent = code;
    if (weatherTemp) weatherTemp.textContent = temp;

  } catch (error) {
    console.error(error);
  }
}

// Dashboard card populator (outside frontend)
async function loadDashboard() {
    if (!document.querySelector('.stats')) {
        return;
    }
    try {
        const response = await fetch("/api/v1/alarms/dashboard");
        const data = await response.json();
        console.log(data);
        document.getElementById("next-alarm").textContent = data.next_alarm.timestamp ?? "--:--";
        document.getElementById("average-tries").textContent =Number(data.average_tries ?? 0).toFixed(1);
        document.getElementById("average-solve-time").textContent = `${Math.round(data.average_solve_time ?? 0)}s`;
        document.getElementById("first-try-percent").textContent = `${Math.round(data.first_try_percentage ?? 0)}%`;
        function renderAnswers(answerString) {
            return answerString
                .split("|")
                .map(entry => {
                    const [answer, correct] = entry.split(":");
                    return `<span style="color:${correct === "1" ? "green" : "red"};font-weight:600">${answer}</span>`;
                })
                .join(" ");
        }
        const historyBody = document.getElementById("history-body");
        historyBody.innerHTML = "";

        for (const row of data.history) {
            historyBody.innerHTML += `
              <tr>
                  <td>${row.triggered_at}</td>
                  <td>${row.difficultyName}</td>
                  <td>${row.mathQuery}</td>
                  <td>${renderAnswers(row.answers || "")}</td>
                  <td>${row.time_to_complete ?? 0}s</td>
              </tr>
              `;
        }
    } catch (error) {
        console.error("Failed loading dashboard:", error);
    }
}

// Makes correct screen visible (inside frontend)
function showScreen(screen) {
  currentInsideScreen = screen;
  focusIndex = -1;
  document.querySelectorAll('.alarm-action-button').forEach(btn => btn.classList.remove('selected'));
  document.querySelectorAll('.screen').forEach(el => el.classList.remove('screen-visible'));
  const target = document.getElementById(`${screen}-screen`);
  if (target) {
    target.classList.add('screen-visible');
    if (screen === 'settings' ) {
      refreshInsideSettingsScreen();
    }
  }
}

// Sets nav svg to active for screen
function setActiveNav(screen) {
  document.querySelector('.nav-home')?.classList.remove('active');
  document.querySelector('.nav-alarms')?.classList.remove('active');
  document.querySelector('.nav-settings')?.classList.remove('active');
  document.querySelector(`.nav-${screen}`)?.classList.add('active');
}

// Refresh settings (inside frontend)
async function refreshInsideSettingsScreen() {
  const networkSummary = document.getElementById('inside-network-summary');
  const timeSummary = document.getElementById('inside-time-summary-value');
  const weatherSummary = document.getElementById('inside-weather-value');
  const networkButton = document.getElementById('inside-network-settings');
  const timeButton = document.getElementById('inside-time-settings');
  const weatherButton = document.getElementById('inside-weather-settings');
  const powerOffButton = document.getElementById('inside-poweroff');
  const rebootButton = document.getElementById('inside-reboot');

  if (timeButton) timeButton.onclick = openTimeSettings;
  if (networkButton) networkButton.onclick = openInsideNetworkSettings;
  if (weatherButton) weatherButton.onclick = openWeatherSettings;
  if (powerOffButton) powerOffButton.onclick = PowerOffDevice;
  if (rebootButton) rebootButton.onclick = rebootDevice;
  if (networkSummary) {
    try {
      const response = await fetch('/api/v1/settings/network');
      const data = await response.json();
      if (data.network_mode === 'ap') {
        networkSummary.innerHTML = `SSID: CogniWake<br>Password: c0gn!wake<br>IP: ${data.ip_address}`;
      } else {
        networkSummary.innerHTML = `SSID: ${data.connected_ssid || 'Not Connected'}<br>IP: ${data.ip_address}`;
      }
    } catch {
      networkSummary.textContent = 'Unavailable';
    }
  }

  if (timeSummary) {
    try {
      const response = await fetch('/api/v1/settings/time');
      const data = await response.json();
      timeSummary.textContent = (data.time_mode === 'ntp' || data.time_mode === 'network') ? 'Network Time' : 'Manual Time';
    } catch {
      timeSummary.textContent = 'Unavailable';
    }
  }
  if (weatherSummary) {
    try {
      const response = await fetch('/api/v1/settings/weather');
      const data = await response.json();
      weatherSummary.textContent = (data.weather === 'on') ? 'Enabled' : 'Disabled';
    } catch (error) {
      weatherSummary.textContent = error;
    }
  }
}
// Clock update function
async function updateClock() {
  const clock = document.getElementById('clock');
  if (!clock) return;
  try {
    const response = await fetch(`/api/v1/settings/system-time`);
    const data = await response.json();
    clock.textContent = data.time;
  } catch (error) {console.error("Clock error: ", error);}
}

// Modal creation helper function
function createModal(title) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title">${title}</div>
        <button class="modal-close">✕</button>
        </div>
        <div class="modal-body">
      </div>
    </div>
    `;
  document.body.appendChild(overlay);
  return overlay;
}

// Sensor status modal
function createSensorStatus(modal) {
  const body = modal.querySelector('.modal-body');
  const statusBox = document.createElement('div');
  statusBox.className = 'sensor-status inactive';
  body.appendChild(statusBox);
  return statusBox;
}

// update sensor status modal...
function updateSensorStatus(statusBox, state) {
  statusBox.textContent = state;
  const activeStates = ['LIFTED', 'MOTION', 'ACTIVE'];
  if (activeStates.includes(state)) {
    statusBox.classList.remove('inactive');
    statusBox.classList.add('active');
  } else {
    statusBox.classList.remove('active');
    statusBox.classList.add('inactive');
  }
}

// Virtual keypad modal mapped to phyiscalkeypad
function createKeypad(modal) {
  const body = modal.querySelector('.modal-body');
  const keypad = document.createElement('div');
  keypad.className = 'virtual-keypad';
  const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];
  keys.forEach((key) => {
    const button = document.createElement('div');
    button.className = 'virtual-key';
    button.dataset.key = key;
    button.textContent = key;
    keypad.appendChild(button);
  });
  body.appendChild(keypad);
  return keypad;
}

// function to set keystates
function setKeyState(keypad, key, pressed) {
  const button = keypad.querySelector(`[data-key="${key}"]`);
  if (!button) return;
  if (pressed) button.classList.add('active');
  else button.classList.remove('active');
}
// #endregion

// #region *** Callback-No Visualisation - callback___  ***********
// Listens for alarrm triggers
function startLiveAlarmListener() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/alarms/live`);
  ws.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.event === 'alarm_triggered') {
        const response = await fetch(`/api/v1/alarms/math-query/${data.alarmID}`);
        const query = await response.json();
        showAlarmQueryModal(data.alarmID, query.question);
      } else if (data.event === 'alarm_snoozed') {
        showSnoozeCountdown(data.alarmID, data.snooze_until);
      } else if (data.event == 'reload') {
        loadAlarms();
      }
    } catch (err) { console.error(err); }
  };
  ws.onclose = () => {
    setTimeout(startLiveAlarmListener, 2000);
  };
}
async function clearHistory() {
  const modal = createModal('Confirm');
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <p>
      Are you sure you want to clear all math history?
    </p>
    <button id="confirm-action">
      Confirm
    </button>
  `;

  body.querySelector('#confirm-action').addEventListener('click', async () => {
    try {
    await fetch('/api/v1/settings/clear-history', {
      method: 'POST'
    });
  } catch (error) {
    console.error(error);
  }
    modal.remove();
  });

  modal.querySelector('.modal-close').addEventListener('click', () => {
    modal.remove();
  });
}
async function clearAlarms() {
  const modal = createModal('Confirm');
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <p>
      Are you sure you want to clear all alarms?
    </p>
    <button id="confirm-action">
      Confirm
    </button>
  `;

  body.querySelector('#confirm-action').addEventListener('click', async () => {
    try {
    await fetch('/api/v1/settings/clear-alarms', {
      method: 'POST'
    });
  } catch (error) {
    console.error(error);
  }
    modal.remove();
  });
  modal.querySelector('.modal-close').addEventListener('click', () => {
    modal.remove();
  });
}

async function clearLogs() {
  const modal = createModal('Confirm');
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <p>
      Are you sure you want to clear all logs?
    </p>
    <button id="confirm-action">
      Confirm
    </button>
  `;

  body.querySelector('#confirm-action').addEventListener('click', async () => {
    try {
    await fetch('/api/v1/settings/clear-logs', {
      method: 'POST'
    });
  } catch (error) {
    console.error(error);
  }
    modal.remove();
  });
  modal.querySelector('.modal-close').addEventListener('click', () => {
    modal.remove();
  });
}

async function rebootDevice() {
  const modal = createModal('Confirm');
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <p>
      Are you sure you want to reboot the device?
    </p>
    <button id="confirm-action">
      Confirm
    </button>
  `;

  body.querySelector('#confirm-action').addEventListener('click', async () => {
    try {
    await fetch('/api/v1/settings/reboot', {
      method: 'POST'
    });
  } catch (error) {
    console.error(error);
  }
    modal.remove();
  });
  modal.querySelector('.modal-close').addEventListener('click', () => {
    modal.remove();
  });
}

async function PowerOffDevice() {
  const modal = createModal('Confirm');
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <p>
      Are you sure you want to power off?
    </p>
    <button id="confirm-action">
      Confirm
    </button>
  `;

  body.querySelector('#confirm-action').addEventListener('click', async () => {
    try {
    await fetch('/api/v1/settings/poweroff', {
      method: 'POST'
    });
  } catch (error) {
    console.error(error);
  }
    modal.remove();
  });
  modal.querySelector('.modal-close').addEventListener('click', () => {
    modal.remove();
  });
}
// Snooze countdown
function showSnoozeCountdown(alarmID, snoozeUntil) {
  const container = document.querySelector('.alarm-query-container');
  if (!container) return;

  container.innerHTML = `
    <h3 style="color:var(--accent);margin-bottom:16px;">
      Alarm Snoozed
    </h3>
    <div id="snooze-countdown" style="font-size:2.5rem;font-weight:bold;">
    </div>
  `;
  const countdown = document.getElementById('snooze-countdown');
  const updateCountdown = () => {
    const remaining = Math.max(0, Math.floor((new Date(snoozeUntil) - new Date()) / 1000));
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;

    countdown.textContent =
      `${minutes}:${seconds.toString().padStart(2, '0')}`;

    if (remaining <= 0) {
      clearInterval(interval);
      const modal = container.closest('.modal-overlay');
      if (modal) { modal.remove(); }
      return;
    }
  };

  updateCountdown();
  const interval = setInterval(updateCountdown, 1000);
}
// Shows the math query
function showAlarmQueryModal(alarmID, questionText) {
  if (document.getElementById('query-user-input')) return;

  const modal = createModal('Challenge');
  const body = modal.querySelector('.modal-body');

  const closeBtn = modal.querySelector('.modal-close');
  if (closeBtn) closeBtn.remove();

  body.innerHTML = `
    <div class="alarm-query-container" style="text-align: center; padding: 10px;">
      <h3 style="color: var(--accent); margin-bottom: 16px;">Solve to Deactivate</h3>
      <div id="query-equation-display" style="font-size: 2.5rem; font-weight: bold; margin-bottom: 20px;">
        ${questionText}
      </div>
      <input id="query-user-input" type="text" placeholder="Enter Answer" style="text-align: center; font-size: 1.5rem; width: 100%; margin-bottom: 16px;">
      <button id="query-submit-button" style="width: 100%;">
        Submit Answer
      </button>
      <div id="query-error-feedback" style="color: #ef4444; margin-top: 12px; min-height: 20px; font-weight: 600;"></div>
    </div>
  `;
  focusIndex = -1;
  setTimeout(() => focusNext(), 0);

  body.querySelector('#query-submit-button').addEventListener('click', async () => {
    const inputField = body.querySelector('#query-user-input');
    const feedback = body.querySelector('#query-error-feedback');
    const submitBtn = body.querySelector('#query-submit-button');
    const value = parseInt(inputField.value.trim());
    if (isNaN(value)) return;
    submitBtn.disabled = true;
    try {
      const response = await fetch('/api/v1/alarms/verify-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        alarmID: parseInt(alarmID),
        user_answer: value
      })
    });
      const data = await response.json();
      if (data.success) {
        modal.remove();
      } else {
        inputField.value = '';
        feedback.textContent = 'Incorrect.';
        submitBtn.disabled = false;
        focusIndex = -1;
        focusNext();
      }
    } catch (error) {
      console.error(error);
      submitBtn.disabled = false;
    }
  });
}
// inside network settings modal
async function openInsideNetworkSettings() {
  const modal = createModal('Network Settings');
  const body = modal.querySelector('.modal-body');
  const response = await fetch('/api/v1/settings/network');
  const data = await response.json();
  body.innerHTML = `
    <div class="settings-item">
      <label>Use Network</label>
      <input type="checkbox" id="network-mode" ${data.network_mode === 'wifi' ? 'checked' : ''}>
    </div>
    <div class="settings-item">
      <label>Use Access Point</label>
      <input type="checkbox" id="ap-mode" ${data.network_mode === 'ap' ? 'checked' : ''}>
    </div>
    <button id="save-network">
      Save
    </button>
  `;
  const networkMode = body.querySelector('#network-mode');
  const apMode = body.querySelector('#ap-mode');

  networkMode.addEventListener('change', () => {
    if (networkMode.checked) apMode.checked = false;
  });

  apMode.addEventListener('change', () => {
    if (apMode.checked) networkMode.checked = false;
  });

  body.querySelector('#save-network').addEventListener('click', async () => {
    try {
      await fetch('/api/v1/settings/network/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          network_mode: networkMode.checked ? 'wifi' : 'ap'
        })
      });

      modal.remove();
      refreshInsideSettingsScreen();
    } catch (error) {
      console.error(error);
    }
  });

  modal.querySelector('.modal-close').addEventListener('click', () => {
    modal.remove();
  });
}
// Network settings modal
async function openNetworkSettings() {
  const modal = createModal('Network Settings');
  const body = modal.querySelector('.modal-body');
  let data = {};
  try {
    const response = await fetch(`/api/v1/settings/network`);
    data = await response.json();
  } catch (error) { console.error(error); return; }
  const networks = Array.isArray(data.networks) ? data.networks : [];
  body.innerHTML = `
  <div style="background:#1e293b;padding:16px;border-radius:12px;margin-bottom:16px;">
    <div>
      Current Connection
    </div>
    <div style="margin-top:8px;font-weight:600;" id="current-connection">
      ${data.connected_ssid || 'Not Connected'}
    </div>
  </div>
  <div style="background:#1e293b;padding:16px;border-radius:12px;margin-bottom:16px;">
    <div>
      Device IP
    </div>
    <strong>${data.ip_address}</strong>
  </div>
  <div class="settings-item">
    <label>
      <input type="checkbox" id="network-mode" ${data.network_mode === 'wifi' ? 'checked' : ''}>
      Use Network
    </label>
  </div>
  <div id="wifi-section" style="margin-top:12px;display:${data.network_mode === 'wifi' ? 'block' : 'none'};">
    <button id="refresh-networks" style="width:100%;margin-bottom:12px;">
      Refresh Networks
    </button>
    <div id="network-warning" style="font-size:0.85rem;opacity:0.8;margin-bottom:12px;">
      Refreshing will temporarily interrupt the AP.
    </div>
    <div class="network-list" id="network-list">
      ${networks.map((network) => `
        <div class="network-row" data-ssid="${network.ssid}" data-known="${network.known ? '1' : '0'}">
          <div class="network-row-left">
            <div class="network-row-ssid">
              ${network.ssid}
            </div>
            <div class="network-row-meta">
              <span>${network.signal}%</span>
            </div>
          </div>
          <div class="network-badge ${network.known ? 'known' : 'unknown'}">
            ${network.known ? 'Known' : 'Unknown'}
          </div>
        </div>
      `).join('')}
    </div>
    <div class="network-detail" id="network-detail" style="display:none;">
      <div class="network-detail-title" id="selected-network-name"></div>
      <div id="selected-network-state"></div>
      <input class="network-password" id="wifi-password" type="password" placeholder="Password">
      <div class="network-actions">
        <button id="connect-network">
          Connect
        </button>
      </div>
    </div>
  </div>
  <div class="settings-item" style="margin-top:20px;">
    <label>
      <input type="checkbox" id="ap-mode" ${data.network_mode === 'ap' ? 'checked' : ''}>
      Use Access Point
    </label>
  </div>
  <div style="background:#1e293b;padding:16px;border-radius:12px;">
    <div>
      SSID: <strong>CogniWake</strong>
    </div>
    <div>
      Password: <strong>c0gn!wake</strong>
    </div>
  </div>

  <div class="network-actions">
    <button id="save-network">
      Save
    </button>
  </div>
  `;
  const networkCheckbox = body.querySelector('#network-mode');
  const apCheckbox = body.querySelector('#ap-mode');
  const wifiSection = body.querySelector('#wifi-section');
  const networkList = body.querySelector('#network-list');
  const networkDetail = body.querySelector('#network-detail');
  const selectedName = body.querySelector('#selected-network-name');
  const selectedState = body.querySelector('#selected-network-state');
  const wifiPassword = body.querySelector('#wifi-password');
  const connectNetworkButton = body.querySelector('#connect-network');
  const saveNetworkButton = body.querySelector('#save-network');
  const refreshNetworksButton = body.querySelector('#refresh-networks');
  let selectedNetwork = null;
  let networkScanPending = false;
  function clearSelectionStyles() { body.querySelectorAll('.network-row').forEach((row) => row.classList.remove('selected')); }
  function showNetworkDetail(network) {
    selectedNetwork = network;
    networkDetail.style.display = 'block';
    selectedName.textContent = network.ssid;
    selectedState.innerHTML = network.known ? '<span class="network-badge known">Known network</span>' : '<span class="network-badge unknown">Password required</span>';
    wifiPassword.style.display = network.known ? 'none' : 'block';
    wifiPassword.value = '';
  }
  function attachNetworkEvents() {
    body.querySelectorAll('.network-row').forEach((row) => {
      row.addEventListener('click', () => {
        clearSelectionStyles();
        row.classList.add('selected');
        showNetworkDetail({ ssid: row.dataset.ssid, known: row.dataset.known === '1' });
      });
    });
  }
  function renderNetworks(list) {
    networkList.innerHTML = list.map((network) => `
      <div class="network-row" data-ssid="${network.ssid}" data-known="${network.known ? '1' : '0'}">
        <div class="network-row-left">
          <div class="network-row-ssid">${network.ssid}</div>
          <div class="network-row-meta">
            <span>${network.signal}%</span>
          </div>
        </div>
        <div class="network-badge ${network.known ? 'known' : 'unknown'}">
          ${network.known ? 'Known' : 'Unknown'}
        </div>
      </div>
    `).join('');
    attachNetworkEvents();
  }

  networkCheckbox.addEventListener('change', () => {
    if (networkCheckbox.checked) { 
      apCheckbox.checked = false; 
      wifiSection.style.display = 'block'; 
    } else { 
      networkDetail.style.display = 'none';
      selectedNetwork = null; 
      }
  });

  apCheckbox.addEventListener('change', () => {
    if (apCheckbox.checked) { 
      networkCheckbox.checked = false; 
      wifiSection.style.display = 'none'; 
      networkDetail.style.display = 'none'; 
      selectedNetwork = null; }
  });
  refreshNetworksButton.addEventListener('click', async () => {
  if (networkScanPending) {
    refreshNetworksButton.disabled = true; 
    refreshNetworksButton.textContent = 'Scanning';
    try { 
      const response = await fetch(`/api/v1/settings/network`); 
      const data = await response.json(); 
      renderNetworks(data.networks || []); 
      networkScanPending = false; }
    catch (error) { console.error("Error refreshing networks:", error); }
    finally { 
      refreshNetworksButton.disabled = false; 
      refreshNetworksButton.textContent = 'Refresh Networks'; }
    return;
  }       

  const modal = createModal('Confirm');
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <p>
      Scanning for networks will temporarily interrupt the access point.
    </p>
    <p>
      Connect to the access point again and press the button again, the list will load.
    </p>
    <button id="confirm-action">
      Confirm
    </button>
  `;

  body.querySelector('#confirm-action').addEventListener('click', async () => {
    modal.remove();

    networkScanPending = true; 
    refreshNetworksButton.disabled = true; 
    refreshNetworksButton.textContent = 'Disabled';

    try { 
      const response = await fetch(`/api/v1/settings/network/refresh`, { method: 'POST' }); 
      const result = await response.json(); 
      renderNetworks(result.networks || []); 
      networkScanPending = false; }
    catch (error) {
      console.log('Reconnect to access point and scan again.'); 
      refreshNetworksButton.textContent = 'Load networks'; 
    }
    finally { 
      refreshNetworksButton.disabled = false; 
      if (!networkScanPending) refreshNetworksButton.textContent = 'Refresh Networks'; }
  });

  modal.querySelector('.modal-close').addEventListener('click', () => {
    modal.remove();
  });
});

  if (data.wifi_ssid) {
    const preselected = body.querySelector(`.network-row[data-ssid="${CSS.escape(data.wifi_ssid)}"]`);
    if (preselected) { 
      preselected.classList.add('selected'); 
      showNetworkDetail({ ssid: preselected.dataset.ssid, known: preselected.dataset.known === '1' }); }
  }
  connectNetworkButton.addEventListener('click', async () => {
    if (!selectedNetwork) return;
    const payload = { 
      network_mode: 'wifi', 
      ssid: selectedNetwork.ssid, 
      password: selectedNetwork.known ? '' : wifiPassword.value.trim() 
    };
    if (!selectedNetwork.known && !payload.password) return;
    await fetch(`/api/v1/settings/network`, { 
      method: 'POST', headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(payload) 
    });
    modal.remove(); 
  });
  saveNetworkButton.addEventListener('click', async () => {
    const payload = networkCheckbox.checked ? { network_mode: 'wifi', ssid: selectedNetwork ? selectedNetwork.ssid : '', password: selectedNetwork && selectedNetwork.known ? '' : (wifiPassword.value.trim() || '') } : { network_mode: 'ap' };
    await fetch(`/api/v1/settings/network`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    modal.remove(); 
  });
  attachNetworkEvents();
  modal.querySelector('.modal-close').addEventListener('click', () => { modal.remove(); refreshInsideSettingsScreen(); });
}

// Weather settings modal
async function openWeatherSettings() {
  const modal = createModal('Weather Settings');
  const body = modal.querySelector('.modal-body');
  let data = {};
  try { 
    const response = await fetch(`/api/v1/settings/weather`); 
    data = await response.json(); }
  catch (error) { 
    console.error(error); 
    return; 
  }
  const isInsideFrontend = document.body.classList.contains('inside-frontend');

  body.innerHTML = `
    <div class="settings-item">
      <label>
        Enabled
      </label>
      <input type="checkbox" id="weather-checkbox" ${data.weather === 'on' ? 'checked' : ''}>
      ${isInsideFrontend ? '' : `
        <button id="set-weather" ${data.weather === 'on' ? '' : 'disabled'}>
          Set
        </button>
      `}
    </div>
    <button id="save-weather" style="margin-top:20px;">
      Save
    </button>
  `;
  const weatherCheckbox = body.querySelector('#weather-checkbox');
  const setButton = body.querySelector('#set-weather');
  if (setButton) {
    setButton.disabled = !weatherCheckbox.checked;
    setButton.addEventListener('click', () => openWeatherDetailsModal());
    weatherCheckbox.addEventListener('change', () => {
      setButton.disabled = !weatherCheckbox.checked;
    });
  }
  body.querySelector('#save-weather').addEventListener('click', async () => {
    const mode = weatherCheckbox.checked ? 'on' : 'off';
      await fetch(`/api/v1/settings/weather`, {
         method: 'POST', 
         headers: { 'Content-Type': 'application/json' }, 
         body: JSON.stringify({ state: mode }) 
        });
    modal.remove();
  });
  modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
}
// Configure City & Country for the OpenMeteo API, wordt nog veranderd, moet beter ogen.
async function openWeatherDetailsModal() {
  const modal = createModal('Set city & country');
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <input type="text" id="weather-city" placeholder="City">
    <input type="text" id="weather-country" placeholder="Country">
    <button id="save-weather-details">Save</button>`;
  body.querySelector('#save-weather-details').addEventListener('click', async () => {
    const city = body.querySelector('#weather-city').value;
    const country = body.querySelector('#weather-country').value;
    await fetch(`/api/v1/settings/weather-details`, {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify({ city, country }) });
    modal.remove();
  });
  modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
}

// Time Settings Modal
async function openTimeSettings() {
  const modal = createModal('Time Settings');
  const body = modal.querySelector('.modal-body');
  let data = {};
  try {
    const response = await fetch(`/api/v1/settings/time`);
    data = await response.json();
  } catch (error) {
    console.error(error);
    return;
  }

  body.innerHTML = `
    <div class="settings-item">
      <label>
        Network Time
      </label>
      <input type="checkbox" id="network-time" ${data.time_mode === 'ntp' || data.time_mode === 'network' ? 'checked' : ''}>
    </div>
    <div class="settings-item">
      <label>
        Manual Time
      </label>
      <input type="checkbox" id="manual-time" ${data.time_mode === 'manual' ? 'checked' : ''}> 
    </div>
    <div>
      <button id="set-time" class="time-action-button" ${data.time_mode !== 'manual' ? 'disabled' : ''}>
        Set
      </button>
    </div>
    <button id="save-time" class="time-action-button" style="margin-top:20px;">
      Save
    </button>
  `;

  const networkTime = body.querySelector('#network-time');
  const manualTime = body.querySelector('#manual-time');
  const setButton = body.querySelector('#set-time');

  networkTime.addEventListener('change', () => {
    if (networkTime.checked) {
      manualTime.checked = false;
      setButton.disabled = true;
    } else {
      networkTime.checked = true;
    }
  });

  manualTime.addEventListener('change', () => {
    if (manualTime.checked) {
      networkTime.checked = false;
      setButton.disabled = false;
    } else {
      manualTime.checked = true;
    }
  });

  setButton.addEventListener('click', () => openManualTimeModal());

  body.querySelector('#save-time').addEventListener('click', async () => {
    const mode = manualTime.checked ? 'manual' : 'network';
    await fetch(`/api/v1/settings/time`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ time_mode: mode })
    });
    modal.remove();
    refreshInsideSettingsScreen();
  });

  modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
}
// Manual time input modal
function openManualTimeModal() {
  const modal = createModal('Set Date & Time');
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <input type="text" id="manual-date" placeholder="YYYY-MM-DD">
    <input type="text" id="manual-time-value" placeholder="HH:MM">
    <button id="save-manual-time">Save</button>
  `;

  focusIndex = -1;
  setTimeout(() => focusNext(), 0);

  body.querySelector('#save-manual-time').addEventListener('click', async () => {
    const date = body.querySelector('#manual-date').value;
    const time = body.querySelector('#manual-time-value').value;
    await fetch(`/api/v1/settings/manual-time`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, time })
    });
    modal.remove();
    refreshInsideSettingsScreen();
  });

  modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
}
// Alarm adding/editing modal
function openAlarmModal(alarm = null) {
  const isInsideFrontend = document.body.classList.contains('inside-frontend');
  const modal = createModal(alarm ? 'Edit Alarm' : 'Add Alarm');
  const body = modal.querySelector('.modal-body');
  focusIndex = -1;
  setTimeout(() => focusNext(), 0);
  const timestamp = alarm?.timestamp || '07:00:00';
  const label = alarm?.label || '';
  const bitmask = alarm?.days_bitmask || 0;
  const snoozeEnabled = alarm?.snooze_enabled ?? 1;
  const snoozeMinutes = alarm?.snooze_minutes ?? 5;
  const time = timestamp.split(' ')[1]?.slice(0, 5) || timestamp.split('T')[1]?.slice(0, 5) || timestamp.slice(0, 5);
  const days = [
    { label: 'M', value: 2 }, { label: 'T', value: 4 }, { label: 'W', value: 8 }, { label: 'T', value: 16 },
    { label: 'F', value: 32 }, { label: 'S', value: 64 }, { label: 'S', value: 1 }
  ];
  body.innerHTML = `
  <label>
    Time
  </label>
  <input id="alarm-time" type="text" value="${time}">
    ${isInsideFrontend ? '' : `
      <label>
        Label
      </label>
      <input id="alarm-label" type="text" value="${label}" placeholder="Alarm label">`}
      <div class="settings-item">
        <label>
          Active
        </label>
        <input type="checkbox" id="alarm-active" ${(alarm?.active ?? 1) ? 'checked' : ''}>
      </div>
      <div class="settings-item">
        <label>
          Snooze enabled
        </label>
        <input type="checkbox" id="alarm-snooze-enabled" ${snoozeEnabled ? 'checked' : ''}>
      </div>
      <div class="settings-item">
        <label>
          Snooze minutes
        </label>
        <div style="display:flex;gap:8px;align-items:center;">
          <input type="number" id="alarm-snooze-minutes" min="1" max="60" value="${snoozeMinutes}">
          <button type="button" id="alarm-clear-snooze">Clear</button>
        </div>
      </div>
      <div id="alarm-difficulty">
        <div class="difficulty-option ${!alarm || alarm.difficultyID == 1 ? 'active' : ''}" data-value="1">Easy</div>
        <div class="difficulty-option ${alarm?.difficultyID == 2 ? 'active' : ''}" data-value="2">Medium</div>
        <div class="difficulty-option ${alarm?.difficultyID == 3 ? 'active' : ''}" data-value="3">Hard</div>
      </div>
      <div id="alarm-days" style="display:flex;gap:8px;flex-wrap:wrap;">
        ${days.map((day) => `<div class="day-sphere ${bitmask & day.value ? 'active' : ''}" data-bit="${day.value}">${day.label}</div>`).join('')}
      </div>
      <button id="save-alarm">
        Save Alarm
      </button>`;
  const dayButtons = body.querySelectorAll('.day-sphere');
  const snoozeEnabledCheckbox = body.querySelector('#alarm-snooze-enabled');
  const snoozeMinutesInput = body.querySelector('#alarm-snooze-minutes');
  const clearSnoozeButton = body.querySelector('#alarm-clear-snooze');
  if (snoozeMinutesInput) snoozeMinutesInput.disabled = !snoozeEnabledCheckbox.checked;
  body.querySelectorAll('.difficulty-option').forEach(option => {
  option.addEventListener('click', () => {
    body.querySelectorAll('.difficulty-option')
      .forEach(el => el.classList.remove('active'));

      option.classList.add('active');
    });
  });
  dayButtons.forEach((button) => button.addEventListener('click', () => button.classList.toggle('active')));
  if (snoozeEnabledCheckbox && snoozeMinutesInput) {
    snoozeEnabledCheckbox.addEventListener('change', () => {
      snoozeMinutesInput.disabled = !snoozeEnabledCheckbox.checked;
    });
  }
  if (clearSnoozeButton && snoozeMinutesInput) {
    clearSnoozeButton.addEventListener('click', () => {
      snoozeMinutesInput.value = '';
    });
  }
  body.querySelector('#save-alarm').addEventListener('click', async () => {
    const time = body.querySelector('#alarm-time').value.trim();
    const label = isInsideFrontend ? (alarm?.label || '') : body.querySelector('#alarm-label').value;
    let days_bitmask = 0;
    body.querySelectorAll('.day-sphere.active').forEach((day) => days_bitmask |= Number(day.dataset.bit));
    const active = document.getElementById('alarm-active').checked ? 1 : 0;
    const difficultyID = parseInt(body.querySelector('.difficulty-option.active').dataset.value);
    const originalDate = alarm ? (timestamp.split('T')[0] || timestamp.split(' ')[0]) : new Date().toISOString().split('T')[0];
    const snooze_enabled = snoozeEnabledCheckbox?.checked ? 1 : 0;
    const snooze_minutes = parseInt(snoozeMinutesInput?.value || '5') || 5;
    if (!/^\d{2}:\d{2}$/.test(time)) return;
    const [hours, minutes] = time.split(':').map(Number);
    if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) return;
    const payload = { timestamp: `${originalDate}T${time}:00`, label, difficultyID, days_bitmask, active, snooze_enabled, snooze_minutes };
    try {
      if (alarm) await fetch(`/api/v1/alarms/${alarm.alarmID}/`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      else await fetch(`/api/v1/alarms/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      modal.remove(); loadAlarms();
    } catch (error) { console.error(error); }
  });
  modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
}
// Hardware test modal + stream
async function runHardwareTest(testName, isSensor = false) {
  const modal = createModal(`Hardware Test • ${testName}`);
  let ws = null;
  let closed = false;
  let doneResolve = null;
  const done = new Promise((resolve) => { doneResolve = resolve; });
  async function stopHardware() { try { 
    await fetch(`/api/v1/hardware/${testName}/stop`, { method: 'POST' }); } 
    catch {} 
  }
  function closeSocket() { try { 
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) ws.close(); } 
    catch {} 
  }
  async function closeModal() {
    if (closed) return;
    closed = true; await stopHardware();
    if (testName === 'keypad') await new Promise((resolve) => setTimeout(resolve, 100));
    closeSocket(); 
    modal.remove(); 
    if (doneResolve) doneResolve();
  }

  modal.querySelector('.modal-close').addEventListener('click', closeModal);
  try {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/hardware/${testName}/ws`);
    if (testName === 'keypad') {
      const keypad = createKeypad(modal);
      ws.onmessage = (event) => {
        if (closed) return;
        const lines = String(event.data || '').split('\n').filter(Boolean);
        for (const line of lines) {
          const clean = line.trim();
          if (clean.startsWith('PRESS:')) setKeyState(keypad, clean.replace('PRESS:', ''), true);
          else if (clean.startsWith('RELEASE:')) setKeyState(keypad, clean.replace('RELEASE:', ''), false);
        }
      };
      ws.onerror = (error) => { if (!closed) console.error(error); };
      await done; return;
    }
    if (!isSensor) {
      const statusBox = createSensorStatus(modal);
      let active = true;
      function connectSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/hardware/${testName}/ws`);
        ws.onmessage = () => {}; ws.onerror = (error) => { if (!closed) console.error(error); };
      }
      updateSensorStatus(statusBox, 'ACTIVE'); statusBox.style.cursor = 'pointer';
      statusBox.addEventListener('click', async () => {
        active = !active;
        if (active) { 
          updateSensorStatus(statusBox, 'ACTIVE'); 
          closeSocket(); 
          connectSocket(); }
        else { 
          await stopHardware(); 
          closeSocket(); 
          updateSensorStatus(statusBox, 'STOPPED'); }
      });
      ws.onmessage = () => {}; ws.onerror = (error) => { if (!closed) console.error(error); };
      await done; return;
    }
    const statusBox = createSensorStatus(modal);
    ws.onmessage = (event) => { 
      if (closed) return; 
      updateSensorStatus(statusBox, String(event.data || '').trim()); 
    };
    ws.onerror = (error) => { 
      if (!closed) console.error(error); 
    };
    await done;
  } catch (error) { if (!closed) console.error(error); }
  finally { 
    try { closeSocket(); } 
    catch {} 
  }
}
// Key input in modals (inside frontend)
function modalInput(key) {
  const current = document.activeElement;
  if (!current || current.tagName !== 'INPUT') return;

  if (current.id === 'alarm-time' || current.id === 'manual-time-value') {
    let digits = (current.dataset.digits || '') + key;
    digits = digits.replace(/\D/g, '').slice(-4);
    current.dataset.digits = digits;

    if (digits.length <= 2) current.value = digits;
    else current.value = `${digits.slice(0, digits.length - 2)}:${digits.slice(-2)}`;
    return;
  }

  if (current.id === 'manual-date') {
    let digits = (current.dataset.digits || '') + key;
    digits = digits.replace(/\D/g, '').slice(-8);
    current.dataset.digits = digits;

    if (digits.length <= 4) current.value = digits;
    else if (digits.length <= 6) current.value = `${digits.slice(0, 4)}-${digits.slice(4)}`;
    else current.value = `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6)}`;
    return;
  }

  current.value += key;
}

// Next element through keypad (inside frontend)
function focusNext() {
  const elements = Array.from(getFocusableElements());
  if (!elements.length) return;

  const active = document.activeElement;
  if (active && active.blur) active.blur();

  elements.forEach((el) => {
    el.classList.remove('selected');
    el.closest('.settings-item')?.classList.remove('selected');
  });

  focusIndex++;
  if (focusIndex >= elements.length) focusIndex = 0;

  const element = elements[focusIndex];

  if ((element.type === 'checkbox' || element.type === 'radio') && element.closest('.settings-item')) {
    element.closest('.settings-item').classList.add('selected');
  } else {
    element.classList.add('selected');
  }
  element.scrollIntoView({
    block: 'center',
    behavior: 'smooth'
  });
  if (element.tagName === 'INPUT' || element.tagName === 'SELECT') {
    element.focus();
  }
  
}

// Confirmation through keypad (inside frontend)
function confirmFocused() {
  const elements = getFocusableElements();
  if (!elements.length) return;
  const element = elements[focusIndex];
  if (!element) return;
  if (element.classList.contains('day-sphere')) { element.classList.toggle('active'); return;}
  if (element.classList.contains('difficulty-option')) {
  document.querySelectorAll('.difficulty-option')
    .forEach(el => el.classList.remove('active'));
    element.classList.add('active');
    return;
  }
  if (element.tagName === 'INPUT' && (element.type === 'checkbox' || element.type === 'radio')) {
    element.click();
    return;
  }
  element.click();
  
}

// #endregion

// #region *** Data Access - get___                     ***********
// Load alarms & fill content
async function loadAlarms() {
  const container = document.getElementById('alarms-container');
  const insideContainer = document.getElementById('alarms-screen');
  if (!container && !insideContainer) return;
  const response = await fetch(`/api/v1/alarms`);
  const data = await response.json();
  const days = [
    { label: 'M', bit: 2 }, 
    { label: 'T', bit: 4 }, 
    { label: 'W', bit: 8 }, 
    { label: 'T', bit: 16 },
    { label: 'F', bit: 32 }, 
    { label: 'S', bit: 64 }, 
    { label: 'S', bit: 1 }
  ];
  const html = `
    <div class="alarm-actions">
      <button id="add-alarm" onclick="openAlarmModal()">
        Add
      </button>
    </div>` + data.alarms.map((alarm) => {
    const mask = alarm.days_bitmask || 0;
    let time = '';
    if (typeof alarm.timestamp === 'string') {
      time = alarm.timestamp.split(' ')[1]?.slice(0, 5) || alarm.timestamp.split('T')[1]?.slice(0, 5) || alarm.timestamp.slice(0, 5);
    } else { time = '--:--'; }
    return `
    <div class="alarm-row">
      <div class="alarm-main">
        <div class="alarm-time">${time}
      </div>
      <div class="alarm-days">
        ${days.map((day) => `
          <div class="day-sphere ${mask & day.bit ? 'active' : ''}">
            ${day.label}
          </div>`).join('')}
      </div>
    </div>
    <div class="alarm-actions">
      <button onclick="editAlarm(${alarm.alarmID})">
        Edit
      </button>
      <button onclick="toggleAlarm(${alarm.alarmID})">
        ${alarm.active ? 'Disable' : 'Enable'}
      </button>
      <button onclick="deleteAlarm(${alarm.alarmID})">
        Delete
      </button>
    </div>
  </div>
  `;
  }).join('');
  if (container) container.innerHTML = html;
  if (insideContainer) insideContainer.innerHTML = html;
}

// Alarm edit modal (w/ alarm id)
async function toggleAlarm(alarmID) {
  const response = await fetch('/api/v1/alarms');
  const data = await response.json();

  const alarm = data.alarms.find(a => a.alarmID === alarmID);
  if (!alarm) return;

  try {
    await fetch(`/api/v1/alarms/${alarmID}/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        timestamp: alarm.timestamp,
        label: alarm.label,
        difficultyID: alarm.difficultyID,
        days_bitmask: alarm.days_bitmask,
        active: alarm.active ? 0 : 1
      })
    });
    loadAlarms();
  } catch (e) {
    console.error(e);
  }
}
async function editAlarm(alarmID) {
  const response = await fetch(`/api/v1/alarms`);
  const data = await response.json();
  const alarm = data.alarms.find((a) => a.alarmID === alarmID);
  if (!alarm) return;
  openAlarmModal(alarm);
}

async function deleteAlarm(alarmID) {
  try { 
    await fetch(`/api/v1/alarms/${alarmID}`, { method: 'DELETE' }); 
    loadAlarms(); 
  }
  catch (error) { console.error(error); }
}
// #endregion

// #region *** Event Listeners - listenTo___            ***********
function listenToSettings() {
  if (settingsWS && (settingsWS.readyState === WebSocket.OPEN || settingsWS.readyState === WebSocket.CONNECTING)) return;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  settingsWS = new WebSocket(`${protocol}//${window.location.host}/api/v1/settings/ws`);
  settingsWS.onopen = () => console.log("settings WS connected");
  settingsWS.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(event.data);
    if (data.type === 'theme') document.documentElement.style.setProperty('--accent', data.color);
    if (data.type === 'username') {
      const welcome = document.querySelector('.welcome-text');
      if (welcome) welcome.textContent = `Hi, ${data.username}`;
    }
    if (data.type === 'refresh') {
      refreshAll();
    }
  };
  settingsWS.onclose = () => { settingsWS = null; setTimeout(listenToSettings, 2000); };
  settingsWS.onerror = () => { settingsWS = null; };
}

// Listens to live keypad stream (inside frontend)
function startInsideKeypadListener() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/hardware/keypad/live`);
  console.log("ws reach");
  ws.onmessage = (event) => {
    const message = String(event.data || '');
    if (!message.startsWith('PRESS:')) return;
    handleInsideKeypad(message.replace('PRESS:', ''));
  };
  ws.onclose = () => setTimeout(startInsideKeypadListener, 1000);
}

// Handles the inputs from the live keypad stream for naviftion (inside frontend)
function handleInsideKeypad(key) {
  if (!document.getElementById('home-screen')) return;

  const active = document.activeElement;
  if (active && active.tagName === 'INPUT') {
    if (/^[0-9]$/.test(key)) {
      if (active.id === 'alarm-time' || active.id === 'manual-time-value') {
        let digits = (active.dataset.digits || '') + key;
        digits = digits.replace(/\D/g, '').slice(-4);
        active.dataset.digits = digits;
        if (digits.length <= 2) active.value = digits;
        else active.value = `${digits.slice(0, digits.length - 2)}:${digits.slice(-2)}`;
        return;
      }

      if (active.id === 'manual-date') {
        let digits = (active.dataset.digits || '') + key;
        digits = digits.replace(/\D/g, '').slice(-8);
        active.dataset.digits = digits;
        if (digits.length <= 4) active.value = digits;
        else if (digits.length <= 6) active.value = `${digits.slice(0, 4)}-${digits.slice(4)}`;
        else active.value = `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6)}`;
        return;
      }

      active.value += key;
      return;
    }

    if (key === '*') {
      focusNext();
      return;
    }

    if (key === '#') {
      confirmFocused();
      return;
    }
  }

  switch (key) {
    case '1': showScreen('home'); setActiveNav('home'); break;
    case '2': showScreen('alarms'); setActiveNav('alarms'); break;
    case '3': showScreen('settings'); setActiveNav('settings'); break;
    case '*': focusNext(); break;
    case '#': confirmFocused(); break;
  }
}
// #endregion

// #region *** Init / DOMContentLoaded                  ***********
// Initialises the theme and applies it
async function initTheme() {
  let selectedColor = null;
  const picker = document.getElementById('theme-picker');
  const confirmButton = document.getElementById('theme-save-button');
  try {
    const response = await fetch(`/api/v1/settings/theme`);
    const data = await response.json();
    if (data.color) {
      document.documentElement.style.setProperty('--accent', data.color);
      selectedColor = data.color;
      if (picker) picker.value = data.color;
    }
  } catch (error) { console.error(error); }
  if (!picker || !confirmButton) return;
  picker.addEventListener('input', (e) => selectedColor = e.target.value);
  confirmButton.addEventListener('click', async () => {
    if (!selectedColor) return;
    document.documentElement.style.setProperty('--accent', selectedColor);
    try { 
      await fetch(`/api/v1/settings/theme`, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ color: selectedColor }) }); 
      }
    catch (error) { console.error("Couldn't get theme: ", error); }
  });
}

// Initialises the user name and sets it
async function initName() {
  const welcomeText = document.querySelector('.welcome-text');
  const nameInput = document.getElementById('name-input');
  const confirmButton = document.getElementById('username-save-button');
  try {
    const response = await fetch(`/api/v1/settings/username`);
    const data = await response.json();
    if (data.username) {
      if (welcomeText) welcomeText.textContent = `Hi, ${data.username}`;
      if (nameInput) nameInput.value = data.username;
    }
  } catch (error) { console.error(error); }
  if (!nameInput || !confirmButton) return;
  confirmButton.addEventListener('click', async () => {
    try {
      await fetch(`/api/v1/settings/username`, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ username: nameInput.value.trim() }) 
      });
      if (welcomeText) welcomeText.textContent = `Hello, ${nameInput.value.trim()}`;
    } catch (error) { console.error(error); }
  });
}

// DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initName();
  updateClock();
  setInterval(updateClock, 10000);
  loadAlarms();
  listenToSettings();
  loadDashboard();
  loadLogs();
  if (document.body.classList.contains('inside-frontend')) {
    startLiveAlarmListener();
    startInsideKeypadListener();
    refreshWeather();
  }
  refreshWeather();
});
// #endregion