import hashlib
import json
from flask import Flask, request, render_template_string, jsonify
import datetime
from collections import deque
import random

app = Flask(__name__)

# --- DISABLE CACHING ---
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# --- 1. BLOCKCHAIN LEDGER ---
class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(proof=1, previous_hash='0', data="Genesis Block")

    def create_block(self, proof, previous_hash, data):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'data': data
        }
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

community_ledger = Blockchain()

# --- 2. CONFIGURATION (Kakamega Forest) ---
NODE_LOCATIONS = [
    {"id": 0, "lat": 0.3520, "lng": 34.8650, "name": "Buyangu Hill"},
    {"id": 1, "lat": 0.3850, "lng": 34.8950, "name": "Kisere Fragment"},
    {"id": 2, "lat": 0.3150, "lng": 34.8450, "name": "Isiukhu River"},
    {"id": 3, "lat": 0.3280, "lng": 34.8200, "name": "Salazar Circuit"},
    {"id": 4, "lat": 0.2820, "lng": 34.8640, "name": "Isecheno Station"},
    {"id": 5, "lat": 0.2650, "lng": 34.8420, "name": "Lirhanda Hill"},
    {"id": 6, "lat": 0.2300, "lng": 34.8850, "name": "Yala River Border"},
    {"id": 7, "lat": 0.2150, "lng": 34.8550, "name": "Kibiri Block"},
    {"id": 8, "lat": 0.3600, "lng": 34.8100, "name": "Malava Edge"},
    {"id": 9, "lat": 0.2600, "lng": 34.9100, "name": "Ikuywa River East"},
    {"id": 10, "lat": 0.2900, "lng": 34.8200, "name": "Pump House Sector"},
    {"id": 11, "lat": 0.1900, "lng": 34.8400, "name": "Kaimosi Border"},
    {"id": 12, "lat": 0.2800, "lng": 34.7900, "name": "Mukumu West Gate"},
    {"id": 13, "lat": 0.3100, "lng": 34.9200, "name": "Cheenya Edge"},
    {"id": 14, "lat": 0.3000, "lng": 34.8500, "name": "Colobus Trail Inner"},
]

# --- STATE ---
node_states = {}
for node in NODE_LOCATIONS:
    node_states[node["id"]] = {
        **node, "status": "Natural", "probs": [1.0, 0.0, 0.0], "fire": False, "last_update": "Waiting..."
    }

# FIX 1: Use a standard List instead of Deque(maxlen) so count keeps growing
event_history = [] 

# Pre-fill data
curr = datetime.datetime.now()
for i in range(50):
    t = curr - datetime.timedelta(seconds=(50-i)*2)
    rand = random.random()
    if rand < 0.7:
        status = "Natural"; probs = [0.9, 0.05, 0.05]
    elif rand < 0.85:
        status = "Unnatural"; probs = [0.1, 0.8, 0.1]
    else:
        status = "Human Sound"; probs = [0.1, 0.1, 0.8]

    event_history.append({
        "node_id": random.randint(0, 14), 
        "time": t.strftime("%H:%M:%S"), 
        "status": status, 
        "probs": probs, 
        "fire": False
    })

