/**
 * Traffic Sentinel - Dashboard JavaScript
 * Handles interactivity for the MVP frontend
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set default active section
    showSection('dashboard');

    // Add current date/time
    updateLiveTime();
    setInterval(updateLiveTime, 60000); // Update every minute

    loadDashboardStats(); // Initial load of real data
});

// Show/Hide sections
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const activeSection = document.getElementById(sectionName + '-section');
    if (activeSection) {
        activeSection.classList.add('active');
    }
}

// Live time updater (Uganda time awareness)
function updateLiveTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
    
    const dateString = now.toLocaleDateString('en-GB', {
        weekday: 'short',
        day: 'numeric',
        month: 'short'
    });
    
    // You can add this element to index.html later if needed
    console.log(`Current Kampala Time: ${dateString} ${timeString}`);
}

// Run Video Processing (connects to backend API)
async function runVideoProcessing() {
    const resultsBox = document.getElementById('video-results');
    resultsBox.innerHTML = `<p><strong>Processing videos... (this runs in background)</strong></p>`;

    try {
        const response = await fetch('http://localhost:8000/api/pipeline', { method: 'POST' });
        const data = await response.json();
        resultsBox.innerHTML = `<p><strong>Pipeline started!</strong> Check status or refresh dashboard.</p>`;
        
        // Poll status briefly then load dashboard
        setTimeout(() => loadDashboardStats(), 3000);
    } catch (e) {
        resultsBox.innerHTML = `<p>Error: ${e.message}. Make sure backend is running.</p>`;
    }
}

// Core function to load real stats from backend
async function loadDashboardStats() {
    try {
        // Fetch processed results
        const resResponse = await fetch('http://localhost:8000/api/results');
        const resultsData = await resResponse.json();

        // Fetch predictions
        const predResponse = await fetch('http://localhost:8000/api/predictions');
        const predData = await predResponse.json().catch(() => ({}));

        // Aggregate stats
        let totalVehicles = 0;
        let peakVehicles = 0;

        if (resultsData.results && resultsData.results.length > 0) {
            resultsData.results.forEach(result => {
                if (result.avg_vehicles_per_sample) {
                    totalVehicles += result.avg_vehicles_per_sample * 10; // rough estimate
                }
                if (result.peak_vehicles > peakVehicles) {
                    peakVehicles = result.peak_vehicles;
                }
            });

            // Update stat card DOM elements
            updateStatCard('vehicles-detected', Math.round(totalVehicles).toLocaleString());
            updateStatCard('peak-vehicles', peakVehicles);

            // Update chart placeholder content if data is available
            const chartContent = document.getElementById('chart-content');
            if (chartContent) {
                chartContent.textContent = `Data loaded: ${resultsData.count} video(s) processed.`;
            }
        }

        // Update risk level from predictions if available
        if (predData && predData.summary) {
            const summary = predData.summary;
            const riskEl = document.getElementById('risk-level');
            const riskDesc = document.getElementById('risk-desc');
            if (riskEl && summary.overall_risk_level) {
                riskEl.textContent = summary.overall_risk_level.toUpperCase();
                riskEl.className = `risk-${summary.overall_risk_level.toLowerCase()}`;
            }
            if (riskDesc && summary.peak_risk_period) {
                riskDesc.textContent = `Peak: ${summary.peak_risk_period}`;
            }
        }

        console.log("✅ Dashboard updated with real data", resultsData);
    } catch (error) {
        console.error("Failed to load stats:", error);
        // Gracefully leave default demo values in place
    }
}

// Helper: update a stat card element by ID
function updateStatCard(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === "1") showSection('dashboard');
    if (e.key === "2") showSection('videos');
    if (e.key === "3") showSection('hotspots');
});

// Make functions available globally
window.showSection = showSection;
window.runVideoProcessing = runVideoProcessing;
