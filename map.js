// Leaflet Map Controller for Cognitive Digital Twin

let map = null;
let heatmapLayer = null;
let incidentMarkersGroup = null;
let zonesLayerGroup = null;
let clustersLayerGroup = null;
let patrolRouteLayerGroup = null;

function initCrimeMap(centerLat, centerLon, zoomLevel = 12) {
    if (map) {
        map.remove();
        map = null;
    }

    map = L.map('crimeMap').setView([centerLat, centerLon], zoomLevel);

    // Create elevated panes so Patrol Routes & DBSCAN Centroids stay cleanly on top of zone circles
    map.createPane('patrolPane');
    map.getPane('patrolPane').style.zIndex = 620;

    map.createPane('centroidPane');
    map.getPane('centroidPane').style.zIndex = 640;

    // Clean OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '© OpenStreetMap contributors | Cognitive Digital Twin'
    }).addTo(map);

    // All 4 layer groups active by default so all 5 Legend elements show immediately
    zonesLayerGroup = L.layerGroup().addTo(map);
    incidentMarkersGroup = L.layerGroup().addTo(map);
    patrolRouteLayerGroup = L.layerGroup().addTo(map);
    clustersLayerGroup = L.layerGroup().addTo(map);

    // Add custom layer control
    const overlayMaps = {
        "Hotspot Zones (High / Med / Low)": zonesLayerGroup,
        "Individual Crime Markers": incidentMarkersGroup,
        "DBSCAN Cluster Centroids": clustersLayerGroup,
        "Optimized Patrol Route": patrolRouteLayerGroup
    };
    L.control.layers(null, overlayMaps, { position: 'topright' }).addTo(map);
}

function renderZonesOnMap(zones) {
    if (!zonesLayerGroup) return;
    zonesLayerGroup.clearLayers();

    zones.forEach(zone => {
        const color = zone.risk_level === 'High' ? '#E11D48' : (zone.risk_level === 'Medium' ? '#F59E0B' : '#10B981');

        const circle = L.circle([zone.lat, zone.lon], {
            color: color,
            fillColor: color,
            fillOpacity: 0.30,
            weight: 2,
            radius: 800 + (zone.incident_count * 8)
        });

        const popupContent = `
            <div style="font-family: inherit; min-width: 180px;">
                <h6 style="margin: 0 0 6px 0; font-weight: bold; color: #3B103F;">${zone.area_name}</h6>
                <div style="margin-bottom: 4px;">
                    <span class="badge" style="background-color: ${color}; color: white;">${zone.risk_level} Risk (${zone.risk_score}/100)</span>
                </div>
                <div style="font-size: 0.8rem; color: #475569; line-height: 1.4;">
                    <div><b>Incidents:</b> ${zone.incident_count} records</div>
                    <div><b>Top Offense:</b> ${zone.top_crime_type}</div>
                    <div><b>Avg Daily Freq:</b> ${zone.avg_frequency}</div>
                </div>
                <div style="margin-top: 8px;">
                    <button class="btn btn-sm btn-plum py-1 px-2 text-white" onclick="filterByArea('${zone.area_name}')" style="font-size: 0.75rem;">
                        <i class="fa-solid fa-filter me-1"></i> View Incidents
                    </button>
                </div>
            </div>
        `;

        circle.bindPopup(popupContent);
        zonesLayerGroup.addLayer(circle);
    });
}