# --- USSD ROUTE ---
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    text = request.values.get("text", "default")
    inputs = text.split('*') if text else []
    phone = request.values.get("phoneNumber", "000")
    
    if text == "":
        response = "CON BUNDI Reporter \n1. Illegal Logging \n2. Charcoal Burning \n3. Encroachment"
    elif len(inputs) == 1:
        response = "CON Select Location Code (0-14) \n 0.Buyangu Hill \n 1.Kisere Fragment \n 2.Isiukhu River \n 3.Salazar Circuit \n 4.Isecheno Station \n 5.Lirhanda Hill \n 6.Yala River Border \n 7.Kibiri Block \n 8.Malava Edge \n 9.Ikuywa River East \n 10.Pump House Sector \n 11.Kaimosi Border \n 12.Mukumu West Gate \n 13.Cheenya Edge \n 14.Colobus Trail Inner"
    elif len(inputs) == 2:
        try:
            r_type = {"1":"Logging", "2":"Charcoal", "3":"Encroachment"}.get(inputs[0], "General")
            n_id = int(inputs[1])
            if 0 <= n_id <= 14:
                target = NODE_LOCATIONS[n_id]
                anon_id = hashlib.sha256(phone.encode()).hexdigest()[:8]
                
                # 1. Add to Blockchain Ledger
                prev = community_ledger.get_previous_block()
                data = {"issue": r_type, "loc": target['name'], "lat": target['lat'], "lng": target['lng'], "reporter": anon_id}
                community_ledger.create_block(100, community_ledger.hash(prev), data)
                
                # FIX 2: Register as a Main Alert Event
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                status_msg = f"Community Report: {r_type}"
                
                # Update Node State (So it shows in the Sidebar)
                node_states[n_id].update({ 
                    "status": status_msg, 
                    "probs": [0.0, 0.0, 0.0], # Irrelevant for manual report
                    "fire": False, 
                    "last_update": ts 
                })
                
                # Append to History (So it counts in Total Events & Charts)
                event_history.append({ 
                    "node_id": n_id, 
                    "time": ts, 
                    "status": "Community", # Simplified status for charting
                    "probs": [0.0, 0.0, 0.0], 
                    "fire": False 
                })
                
                response = f"END Report Filed. \nID: {anon_id} \nLocation: {target['name']}"
            else:
                response = "END Invalid Location Code"
        except:
            response = "END Error. Try again."
    else:
        response = "END Invalid"
    return response

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BUNDI | Command Center</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg-dark: #010b0e; --sidebar-bg: #03141a; --panel-glass: rgba(5, 26, 30, 0.85); 
            --border: rgba(45, 212, 191, 0.15); --text-main: #ccfbf1; --text-muted: #5eead4; 
            --accent: #2dd4bf; 
            --nat: #10b981; --unn: #f59e0b; --hum: #0ea5e9; --fire: #ef4444; 
            --comm: #a855f7; /* Purple for Community */
        }
        * { box-sizing: border-box; }
        body { margin: 0; font-family: 'Rajdhani', sans-serif; background: var(--bg-dark); color: var(--text-main); height: 100vh; overflow: hidden; }
        .app-container { display: flex; height: 100vh; width: 100vw; background-image: radial-gradient(circle at 50% 50%, #071f24 0%, #010b0e 80%); }
        
        /* SIDEBAR */
        .sidebar { width: 360px; background: var(--sidebar-bg); border-right: 1px solid var(--border); display: flex; flex-direction: column; z-index: 20; box-shadow: 5px 0 30px rgba(0,0,0,0.5); }
        .brand { padding: 25px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 15px; }
        .logo-svg { width: 40px; height: 40px; fill: var(--accent); filter: drop-shadow(0 0 5px var(--accent)); }
        
        .nav-tabs { display: flex; padding: 15px 25px; gap: 10px; border-bottom: 1px solid var(--border); }
        .nav-btn { flex: 1; background: rgba(45, 212, 191, 0.05); border: 1px solid var(--border); color: var(--text-muted); padding: 12px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9rem; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; }
        .nav-btn.active { background: var(--accent); color: #000; box-shadow: 0 0 20px rgba(45, 212, 191, 0.3); }
        
        .node-list { flex-grow: 1; overflow-y: auto; padding: 20px; }
        
        /* CARDS */
        .node-card { background: rgba(0,0,0,0.2); border-radius: 8px; padding: 15px; margin-bottom: 10px; border: 1px solid var(--border); border-left: 3px solid #333; cursor: pointer; transition: 0.2s; }
        .node-card:hover { transform: translateX(5px); border-color: var(--accent); }
        .node-card.selected { border: 1px solid var(--accent); background: rgba(45, 212, 191, 0.1); }
        
        .node-card.Fire { border-left-color: var(--fire); animation: pulse-card 1s infinite; }
        .node-card.Natural { border-left-color: var(--nat); }
        .node-card.Unnatural { border-left-color: var(--unn); }
        .node-card.Human { border-left-color: var(--hum); }
        /* Community Card Style */
        .node-card.Community { border-left-color: var(--comm); border-right: 1px solid var(--comm); }

        .card-top { display: flex; justify-content: space-between; font-weight: 700; font-size: 1rem; }
        .card-btm { font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }

        /* VIEWS */
        .main-view { flex-grow: 1; position: relative; }
        #view-map, #view-analytics { width: 100%; height: 100%; position: absolute; top: 0; left: 0; }
        #view-analytics { display: none; padding: 30px; overflow-y: auto; backdrop-filter: blur(10px); background: rgba(1, 11, 14, 0.6); }
        
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }
        .glass-panel { background: var(--panel-glass); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 4px 30px rgba(0,0,0,0.3); position: relative; }
        .big-number { font-size: 2.5rem; font-weight: 700; color: white; margin-top: 10px;}
        .sub-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
        .charts-row { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; height: 400px; }

        @keyframes pulse-card { 0% { background: rgba(239,68,68,0.1); } 50% { background: rgba(239,68,68,0.25); } 100% { background: rgba(239,68,68,0.1); } }
        .pin-wrapper { transition: transform 0.3s; filter: drop-shadow(0 0 5px rgba(0,0,0,0.5)); }
        .pin-wrapper:hover { transform: scale(1.3); z-index: 999; }
        .reset-btn { background: none; border: 1px solid var(--border); color: var(--text-muted); padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.7rem; font-family: inherit; }
        .reset-btn:hover { color: var(--accent); border-color: var(--accent); }
    </style>
</head>
<body>

<div class="app-container">
    <div class="sidebar">
        <div class="brand">
            <svg class="logo-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/><circle cx="8.5" cy="10.5" r="1.5"/><circle cx="15.5" cy="10.5" r="1.5"/><path d="M12 14l-1 1h2l-1-1z"/><path d="M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4" stroke="currentColor" stroke-width="1.5"/></svg>
            <div><h1 style="margin:0; font-size:1.4rem; letter-spacing:2px;">BUNDI</h1><div style="font-size: 0.7rem; color: var(--text-muted); letter-spacing: 1px;">ACOUSTIC SENTRY</div></div>
        </div>
        <div class="nav-tabs">
            <button class="nav-btn active" onclick="switchTab('map', this)">Monitor</button>
            <button class="nav-btn" onclick="switchTab('analytics', this)">Analysis</button>
        </div>
        <div style="padding: 15px 20px 0; display: flex; justify-content: space-between; align-items: center;">
            <span class="sub-label" style="font-size:0.7rem;">Active Nodes</span>
            <button class="reset-btn" onclick="resetFocus()">GLOBAL</button>
        </div>
        <div class="node-list" id="node-list-container">Loading...</div>
    </div>

    <div class="main-view">
        <div id="view-map"><div id="map" style="width:100%; height:100%;"></div></div>
        
        <div id="view-analytics">
            <div class="analytics-header">
                <div><h2 style="margin:0; font-size: 2rem; text-transform: uppercase;">Acoustic Telemetry</h2></div>
                <div class="focus-badge" id="analytics-focus-label">Focus: Global Network</div>
            </div>
            
            <div class="stats-grid">
                <div class="glass-panel">
                    <div class="sub-label">Health</div>
                    <div class="big-number" style="color: var(--nat);">100%</div>
                </div>
                <div class="glass-panel">
                    <div class="sub-label">Latest Threat</div>
                    <div class="big-number" id="stat-threat">Safe</div>
                </div>
                <div class="glass-panel">
                    <div class="sub-label">Total Events</div>
                    <div class="big-number" id="stat-events">0</div>
                </div>
                <div class="glass-panel" style="border-color: var(--unn);">
                    <div class="sub-label" style="color: var(--unn);">Hotspot Node</div>
                    <div class="big-number" id="stat-hotspot" style="font-size: 1.8rem;">--</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 5px;" id="stat-hotspot-score">Calculating...</div>
                </div>
            </div>

            <div class="charts-row">
                <div class="glass-panel">
                    <div class="sub-label" style="margin-bottom: 15px;">Precision Timeline (Winning Class)</div>
                    <div style="height: 320px; position: relative;"><canvas id="lineChart"></canvas></div>
                </div>
                <div class="glass-panel">
                    <div class="sub-label" style="margin-bottom: 15px;">Class Distribution</div>
                    <div style="height: 320px; position: relative;"><canvas id="doughnutChart"></canvas></div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    const colors = { Natural: '#10b981', Unnatural: '#f59e0b', Human: '#0ea5e9', Fire: '#ef4444', Community: '#a855f7' };
    var markers = {}, selectedNodeId = null, lineChart, doughChart, nodesData = {};

    const svgs = {
        Natural: `<svg viewBox="0 0 24 24" fill="${colors.Natural}" stroke="none"><path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66l.95-2.3c.48.17 1.05.23 1.63.09c-1.09-2.36-1.72-5.03-1.23-8.36c.39-2.67 2.17-4.89 4.54-5.42C13.32 5.62 15 6.5 17 8z"/></svg>`,
        Unnatural: `<svg viewBox="0 0 24 24" fill="${colors.Unnatural}" stroke="none"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/></svg>`,
        Human: `<svg viewBox="0 0 24 24" fill="${colors.Human}" stroke="none"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>`,
        Fire: `<svg viewBox="0 0 24 24" fill="${colors.Fire}" stroke="none"><path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73c-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14c0-1.62 1.05-2.76 2.81-3.12c1.77-.36 3.6-1.21 4.62-2.58c.39 1.29.59 2.65.59 4.04c0 2.65-2.15 4.8-4.8 4.8z"/></svg>`,
        Community: `<svg viewBox="0 0 24 24" fill="${colors.Community}" stroke="none"><path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/></svg>`
    };

    document.addEventListener("DOMContentLoaded", function() {
        initMap();
        initCharts();
        setInterval(fetchData, 1000);
        fetchData();
    });

    function initMap() {
        if(typeof L === 'undefined') return;
        map = L.map('map', {zoomControl: false}).setView([0.2827, 34.8647], 12);
        L.control.zoom({ position: 'topright' }).addTo(map);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: 'CARTO' }).addTo(map);
    }

    function initCharts() {
        if(typeof Chart === 'undefined') return;
        Chart.defaults.color = '#5eead4';
        Chart.defaults.borderColor = 'rgba(45, 212, 191, 0.1)';
        Chart.defaults.font.family = 'Rajdhani';

        lineChart = new Chart(document.getElementById('lineChart'), {
            type: 'line',
            data: { labels: [], datasets: [
                { label: 'Natural', data: [], borderColor: colors.Natural, backgroundColor: colors.Natural, tension: 0.4, spanGaps: true, pointRadius: 2 },
                { label: 'Unnatural', data: [], borderColor: colors.Unnatural, backgroundColor: colors.Unnatural, tension: 0.4, spanGaps: true, pointRadius: 2 },
                { label: 'Human', data: [], borderColor: colors.Human, backgroundColor: colors.Human, tension: 0.4, spanGaps: true, pointRadius: 2 },
                { label: 'Community', data: [], borderColor: colors.Community, backgroundColor: colors.Community, tension: 0.4, spanGaps: true, pointRadius: 2 }
            ]},
            options: { 
                responsive: true, maintainAspectRatio: false, 
                scales: { y: { beginAtZero: true, max: 1.0 }, x: { display: false } },
                plugins: { legend: { position: 'top', labels: { usePointStyle: true } } }
            }
        });

        doughChart = new Chart(document.getElementById('doughnutChart'), {
            type: 'doughnut',
            data: { labels: ['Natural','Unnatural','Human','Fire','Community'], datasets: [{ data: [1,0,0,0,0], backgroundColor: [colors.Natural, colors.Unnatural, colors.Human, colors.Fire, colors.Community], borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom' } } }
        });
    }

    async function fetchData() {
        try {
            const res = await fetch('/status');
            const data = await res.json();
            nodesData = data.nodes;
            updateUI(data.nodes);
            updateCharts(data.history);
            calculateHotspot(data.history);
        } catch (e) { console.error(e); }
    }

    function calculateHotspot(history) {
        let stats = {};
        history.forEach(h => {
            if (h.status === 'Natural' || h.status === 'Community') return;
            let nid = h.node_id;
            if (!stats[nid]) stats[nid] = { count: 0, sum: 0 };
            let prob = (h.status === 'Unnatural') ? h.probs[1] : h.probs[2];
            stats[nid].count++;
            stats[nid].sum += prob;
        });

        let maxScore = -1;
        let bestNodeId = null;
        for (const [nid, data] of Object.entries(stats)) {
            if (data.count === 0) continue;
            let score = data.count * (data.sum / data.count);
            if (score > maxScore) { maxScore = score; bestNodeId = nid; }
        }

        const hotspotEl = document.getElementById('stat-hotspot');
        const scoreEl = document.getElementById('stat-hotspot-score');
        if (bestNodeId !== null && nodesData[bestNodeId]) {
            hotspotEl.innerText = nodesData[bestNodeId].name;
            hotspotEl.style.color = colors.Unnatural;
            scoreEl.innerText = `Threat Score: ${maxScore.toFixed(2)}`;
        } else {
            hotspotEl.innerText = "None";
            hotspotEl.style.color = "#fff";
            scoreEl.innerText = "No significant activity";
        }
    }

    function updateUI(nodes) {
        const container = document.getElementById('node-list-container');
        let html = '';
        const sorted = Object.values(nodes).sort((a,b) => {
            // Sort by priority: Fire > Community > Unnatural > Human > Natural
            const rank = { 'Fire': 5, 'Community Report': 4, 'Unnatural': 3, 'Human Sound': 2, 'Natural': 1 };
            // Map status text (e.g., "Community Report: Logging") to generic key "Community Report"
            let aKey = a.status.includes('Community') ? 'Community Report' : a.status;
            let bKey = b.status.includes('Community') ? 'Community Report' : b.status;
            return (rank[bKey]||0) - (rank[aKey]||0);
        });

        sorted.forEach(n => {
            let statusTxt = n.fire ? '🔥 FIRE DETECTED' : n.status;
            let cls = n.fire ? 'Fire' : (n.status === 'Human Sound' ? 'Human' : (n.status.includes('Community') ? 'Community' : n.status));
            let sel = (selectedNodeId === n.id) ? 'selected' : '';
            
            html += `<div class="node-card ${cls} ${sel}" onclick="window.setFocus(${n.id}, ${n.lat}, ${n.lng})">
                <div class="card-top"><span>${n.name}</span><span>${statusTxt}</span></div>
                <div class="card-btm">Last Update: ${n.last_update}</div>
            </div>`;

            if(map) {
                let key = n.fire ? 'Fire' : (n.status === 'Human Sound' ? 'Human' : (n.status.includes('Community') ? 'Community' : (n.status === 'Unnatural' ? 'Unnatural' : 'Natural')));
                let svg = svgs[key];
                let color = n.fire ? colors.Fire : (key === 'Human' ? colors.Human : (key === 'Community' ? colors.Community : (key === 'Unnatural' ? colors.Unnatural : colors.Natural)));
                let pulse = (n.fire || key==='Community') ? 'animation: pulse-card 1s infinite;' : '';
                
                let icon = L.divIcon({ className: 'pin-wrapper', html: `<div style="width:30px; height:30px; filter: drop-shadow(0 0 8px ${color}); ${pulse}">${svg}</div>`, iconSize: [30, 30], iconAnchor: [15, 30] });

                if(markers[n.id]) markers[n.id].setIcon(icon);
                else markers[n.id] = L.marker([n.lat, n.lng], {icon:icon}).addTo(map).bindTooltip(n.name, { direction: 'top', offset: [0, -32], className: 'custom-tooltip' }).on('click', ()=>window.setFocus(n.id, n.lat, n.lng));
            }
        });
        container.innerHTML = html;
    }

    function updateCharts(history) {
        if(!lineChart || !doughChart) return;
        const relevant = selectedNodeId !== null ? history.filter(h => h.node_id === selectedNodeId) : history;
        
        // --- 1. Total Counts (Unlimited) ---
        let c = { Natural:0, Unnatural:0, Human:0, Fire:0, Community:0 };
        relevant.forEach(h => { 
            if(h.fire) c.Fire++; 
            else if(h.status === 'Natural') c.Natural++;
            else if(h.status === 'Unnatural') c.Unnatural++;
            else if(h.status === 'Human Sound') c.Human++;
            else if(h.status === 'Community') c.Community++;
        });
        
        document.getElementById('stat-events').innerText = relevant.length;
        doughChart.data.datasets[0].data = [c.Natural, c.Unnatural, c.Human, c.Fire, c.Community];
        doughChart.update('none');

        // --- 2. Timeline (Last 60 only) ---
        const recent = relevant.slice(-60);
        const last = recent.length ? recent[recent.length-1] : null;
        const threatEl = document.getElementById('stat-threat');
        
        if(last) {
            let label = last.fire ? "CRITICAL" : last.status;
            if(label === 'Community') label = "Verified Report";
            threatEl.innerText = label;
            
            let color = colors.Natural;
            if(last.fire) color = colors.Fire;
            else if(last.status === 'Unnatural') color = colors.Unnatural;
            else if(last.status === 'Human Sound') color = colors.Human;
            else if(last.status === 'Community') color = colors.Community;
            threatEl.style.color = color;
        }

        lineChart.data.labels = recent.map(h => h.time);
        lineChart.data.datasets[0].data = recent.map(h => h.status === 'Natural' ? h.probs[0] : null);
        lineChart.data.datasets[1].data = recent.map(h => h.status === 'Unnatural' ? h.probs[1] : null);
        lineChart.data.datasets[2].data = recent.map(h => h.status === 'Human Sound' ? h.probs[2] : null);
        lineChart.data.datasets[3].data = recent.map(h => h.status === 'Community' ? 1.0 : null); // Report = 100% confidence
        
        lineChart.update('none');
    }

    window.setFocus = function(id, lat, lng) {
        selectedNodeId = id;
        if(lat && lng && map) map.setView([lat, lng], 16);
        document.getElementById('analytics-focus-label').innerText = "Target: " + (nodesData[id] ? nodesData[id].name : "Node "+id);
        fetchData();
    }
    window.resetFocus = function() {
        selectedNodeId = null;
        if(map) map.setView([0.2827, 34.8647], 12);
        document.getElementById('analytics-focus-label').innerText = "Target: Global";
        fetchData();
    }
    window.switchTab = function(tab, btn) {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('view-map').style.display = (tab === 'map') ? 'block' : 'none';
        document.getElementById('view-analytics').style.display = (tab === 'analytics') ? 'block' : 'none';
        if(tab === 'analytics') setTimeout(() => { lineChart.resize(); doughChart.resize(); }, 100);
    }
</script>
</body>
</html>
