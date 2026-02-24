/* Dashboard JavaScript for Dynamic Content */

// API Base URL
const API_BASE_URL = 'http://localhost:5000/api';

// Utility Functions
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

// Load Dashboard Statistics
async function loadStatistics() {
    const stats = await fetchAPI('/stats');
    
    if (stats) {
        document.getElementById('total-entries').textContent = stats.access_events.total_entries;
        document.getElementById('total-exits').textContent = stats.access_events.total_exits;
        document.getElementById('active-alerts').textContent = stats.threats.active_alerts;
        document.getElementById('today-accesses').textContent = stats.access_events.today;
    }
}

// Load Access Logs
async function loadAccessLogs(personId = null, limit = 20) {
    let endpoint = `/logs?limit=${limit}`;
    if (personId) {
        endpoint += `&person_id=${personId}`;
    }

    const data = await fetchAPI(endpoint);
    
    if (data && data.logs) {
        const tableBody = document.getElementById('logs-table-body');
        tableBody.innerHTML = '';

        data.logs.forEach(log => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${log.person_id || 'Unknown'}</td>
                <td>${log.name || '-'}</td>
                <td>${log.type === 'entry' ? '↓ Entry' : '↑ Exit'}</td>
                <td><span class="status ${log.status === 'success' ? 'healthy' : 'critical'}">${log.status}</span></td>
                <td>${(log.confidence * 100).toFixed(1)}%</td>
                <td>${formatDateTime(log.timestamp)}</td>
            `;
            tableBody.appendChild(row);
        });
    }
}

// Load Active Threats/Alerts
async function loadThreats(severity = null) {
    let endpoint = '/threats';
    if (severity) {
        endpoint += `?severity=${severity}`;
    }

    const data = await fetchAPI(endpoint);
    
    if (data && data.threats) {
        const alertsContainer = document.getElementById('alerts-container');
        alertsContainer.innerHTML = '';

        if (data.threats.length === 0) {
            alertsContainer.innerHTML = '<p style="text-align: center; color: #888;">No active threats</p>';
            return;
        }

        data.threats.forEach(threat => {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${threat.severity.toLowerCase()}`;
            alertDiv.innerHTML = `
                <div class="alert-content">
                    <h4>${threat.threat_type}</h4>
                    <p>${threat.message}</p>
                </div>
                <div class="alert-time">${formatDateTime(threat.timestamp)}</div>
            `;
            alertsContainer.appendChild(alertDiv);
        });
    }
}

// Load Audit Log (Compliance)
async function loadAuditLog(limit = 50) {
    const data = await fetchAPI(`/compliance/audit?limit=${limit}`);
    
    if (data && data.audit_log) {
        const tableBody = document.getElementById('audit-table-body');
        if (tableBody) {
            tableBody.innerHTML = '';

            data.audit_log.forEach(entry => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${entry.action}</td>
                    <td>${entry.user || '-'}</td>
                    <td>${entry.resource || '-'}</td>
                    <td>${entry.result}</td>
                    <td>${formatDateTime(entry.timestamp)}</td>
                `;
                tableBody.appendChild(row);
            });
        }
    }
}

// Utility: Format DateTime
function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Navigation
function showTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.style.display = 'none');

    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }

    // Update nav links
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');
}

// Refresh Data
function refreshData() {
    loadStatistics();
    loadAccessLogs();
    loadThreats();
    console.log('Dashboard data refreshed');
}

// Auto-refresh every 30 seconds
setInterval(refreshData, 30000);

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStatistics();
    loadAccessLogs();
    loadThreats();
    console.log('Dashboard initialized');
});