function renderIncidentMarkers(records) {
    if (!incidentMarkersGroup) return;
    incidentMarkersGroup.clearLayers();

    const heatPoints = [];

    // Render up to 300 markers for performance
    records.slice(0, 300).forEach(r => {
        const lat = parseFloat(r.latitude);
        const lon = parseFloat(r.longitude);
        if (isNaN(lat) || isNaN(lon)) return;

        const risk = r.proposed_prediction || r.actual_risk_level;
        const color = risk === 'High' ? '#E11D48' : (risk === 'Medium' ? '#F59E0B' : '#10B981');

        heatPoints.push([lat, lon, risk === 'High' ? 0.9 : (risk === 'Medium' ? 0.5 : 0.2)]);

        const marker = L.circleMarker([lat, lon], {
            radius: 4.5,
            fillColor: color,
            color: '#FFFFFF',
            weight: 1.5,
            opacity: 1,
            fillOpacity: 0.85
        });

        const popupHtml = `
            <div style="font-family: inherit; font-size: 0.82rem;">
                <div style="font-weight: bold; color: #3B103F; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin-bottom: 4px;">
                    ${r.crime_type} — ${r.area_name}
                </div>
                <div><b>Date & Time:</b> ${r.date} ${r.time}</div>
                <div><b>Location Type:</b> ${r.location_category}</div>
                <div><b>Actual Label:</b> <span class="badge" style="background:#E2E8F0; color:#1E293B;">${r.actual_risk_level}</span></div>
                <div><b>Proposed CDT:</b> <span class="badge" style="background:${color}; color:white;">${r.proposed_prediction}</span> (${r.proposed_confidence_pct}%)</div>
                <div><b>Classification:</b> ${r.proposed_correct === '✅' ? '✅ Correct' : '❌ Misclassified'}</div>
                <div style="margin-top: 8px;">
                    <button class="btn btn-sm btn-outline-rose py-1 px-2" onclick="explainRecord(${r.record_index})" style="font-size: 0.75rem;">
                        <i class="fa-solid fa-wand-magic-sparkles me-1"></i> Explain with SHAP
                    </button>
                </div>
            </div>
        `;
        marker.bindPopup(popupHtml);
        incidentMarkersGroup.addLayer(marker);
    });

    // Add or update heatmap
    if (heatmapLayer && map.hasLayer(heatmapLayer)) {
        map.removeLayer(heatmapLayer);
    }
    if (heatPoints.length > 0 && typeof L.heatLayer === 'function') {
        heatmapLayer = L.heatLayer(heatPoints, {
            radius: 25,
            blur: 18,
            maxZoom: 16,
            gradient: { 0.2: '#10B981', 0.5: '#F59E0B', 0.8: '#E11D48', 1.0: '#991B1B' }
        }).addTo(map);
    }
}

function renderClustersOnMap(clustersData) {
    if (!clustersLayerGroup) return;
    clustersLayerGroup.clearLayers();

    // DBSCAN Cluster Centroids (Purple #7C3AED matching Map Legend)
    if (clustersData && clustersData.dbscan) {
        clustersData.dbscan.forEach(c => {
            if (c.is_noise) return; // Only plot valid cluster centroids

            const areaLabel = c.nearby_area ? ` (${c.nearby_area})` : '';
            const shortTag = `C${(c.label !== undefined ? c.label + 1 : '')}`;

            // Outer purple halo ring
            const halo = L.circleMarker([c.center_lat, c.center_lon], {
                pane: 'centroidPane',
                radius: 18,
                fillColor: '#8B5CF6',
                color: '#7C3AED',
                weight: 2.5,
                fillOpacity: 0.28,
                dashArray: '4, 4'
            });

            // High-visibility labeled purple centroid marker
            const centroidIcon = L.divIcon({
                className: 'dbscan-centroid-icon',
                html: `<div style="
                    width: 26px; height: 26px; border-radius: 50%;
                    background: #7C3AED; color: #FFFFFF;
                    border: 2.5px solid #FFFFFF;
                    box-shadow: 0 2px 8px rgba(124, 58, 237, 0.75);
                    display: flex; align-items: center; justify-content: center;
                    font-size: 10px; font-weight: 800; letter-spacing: -0.3px;
                ">${shortTag}</div>`,
                iconSize: [26, 26],
                iconAnchor: [13, 13]
            });

            const centroid = L.marker([c.center_lat, c.center_lon], {
                pane: 'centroidPane',
                icon: centroidIcon
            });

            const popupHtml = `
                <div style="font-family: inherit; min-width: 210px; padding: 2px;">
                    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px; border-bottom: 1px solid #EDE9FE; padding-bottom: 4px;">
                        <span style="display: inline-block; width: 12px; height: 12px; background: #7C3AED; border-radius: 3px;"></span>
                        <b style="color: #4C1D95; font-size: 0.92rem;">DBSCAN Cluster Centroid</b>
                    </div>
                    <div style="font-size: 0.82rem; color: #334155; line-height: 1.5;">
                        <div><b>Cluster ID:</b> ${c.cluster_id}${areaLabel}</div>
                        <div><b>Incident Density:</b> <span class="badge" style="background:#7C3AED; color:white;">${c.incident_count} events</span></div>
                        <div><b>Coordinates:</b> <code>${c.center_lat.toFixed(4)}, ${c.center_lon.toFixed(4)}</code></div>
                        <div class="mt-1" style="font-size: 0.75rem; color: #6D28D9;"><i>Spatial-Density Centroid (DBSCAN)</i></div>
                    </div>
                </div>
            `;

            halo.bindPopup(popupHtml);
            centroid.bindPopup(popupHtml);
            centroid.bindTooltip(`DBSCAN Centroid: ${c.cluster_id}${areaLabel}`, {
                permanent: false,
                direction: 'top'
            });

            clustersLayerGroup.addLayer(halo);
            clustersLayerGroup.addLayer(centroid);
        });
    }

    if (map && !map.hasLayer(clustersLayerGroup)) {
        clustersLayerGroup.addTo(map);
    }
}

