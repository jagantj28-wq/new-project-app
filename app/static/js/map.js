// FarmTwin Leaflet Map Controller
let farmMap = null;
let zonePolygonLayers = {};
let activeZoneId = null;

function initFarmMap(centerLat, centerLng, zoomLevel = 15) {
    if (farmMap) {
        farmMap.remove();
    }

    farmMap = L.map('farm-map', {
        zoomControl: false,
        attributionControl: false
    }).setView([centerLat, centerLng], zoomLevel);

    // Zoom control at bottom right
    L.control.zoom({ position: 'bottomright' }).addTo(farmMap);

    // Esri World Imagery (High-Resolution Satellite)
    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }).addTo(farmMap);

    // CartoDB Dark Matter Labels / Reference overlay
    const labelsLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd'
    }).addTo(farmMap);

    return farmMap;
}

function renderZonePolygons(zones, currentSimulationData = null, selectedZoneId = null) {
    // Clear existing polygon layers
    Object.values(zonePolygonLayers).forEach(layer => {
        if (farmMap.hasLayer(layer)) {
            farmMap.removeLayer(layer);
        }
    });
    zonePolygonLayers = {};

    zones.forEach(zone => {
        if (!zone.coordinates || zone.coordinates.length < 3) return;

        // Determine polygon color based on simulation state
        let fillColor = '#10b981'; // default emerald
        let fillOpacity = 0.45;
        let strokeColor = '#34d399';

        if (currentSimulationData && currentSimulationData[zone.id]) {
            const status = currentSimulationData[zone.id].stress_status;
            if (status === 'CRITICAL_DROUGHT') {
                fillColor = '#ef4444';
                strokeColor = '#f87171';
                fillOpacity = 0.65;
            } else if (status === 'MILD_STRESS') {
                fillColor = '#f59e0b';
                strokeColor = '#fbbf24';
                fillOpacity = 0.55;
            } else if (status === 'WATERLOGGED') {
                fillColor = '#3b82f6';
                strokeColor = '#60a5fa';
                fillOpacity = 0.55;
            }
        }

        const isSelected = zone.id === selectedZoneId;
        const weight = isSelected ? 4 : 2;

        const polygon = L.polygon(zone.coordinates, {
            color: strokeColor,
            weight: weight,
            fillColor: fillColor,
            fillOpacity: fillOpacity,
            dashArray: isSelected ? null : '4, 4'
        }).addTo(farmMap);

        // Tooltip
        polygon.bindTooltip(`
            <div class="font-sans text-xs">
                <div class="font-bold text-emerald-400">${zone.name}</div>
                <div class="text-slate-300">Crop: ${zone.crop.toUpperCase()} | Area: ${zone.area_acres} ac</div>
            </div>
        `, { sticky: true, className: 'custom-leaflet-tooltip' });

        polygon.on('click', () => {
            window.selectZone(zone.id);
        });

        zonePolygonLayers[zone.id] = polygon;
    });

    // Fit map bounds if zones exist
    const allCoords = zones.flatMap(z => z.coordinates || []);
    if (allCoords.length > 0) {
        const bounds = L.latLngBounds(allCoords);
        farmMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
    }
}

function updateZoneVisualStatus(zoneId, stressStatus) {
    const layer = zonePolygonLayers[zoneId];
    if (!layer) return;

    let fillColor = '#10b981';
    let strokeColor = '#34d399';

    if (stressStatus === 'CRITICAL_DROUGHT') {
        fillColor = '#ef4444';
        strokeColor = '#f87171';
    } else if (stressStatus === 'MILD_STRESS') {
        fillColor = '#f59e0b';
        strokeColor = '#fbbf24';
    } else if (stressStatus === 'WATERLOGGED') {
        fillColor = '#3b82f6';
        strokeColor = '#60a5fa';
    }

    layer.setStyle({
        fillColor: fillColor,
        color: strokeColor
    });
}
