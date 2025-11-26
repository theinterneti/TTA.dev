// TTA Observability UI - Client JavaScript
// Handles API communication, WebSocket updates, and UI rendering

const API_BASE = window.location.origin;
const WS_URL = `ws://${window.location.host}/ws/traces`;

let ws = null;
let reconnectAttempts = 0;
let currentFilter = '';

// ============================================================================
// API Client
// ============================================================================

async function fetchTraces(limit = 50, status = null) {
    try {
        const params = new URLSearchParams({ limit });
        if (status) params.append('status', status);
        
        const response = await fetch(`${API_BASE}/api/traces?${params}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        return data.traces || [];
    } catch (error) {
        console.error('Failed to fetch traces:', error);
        return [];
    }
}

async function fetchTrace(traceId) {
    try {
        const response = await fetch(`${API_BASE}/api/traces/${traceId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch trace:', error);
        return null;
    }
}

async function fetchMetricsSummary() {
    try {
        const response = await fetch(`${API_BASE}/api/metrics/summary`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch metrics:', error);
        return null;
    }
}

// ============================================================================
// WebSocket Connection
// ============================================================================

function connectWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
            updateConnectionStatus(true);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus(false);
            
            // Attempt to reconnect with exponential backoff
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            reconnectAttempts++;
            setTimeout(connectWebSocket, delay);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
    }
}

function handleWebSocketMessage(data) {
    if (data.type === 'new_trace') {
        // Add new trace to the top of the list
        addTraceToList(data.trace);
        updateMetrics();
    } else if (data.type === 'ping') {
        // Keep-alive message, ignore
    }
}

function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('connectionStatus');
    const statusText = document.getElementById('connectionText');
    
    if (connected) {
        statusDot.className = 'status-dot';
        statusText.textContent = 'Connected';
    } else {
        statusDot.className = 'status-dot disconnected';
        statusText.textContent = 'Disconnected';
    }
}

// ============================================================================
// UI Rendering
// ============================================================================

function renderTrace(trace, includeTimeline = false) {
    const statusClass = trace.status === 'error' ? 'error' : 'success';
    const duration = trace.duration_ms.toFixed(2);
    const timestamp = new Date(trace.start_time).toLocaleString();
    const primitiveCount = trace.spans.length;
    
    let html = `
        <li class="trace-item status-${statusClass}" onclick="showTraceDetails('${trace.trace_id}')">
            <div class="trace-header">
                <div class="trace-info">
                    <span class="trace-id">${trace.trace_id}</span>
                    <span class="primitive-badge">${primitiveCount} span${primitiveCount !== 1 ? 's' : ''}</span>
                </div>
                <div class="trace-meta">
                    <span class="trace-duration">${duration}ms</span>
                    <span class="trace-timestamp">${timestamp}</span>
                </div>
            </div>
    `;
    
    if (includeTimeline && trace.spans.length > 0) {
        html += renderTimeline(trace);
    }
    
    if (trace.error_message) {
        html += `<div class="trace-error">❌ ${trace.error_message}</div>`;
    }
    
    html += `</li>`;
    return html;
}

