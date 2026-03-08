"""Enhanced dashboard HTML with primitive types, agents, and workflow hierarchies."""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>TTA.dev Observability Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0a0e27;
            color: #e0e6ed;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        h1 { margin: 0; font-size: 2.5em; }
        .subtitle { opacity: 0.9; margin-top: 10px; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: #1a1f3a;
            border: 1px solid #2d3561;
            border-radius: 8px;
            padding: 20px;
        }
        .metric-card h3 {
            margin: 0 0 15px 0;
            color: #667eea;
            font-size: 1.1em;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
            color: #10b981;
        }
        .metric-label {
            opacity: 0.7;
            font-size: 0.9em;
        }
        
        .section {
            background: #1a1f3a;
            border: 1px solid #2d3561;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section h2 {
            margin: 0 0 20px 0;
            color: #667eea;
            font-size: 1.5em;
        }
        
        .primitives-list, .agents-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }
        .primitive-item, .agent-item {
            background: #0f1329;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }
        .primitive-name, .agent-name {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }
        .primitive-count, .agent-count {
            font-size: 1.5em;
            color: #10b981;
        }
        
        .traces-table {
            width: 100%;
            border-collapse: collapse;
        }
        .traces-table th {
            background: #0f1329;
            padding: 12px;
            text-align: left;
            color: #667eea;
            font-weight: 600;
        }
        .traces-table td {
            padding: 12px;
            border-bottom: 1px solid #2d3561;
        }
        .traces-table tr:hover {
            background: #0f1329;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .status-success {
            background: #10b981;
            color: white;
        }
        .status-failed {
            background: #ef4444;
            color: white;
        }
        
        .status-operational {
            background: #10b981;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        #live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
            margin-right: 8px;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.1); }
        }
        
        .footer {
            text-align: center;
            opacity: 0.6;
            margin-top: 50px;
            padding: 20px;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            opacity: 0.6;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 TTA.dev Observability Dashboard</h1>
        <div class="subtitle">
            <span id="live-indicator"></span>
            Real-time monitoring powered by TTA.dev primitives
        </div>
    </div>

    <div id="status-banner" style="margin-bottom: 20px;">
        <span class="status-operational">● OPERATIONAL</span>
    </div>

    <div class="metrics-grid" id="metrics">
        <div class="metric-card">
            <h3>📊 Total Workflows</h3>
            <div class="metric-value" id="total-workflows">0</div>
            <div class="metric-label">Executed</div>
        </div>
        <div class="metric-card">
            <h3>✅ Completed</h3>
            <div class="metric-value" id="completed-workflows">0</div>
            <div class="metric-label">Successfully Finished</div>
        </div>
        <div class="metric-card">
            <h3>❌ Failed</h3>
            <div class="metric-value" id="failed-workflows">0</div>
            <div class="metric-label">With Errors</div>
        </div>
        <div class="metric-card">
            <h3>⏱️ Avg Duration</h3>
            <div class="metric-value" id="avg-duration">0</div>
            <div class="metric-label">milliseconds</div>
        </div>
    </div>

    <div class="section">
        <h2>🔧 Primitives Used</h2>
        <div id="primitives-list" class="primitives-list">
            <div class="empty-state">No primitives executed yet</div>
        </div>
    </div>

    <div class="section">
        <h2>🤖 Agents Active</h2>
        <div id="agents-list" class="agents-list">
            <div class="empty-state">No agents tracked yet</div>
        </div>
    </div>

    <div class="section">
        <h2>📝 Recent Traces</h2>
        <table class="traces-table" id="traces-table">
            <thead>
                <tr>
                    <th>Trace ID</th>
                    <th>Primitive</th>
                    <th>Agent</th>
                    <th>Duration</th>
                    <th>Status</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody id="traces-body">
                <tr><td colspan="6" class="empty-state">No traces recorded yet</td></tr>
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p>Built with TTA.dev primitives: CircuitBreaker + Retry + LambdaPrimitive</p>
        <p>Last updated: <span id="last-update">Never</span></p>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received data:', data);
            
            // Update workflows metrics
            if (data.workflows) {
                document.getElementById('total-workflows').textContent = data.workflows.total || 0;
                document.getElementById('completed-workflows').textContent = data.workflows.completed || 0;
                document.getElementById('failed-workflows').textContent = data.workflows.failed || 0;
            }
            
            // Update performance
            if (data.performance) {
                const avgDuration = data.performance.avg_duration_ms || 0;
                document.getElementById('avg-duration').textContent = avgDuration.toFixed(2);
            }
            
            // Update primitives
            if (data.primitives && Object.keys(data.primitives).length > 0) {
                const primitivesList = document.getElementById('primitives-list');
                primitivesList.innerHTML = '';
                for (const [name, count] of Object.entries(data.primitives)) {
                    const div = document.createElement('div');
                    div.className = 'primitive-item';
                    div.innerHTML = `
                        <div class="primitive-name">${name}</div>
                        <div class="primitive-count">${count}</div>
                        <div class="metric-label">executions</div>
                    `;
                    primitivesList.appendChild(div);
                }
            }
            
            // Update agents
            if (data.agents && Object.keys(data.agents).length > 0) {
                const agentsList = document.getElementById('agents-list');
                agentsList.innerHTML = '';
                for (const [name, count] of Object.entries(data.agents)) {
                    const div = document.createElement('div');
                    div.className = 'agent-item';
                    div.innerHTML = `
                        <div class="agent-name">${name}</div>
                        <div class="agent-count">${count}</div>
                        <div class="metric-label">activities</div>
                    `;
                    agentsList.appendChild(div);
                }
            }
            
            // Update recent traces
            if (data.recent_traces && data.recent_traces.length > 0) {
                const tracesBody = document.getElementById('traces-body');
                tracesBody.innerHTML = '';
                for (const trace of data.recent_traces) {
                    const tr = document.createElement('tr');
                    const statusClass = trace.status === 'success' ? 'status-success' : 'status-failed';
                    const timestamp = new Date(trace.timestamp).toLocaleString();
                    tr.innerHTML = `
                        <td><code>${trace.trace_id}</code></td>
                        <td>${trace.primitive}</td>
                        <td>${trace.agent}</td>
                        <td>${trace.duration_ms.toFixed(2)} ms</td>
                        <td><span class="status-badge ${statusClass}">${trace.status}</span></td>
                        <td>${timestamp}</td>
                    `;
                    tracesBody.appendChild(tr);
                }
            }
            
            // Update last update time
            if (data.timestamp) {
                document.getElementById('last-update').textContent = new Date(data.timestamp).toLocaleString();
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            document.getElementById('status-banner').innerHTML = 
                '<span class="status-badge status-failed">● DISCONNECTED</span>';
        };
    </script>
</body>
</html>
"""
