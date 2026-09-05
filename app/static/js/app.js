// FarmTwin Main Application Orchestrator

let appState = {
    presets: [],
    currentFarm: null,
    currentZone: null,
    simulationData: null,
    activeDayIndex: 0,
    isPlaying: false,
    playInterval: null,
    cropsMetadata: {},
    soilsMetadata: {}
};

// Global accessor helpers
window.getCurrentZone = () => appState.currentZone;
window.getCurrentSimulation = () => appState.simulationData;

document.addEventListener('DOMContentLoaded', async () => {
    console.log("🌱 Initializing FarmTwin Digital Twin...");
    await loadMetadata();
    await loadPresets();
    setupEventListeners();
});

async function loadMetadata() {
    try {
        const [cropsResp, soilsResp] = await Promise.all([
            fetch('/api/farm/crops'),
            fetch('/api/farm/soils')
        ]);
        if (cropsResp.ok) appState.cropsMetadata = await cropsResp.json();
        if (soilsResp.ok) appState.soilsMetadata = await soilsResp.json();
    } catch (err) {
        console.error("Failed to load metadata:", err);
    }
}

async function loadPresets() {
    try {
        const resp = await fetch('/api/farm/presets');
        if (!resp.ok) throw new Error("Could not load presets");
        appState.presets = await resp.json();

        // Populate preset selector dropdown
        const select = document.getElementById('preset-select');
        select.innerHTML = '';
        appState.presets.forEach((farm, idx) => {
            const opt = document.createElement('option');
            opt.value = farm.id;
            opt.textContent = `${farm.name} (${farm.location_name})`;
            select.appendChild(opt);
        });

        // Select first preset by default
        if (appState.presets.length > 0) {
            selectFarm(appState.presets[0].id);
        }
    } catch (err) {
        console.error("Error loading presets:", err);
    }
}

function selectFarm(farmId) {
    const farm = appState.presets.find(f => f.id === farmId);
    if (!farm) return;

    appState.currentFarm = farm;

    // Update location header badge
    const locBadge = document.getElementById('farm-location-badge');
    if (locBadge) locBadge.textContent = farm.location_name;

    // Initialize/fly Leaflet map to farm center
    initFarmMap(farm.latitude, farm.longitude);

    // Populate zone list chips
    renderZonePills(farm.zones);

    // Select first zone
    if (farm.zones.length > 0) {
        selectZone(farm.zones[0].id);
    }
}

function renderZonePills(zones) {
    const container = document.getElementById('zone-pills-container');
    if (!container) return;

    container.innerHTML = '';
    zones.forEach(zone => {
        const btn = document.createElement('button');
        btn.id = `zone-pill-${zone.id}`;
        btn.className = `px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center space-x-1.5 bg-slate-800/80 border border-slate-700/60 text-slate-300 hover:border-emerald-500/50`;
        btn.innerHTML = `
            <span class="w-2 h-2 rounded-full" style="background-color: ${getCropColor(zone.crop)}"></span>
            <span>${zone.name}</span>
        `;
        btn.onclick = () => selectZone(zone.id);
        container.appendChild(btn);
    });
}

function getCropColor(cropKey) {
    if (appState.cropsMetadata && appState.cropsMetadata[cropKey]) {
        return appState.cropsMetadata[cropKey].color || '#10b981';
    }
    return '#10b981';
}

async function selectZone(zoneId) {
    if (!appState.currentFarm) return;
    const zone = appState.currentFarm.zones.find(z => z.id === zoneId);
    if (!zone) return;

    appState.currentZone = zone;

    // Update active pill UI
    appState.currentFarm.zones.forEach(z => {
        const pill = document.getElementById(`zone-pill-${z.id}`);
        if (pill) {
            if (z.id === zoneId) {
                pill.className = `px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center space-x-1.5 bg-emerald-500/20 border border-emerald-500 text-emerald-300 shadow-sm shadow-emerald-500/10`;
            } else {
                pill.className = `px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center space-x-1.5 bg-slate-800/80 border border-slate-700/60 text-slate-300 hover:border-emerald-500/50`;
            }
        }
    });

    // Update Zone Info Card
    document.getElementById('zone-name-display').textContent = zone.name;
    document.getElementById('zone-crop-display').textContent = zone.crop.toUpperCase();
    document.getElementById('zone-soil-display').textContent = zone.soil.replace('_', ' ').toUpperCase();
    document.getElementById('zone-acres-display').textContent = `${zone.area_acres} Acres`;
    document.getElementById('zone-irrigation-display').textContent = zone.irrigation_type.toUpperCase();

    // Trigger 14-day Simulation
    await executeSimulation(zone);
}

window.selectZone = selectZone;