function renderTimeline(trace) {
    const totalDuration = trace.duration_ms;
    const startTime = new Date(trace.start_time).getTime();
    
    let html = '<div class="timeline">';
    
    trace.spans.forEach(span => {
        const spanStart = new Date(span.start_time).getTime();
        const spanDuration = span.duration_ms;
        const offset = ((spanStart - startTime) / totalDuration) * 100;
        const width = (spanDuration / totalDuration) * 100;
        const statusClass = span.status === 'error' ? 'error' : 'success';
        
        html += `
            <div class="timeline-bar status-${statusClass}" 
                 style="left: ${offset}%; width: ${width}%;"
                 title="${span.primitive_type || 'Unknown'}: ${spanDuration.toFixed(2)}ms">
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function renderTraceDetails(trace) {
    const statusClass = trace.status === 'error' ? 'error' : 'success';
    const duration = trace.duration_ms.toFixed(2);
    const timestamp = new Date(trace.start_time).toLocaleString();
    
    let html = `
        <div class="trace-detail">
            <div class="flex gap-2 mb-3">
                <div class="badge badge-${statusClass}">${trace.status.toUpperCase()}</div>
                <div class="badge badge-info">${trace.spans.length} spans</div>
                <div class="badge badge-secondary">${duration}ms</div>
            </div>
            
            <div class="mb-3">
                <strong>Trace ID:</strong> <code>${trace.trace_id}</code><br>
                <strong>Started:</strong> ${timestamp}<br>
                <strong>Duration:</strong> ${duration}ms
            </div>
    `;
    
    if (trace.error_message) {
        html += `
            <div class="card bg-error mb-3" style="padding: 15px;">
                <strong>Error:</strong> ${trace.error_message}
            </div>
        `;
    }
    
    // Render timeline
    html += `
        <div class="mb-3">
            <strong>Timeline:</strong>
            ${renderTimeline(trace)}
        </div>
    `;
    
    // Render spans
    html += '<div><strong>Spans:</strong></div>';
    trace.spans.forEach((span, index) => {
        const spanStatusClass = span.status === 'error' ? 'error' : 'success';
        html += `
            <div class="card mb-2" style="padding: 15px; border-left: 3px solid var(--${spanStatusClass});">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <strong>${span.primitive_type || 'Unknown Primitive'}</strong>
                        <div class="text-muted" style="font-size: 12px;">
                            Span ${index + 1} of ${trace.spans.length}
                        </div>
                    </div>
                    <div class="badge badge-${spanStatusClass}">${span.status}</div>
                </div>
                <div style="font-size: 13px;">
                    <strong>Duration:</strong> ${span.duration_ms.toFixed(2)}ms<br>
                    <strong>Started:</strong> ${new Date(span.start_time).toLocaleString()}
                </div>
        `;
        
        if (span.attributes && Object.keys(span.attributes).length > 0) {
            html += '<div class="mt-2"><strong>Attributes:</strong></div>';
            html += '<pre style="font-size: 12px; background: var(--bg-primary); padding: 10px; border-radius: 4px; overflow-x: auto;">';
            html += JSON.stringify(span.attributes, null, 2);
            html += '</pre>';
        }
        
        if (span.error_message) {
            html += `<div class="mt-2 text-error"><strong>Error:</strong> ${span.error_message}</div>`;
        }
        
        html += '</div>';
    });
    
    html += '</div>';
    return html;
}

function renderMetrics(metrics) {
    if (!metrics) return '<div class="empty-state">No metrics available</div>';
    
    let html = '<div class="metrics-grid">';
    
    html += `
        <div class="metric-card">
            <div class="metric-value text-info">${metrics.total_traces}</div>
            <div class="metric-label">Total Traces</div>
        </div>
        <div class="metric-card">
            <div class="metric-value text-success">${metrics.success_rate.toFixed(1)}%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value text-warning">${metrics.average_duration.toFixed(2)}ms</div>
            <div class="metric-label">Average Duration</div>
        </div>
    `;
    
    html += '</div>';
    
    // Primitive breakdown
    if (metrics.primitive_counts && Object.keys(metrics.primitive_counts).length > 0) {
        html += '<div class="mt-3"><h3>Primitive Usage</h3></div>';
        html += '<div class="card"><ul style="list-style: none; padding: 0;">';
        
        const sortedPrimitives = Object.entries(metrics.primitive_counts)
            .sort((a, b) => b[1] - a[1]);
        
        sortedPrimitives.forEach(([primitive, count]) => {
            html += `
                <li style="padding: 10px; border-bottom: 1px solid var(--border);">
                    <div class="flex justify-between">
                        <span>${primitive}</span>
                        <span class="badge badge-info">${count}</span>
                    </div>
                </li>
            `;
        });
        
        html += '</ul></div>';
    }
    
    return html;
}

function renderPrimitiveStats(traces) {
    const stats = {};
    
    traces.forEach(trace => {
        trace.spans.forEach(span => {
            const primitive = span.primitive_type || 'Unknown';
            if (!stats[primitive]) {
                stats[primitive] = {
                    count: 0,
                    totalDuration: 0,
                    errors: 0,
                    successes: 0
                };
            }
            
            stats[primitive].count++;
            stats[primitive].totalDuration += span.duration_ms;
            if (span.status === 'error') {
                stats[primitive].errors++;
            } else {
                stats[primitive].successes++;
            }
        });
    });
    
    let html = '<div class="card-list">';
    
    Object.entries(stats)
        .sort((a, b) => b[1].count - a[1].count)
        .forEach(([primitive, data]) => {
            const avgDuration = (data.totalDuration / data.count).toFixed(2);
            const errorRate = ((data.errors / data.count) * 100).toFixed(1);
            
            html += `
                <div class="card">
                    <div class="flex justify-between items-start mb-2">
                        <h3 class="card-title">${primitive}</h3>
                        <span class="badge badge-info">${data.count} executions</span>
                    </div>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value text-success">${data.successes}</div>
                            <div class="metric-label">Successes</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value text-error">${data.errors}</div>
                            <div class="metric-label">Errors</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value text-warning">${avgDuration}ms</div>
                            <div class="metric-label">Avg Duration</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value ${errorRate > 10 ? 'text-error' : 'text-success'}">${errorRate}%</div>
                            <div class="metric-label">Error Rate</div>
                        </div>
                    </div>
                </div>
            `;
        });
    
    html += '</div>';
    
    return Object.keys(stats).length > 0 
        ? html 
        : '<div class="empty-state">No primitive statistics available</div>';
}

// ============================================================================
// UI Updates
// ============================================================================

async function updateMetrics() {
    const metrics = await fetchMetricsSummary();
    if (!metrics) return;
    
    // Update overview metrics
    document.getElementById('totalTraces').textContent = metrics.total_traces;
    document.getElementById('successRate').textContent = `${metrics.success_rate.toFixed(1)}%`;
    document.getElementById('avgDuration').textContent = `${metrics.average_duration.toFixed(2)}ms`;
    
    const errorRate = 100 - metrics.success_rate;
    document.getElementById('errorRate').textContent = `${errorRate.toFixed(1)}%`;
}

async function updateTraceList(containerId, limit = 50, status = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const traces = await fetchTraces(limit, status);
    
    if (traces.length === 0) {
        container.innerHTML = '<li class="empty-state">No traces found</li>';
        return;
    }
    
    container.innerHTML = traces
        .map(trace => renderTrace(trace, containerId === 'recentTraces'))
        .join('');
}

function addTraceToList(trace) {
    const containers = ['recentTraces', 'allTraces'];
    
    containers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Remove empty state if present
        const emptyState = container.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
        
        // Add new trace at the top
        const li = document.createElement('li');
        li.innerHTML = renderTrace(trace, containerId === 'recentTraces');
        li.className = 'trace-item fade-in';
        container.insertBefore(li.firstChild, container.firstChild);
        
        // Limit number of displayed traces
        const maxTraces = containerId === 'recentTraces' ? 10 : 50;
        while (container.children.length > maxTraces) {
            container.removeChild(container.lastChild);
        }
    });
}

async function refreshTraces() {
    await updateTraceList('recentTraces', 10);
    await updateTraceList('allTraces', 50, currentFilter || null);
    await updateMetrics();
}

async function refreshMetrics() {
    const metrics = await fetchMetricsSummary();
    const container = document.getElementById('metricsContent');
    if (container) {
        container.innerHTML = renderMetrics(metrics);
    }
}

async function refreshPrimitiveStats() {
    const traces = await fetchTraces(100);
    const container = document.getElementById('primitiveStats');
    if (container) {
        container.innerHTML = renderPrimitiveStats(traces);
    }
}

async function filterTraces() {
    const select = document.getElementById('statusFilter');
    currentFilter = select.value;
    await updateTraceList('allTraces', 50, currentFilter || null);
}

async function showTraceDetails(traceId) {
    const trace = await fetchTrace(traceId);
    if (!trace) {
        alert('Failed to load trace details');
        return;
    }
    
    const modal = document.getElementById('traceModal');
    const details = document.getElementById('traceDetails');
    
    details.innerHTML = renderTraceDetails(trace);
    modal.style.display = 'block';
}

function closeTraceModal() {
    const modal = document.getElementById('traceModal');
    modal.style.display = 'none';
}

// ============================================================================
// Tab Navigation
// ============================================================================

function initTabNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.dataset.tab;
            
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active content
            contents.forEach(c => c.classList.remove('active'));
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
                
                // Refresh data when switching to certain tabs
                if (targetId === 'metrics') {
                    refreshMetrics();
                } else if (targetId === 'primitives') {
                    refreshPrimitiveStats();
                }
            }
        });
    });
}

// ============================================================================
// Initialization
// ============================================================================

async function init() {
    console.log('Initializing TTA Observability UI...');
    
    // Setup tab navigation
    initTabNavigation();
    
    // Connect WebSocket
    connectWebSocket();
    
    // Load initial data
    await refreshTraces();
    await refreshMetrics();
    
    console.log('TTA Observability UI initialized');
}

// Start the application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Close modal on ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeTraceModal();
    }
});
