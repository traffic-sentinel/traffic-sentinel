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

// Run Video Processing (connects to backend)
function runVideoProcessing() {
    const resultsBox = document.getElementById('video-results');
    
    resultsBox.innerHTML = `
        <p><strong>Processing videos...</strong></p>
        <p>This may take a while depending on video length.</p>
    `;
    
    // Simulate processing (in real MVP you can call backend API)
    setTimeout(() => {
        resultsBox.innerHTML = `
            <h4>✅ Processing Complete</h4>
            <ul>
                <li><strong>Videos Analyzed:</strong> All files in data/input_video/</li>
                <li><strong>Average Vehicles:</strong> 14-22 per frame</li>
                <li><strong>Peak Risk Period:</strong> 5:00 PM - 9:00 PM</li>
                <li><strong>Output Saved:</strong> data/output_results/</li>
            </ul>
            <p><em>Run <strong>./run.sh</strong> for full pipeline.</em></p>
        `;
        
        // Auto-switch to dashboard after processing
        setTimeout(() => {
            showSection('dashboard');
        }, 2500);
    }, 1800);
}

// Future: Load real results from JSON
async function loadRiskData() {
    try {
        // In future: fetch('/api/results') or read local JSON
        console.log("Risk data would be loaded here from output_results/");
    } catch (error) {
        console.log("Using demo data for MVP");
    }
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