async function executeSimulation(zone) {
    const spinner = document.getElementById('simulation-loading');
    if (spinner) spinner.classList.remove('hidden');

    try {
        const payload = {
            latitude: appState.currentFarm.latitude,
            longitude: appState.currentFarm.longitude,
            zone_id: zone.id,
            zone_name: zone.name,
            crop: zone.crop,
            soil: zone.soil,
            area_acres: zone.area_acres,
            growth_stage: zone.growth_stage || "mid",
            initial_depletion_fraction: 0.25
        };

        const resp = await fetch('/api/simulation/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) throw new Error("Simulation execution failed");
        const simData = await resp.json();
        appState.simulationData = simData;

        // Render polygons with current stress colors
        const simStatusMap = { [zone.id]: simData.daily_results[0] };
        renderZonePolygons(appState.currentFarm.zones, simStatusMap, zone.id);

        // Reset timeline scrubber to day 0
        appState.activeDayIndex = 0;
        const slider = document.getElementById('timeline-slider');
        if (slider) slider.value = 0;

        // Render Telemetry & Charts
        renderTelemetry(0);

        const soilProp = appState.soilsMetadata[zone.soil] || { fc: 0.28, wp: 0.14 };
        renderTelemetryChart(simData.daily_results, soilProp.fc * 100, soilProp.wp * 100);

        // Fetch & render agronomic risks
        fetchAndRenderRisks(simData, zone);

        // Auto calculate default irrigation prescription
        calculatePrescription();

    } catch (err) {
        console.error("Simulation error:", err);
    } finally {
        if (spinner) spinner.classList.add('hidden');
    }
}

function renderTelemetry(dayIndex) {
    if (!appState.simulationData) return;
    const day = appState.simulationData.daily_results[dayIndex];
    if (!day) return;

    // Update timeline day indicator
    document.getElementById('active-timeline-date').textContent = `${day.date} (Day +${dayIndex})`;

    // Soil Moisture Progress & Value
    const moistVal = document.getElementById('metric-moisture');
    const moistBar = document.getElementById('metric-moisture-bar');
    if (moistVal) moistVal.textContent = `${day.soil_moisture_pct}%`;
    if (moistBar) moistBar.style.width = `${Math.min(100, (day.soil_moisture_pct / 45) * 100)}%`;

    // Status Badge
    const statusBadge = document.getElementById('metric-status-badge');
    if (statusBadge) {
        statusBadge.textContent = day.stress_status.replace('_', ' ');
        statusBadge.className = `text-xs px-2.5 py-1 rounded-full font-semibold `;
        if (day.stress_status === 'OPTIMAL') statusBadge.className += 'badge-optimal';
        else if (day.stress_status === 'MILD_STRESS') statusBadge.className += 'badge-mild';
        else if (day.stress_status === 'CRITICAL_DROUGHT') statusBadge.className += 'badge-critical';
        else if (day.stress_status === 'WATERLOGGED') statusBadge.className += 'badge-waterlogged';
    }

    // Root Zone Depletion (Dr / RAW)
    document.getElementById('metric-dr').textContent = `${day.root_zone_depletion_mm} mm`;
    document.getElementById('metric-raw').textContent = `RAW: ${day.raw_mm} mm (TAW: ${day.taw_mm} mm)`;

    // ETc & ET0
    document.getElementById('metric-etc').textContent = `${day.etc_mm} mm/d`;
    document.getElementById('metric-et0').textContent = `Ref ET0: ${day.et0_mm} mm/d (Kc: ${day.kc})`;

    // Simulated NDVI
    document.getElementById('metric-ndvi').textContent = day.simulated_ndvi.toFixed(2);

    // Weather params (Temp & VPD)
    document.getElementById('metric-temp').textContent = `${day.temperature_c}°C`;
    document.getElementById('metric-vpd').textContent = `${day.vpd_kpa} kPa`;
    document.getElementById('metric-rain').textContent = `${day.precipitation_mm} mm`;

    // Update polygon color on map
    if (appState.currentZone) {
        updateZoneVisualStatus(appState.currentZone.id, day.stress_status);
    }
}

async function fetchAndRenderRisks(simData, zone) {
    try {
        const resp = await fetch('/api/advisor/risks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                crop: zone.crop,
                soil: zone.soil,
                simulation: simData
            })
        });

        if (!resp.ok) return;
        const risks = await resp.json();
        const container = document.getElementById('risks-container');
        if (!container) return;

        container.innerHTML = '';
        if (risks.length === 0) {
            container.innerHTML = `
                <div class="text-xs text-emerald-400/80 bg-emerald-950/20 border border-emerald-500/20 rounded-lg p-3 flex items-center space-x-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <span>No critical pathogen or drought stress alarms detected over the 14-day window.</span>
                </div>
            `;
            return;
        }

        risks.forEach(risk => {
            const isCrit = risk.severity === 'CRITICAL';
            const card = document.createElement('div');
            card.className = `text-xs rounded-xl p-3 border transition-all ${
                isCrit 
                ? 'bg-red-950/20 border-red-500/40 text-red-200' 
                : 'bg-amber-950/20 border-amber-500/40 text-amber-200'
            }`;
            card.innerHTML = `
                <div class="flex items-center justify-between font-semibold mb-1">
                    <span class="${isCrit ? 'text-red-400' : 'text-amber-400'}">${risk.title}</span>
                    <span class="text-[10px] uppercase px-1.5 py-0.5 rounded ${isCrit ? 'bg-red-500/20' : 'bg-amber-500/20'}">${risk.severity}</span>
                </div>
                <div class="text-slate-300 text-[11px] mb-2">${risk.description}</div>
                <div class="text-[11px] pt-1.5 border-t border-slate-700/40 text-emerald-300 font-medium">
                    ⚡ Remediation: ${risk.remediation}
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Risk assessment error:", err);
    }
}

async function calculatePrescription() {
    if (!appState.simulationData || !appState.currentZone) return;

    const curDay = appState.simulationData.daily_results[appState.activeDayIndex];
    const deficitLiters = curDay.deficit_liters_per_acre * appState.currentZone.area_acres;

    try {
        const payload = {
            zone_id: appState.currentZone.id,
            water_deficit_liters: Math.max(1000.0, deficitLiters),
            area_acres: appState.currentZone.area_acres,
            irrigation_type: appState.currentZone.irrigation_type || "drip",
            pump_flow_rate_lpm: 350.0,
            electricity_cost_kwh: 0.14,
            pump_power_kw: 7.5
        };

        const resp = await fetch('/api/prescription/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) return;
        const presc = await resp.json();

        document.getElementById('presc-water-liters').textContent = `${presc.recommended_water_liters.toLocaleString()} L`;
        document.getElementById('presc-water-gallons').textContent = `(${presc.recommended_water_gallons.toLocaleString()} gal)`;
        document.getElementById('presc-runtime').textContent = `${presc.pump_runtime_hours} hrs (${presc.pump_runtime_minutes} min)`;
        document.getElementById('presc-efficiency').textContent = `${presc.irrigation_efficiency_pct}% Delivery`;
        document.getElementById('presc-cost').textContent = `$${presc.estimated_energy_cost.toFixed(2)}`;

        const schedDiv = document.getElementById('presc-schedule');
        if (schedDiv && presc.schedule_breakdown) {
            schedDiv.innerHTML = presc.schedule_breakdown.map(p => `
                <div class="flex items-center justify-between text-[11px] bg-slate-900/60 px-2.5 py-1.5 rounded border border-slate-800">
                    <span class="text-slate-300 font-medium">${p.pulse} (${p.start_time})</span>
                    <span class="text-emerald-400 font-mono">${p.duration_hours}h &middot; ${p.volume_liters.toLocaleString()} L</span>
                </div>
            `).join('');
        }
    } catch (err) {
        console.error("Prescription error:", err);
    }
}

function setupEventListeners() {
    // Preset dropdown
    const presetSelect = document.getElementById('preset-select');
    if (presetSelect) {
        presetSelect.onchange = (e) => selectFarm(e.target.value);
    }

    // Timeline slider
    const slider = document.getElementById('timeline-slider');
    if (slider) {
        slider.oninput = (e) => {
            appState.activeDayIndex = parseInt(e.target.value);
            renderTelemetry(appState.activeDayIndex);
            calculatePrescription();
        };
    }

    // Play/Pause simulation animation
    const playBtn = document.getElementById('btn-play-sim');
    if (playBtn) {
        playBtn.onclick = () => {
            if (appState.isPlaying) {
                clearInterval(appState.playInterval);
                appState.isPlaying = false;
                playBtn.innerHTML = `<span>▶</span><span>Play Forecast</span>`;
            } else {
                appState.isPlaying = true;
                playBtn.innerHTML = `<span>⏸</span><span>Pause</span>`;
                appState.playInterval = setInterval(() => {
                    let nextDay = (appState.activeDayIndex + 1) % 14;
                    appState.activeDayIndex = nextDay;
                    slider.value = nextDay;
                    renderTelemetry(nextDay);
                    if (nextDay === 13) {
                        clearInterval(appState.playInterval);
                        appState.isPlaying = false;
                        playBtn.innerHTML = `<span>▶</span><span>Replay Forecast</span>`;
                    }
                }, 1200);
            }
        };
    }

    // AI Advisor toggle
    const advisorBtn = document.getElementById('btn-open-advisor');
    if (advisorBtn) advisorBtn.onclick = openAdvisorDrawer;

    const closeBtn = document.getElementById('btn-close-advisor');
    if (closeBtn) closeBtn.onclick = closeAdvisorDrawer;

    const advisorSend = document.getElementById('advisor-send');
    if (advisorSend) advisorSend.onclick = submitAdvisorMessage;

    const advisorInput = document.getElementById('advisor-input');
    if (advisorInput) {
        advisorInput.onkeydown = (e) => {
            if (e.key === 'Enter') submitAdvisorMessage();
        };
    }
}