function renderPatrolRouteOnMap(routeData, shouldFit = false) {
    if (!patrolRouteLayerGroup) return;
    patrolRouteLayerGroup.clearLayers();

    if (!routeData || !routeData.route_waypoints || routeData.route_waypoints.length === 0) return;

    const latlngs = routeData.route_waypoints.map(w => [w.lat, w.lon]);

    // Subtle white casing underneath so dashed pink route pops over colored zones
    const casing = L.polyline(latlngs, {
        pane: 'patrolPane',
        color: '#FFFFFF',
        weight: 7,
        opacity: 0.65,
        dashArray: '10, 8'
    });
    patrolRouteLayerGroup.addLayer(casing);

    // Primary dashed pink patrol route polyline (#D83B6F matching Map Legend)
    const polyline = L.polyline(latlngs, {
        pane: 'patrolPane',
        color: '#D83B6F',
        weight: 4.5,
        opacity: 0.95,
        dashArray: '10, 8'
    });
    patrolRouteLayerGroup.addLayer(polyline);

    // Numbered patrol stop waypoint badges
    routeData.route_waypoints.forEach(w => {
        const stopIcon = L.divIcon({
            className: 'patrol-stop-icon',
            html: `<div style="
                width: 22px; height: 22px; border-radius: 50%;
                background: #D83B6F; color: #FFFFFF;
                border: 2px solid #FFFFFF;
                box-shadow: 0 2px 6px rgba(216, 59, 111, 0.7);
                display: flex; align-items: center; justify-content: center;
                font-size: 10px; font-weight: 800;
            ">${w.stop_number}</div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11]
        });

        const marker = L.marker([w.lat, w.lon], {
            pane: 'patrolPane',
            icon: stopIcon
        });

        marker.bindPopup(`
            <div style="font-family: inherit; min-width: 195px; padding: 2px;">
                <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px; border-bottom: 1px solid #FCE7ED; padding-bottom: 4px;">
                    <span style="display: inline-block; padding: 2px 6px; background: #D83B6F; color: white; border-radius: 4px; font-weight: bold; font-size: 0.72rem;">Stop ${w.stop_number}</span>
                    <b style="color: #3B103F; font-size: 0.88rem;">${w.area_name}</b>
                </div>
                <div style="font-size: 0.82rem; color: #334155; line-height: 1.4;">
                    <div><b>Patrol Priority:</b> ${w.priority}</div>
                    <div><b>Hotspot Risk:</b> <span class="badge" style="background:#E11D48; color:white;">${w.risk_score}/100 (${w.risk_level})</span></div>
                    <div class="mt-1" style="font-size: 0.75rem; color: #BE185D;"><i>Optimized Patrol Route Waypoint</i></div>
                </div>
            </div>
        `);

        marker.bindTooltip(`Patrol Stop ${w.stop_number}: ${w.area_name}`, {
            permanent: false,
            direction: 'bottom'
        });

        patrolRouteLayerGroup.addLayer(marker);
    });

    if (map && !map.hasLayer(patrolRouteLayerGroup)) {
        patrolRouteLayerGroup.addTo(map);
    }

    if (shouldFit && map) {
        map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    }
}
