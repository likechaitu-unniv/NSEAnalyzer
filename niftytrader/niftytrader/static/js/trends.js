/* ============================================
   Trends Page JavaScript
   ============================================ */

console.log('[TRENDS] Loading trends page');

// Load trend analysis
async function loadTrendAnalysis() {
    try {
        const response = await fetch('/trends/api/analysis');
        if (!response.ok) throw new Error('Failed to fetch analysis');
        
        const data = await response.json();
        console.log('[TRENDS] Analysis loaded:', data);
        
        updateAnalysisDisplay(data);
    } catch (error) {
        console.error('[TRENDS] Error loading analysis:', error);
    }
}

// Update analysis display
function updateAnalysisDisplay(data) {
    const signalEl = document.getElementById('marketSignal');
    const pcrEl = document.getElementById('pcrValue');
    const supportEl = document.getElementById('supportLevel');
    const resistanceEl = document.getElementById('resistanceLevel');
    
    if (signalEl && data.signal) signalEl.textContent = data.signal;
    if (pcrEl && data.pcr) pcrEl.textContent = formatNumber(data.pcr, 3);
    if (supportEl && data.support) supportEl.textContent = formatNumber(data.support, 2);
    if (resistanceEl && data.resistance) resistanceEl.textContent = formatNumber(data.resistance, 2);
}

// Load OI data
async function loadOIData() {
    try {
        const response = await fetch('/trends/api/oi');
        if (!response.ok) throw new Error('Failed to fetch OI data');
        
        const data = await response.json();
        console.log('[TRENDS] OI data loaded:', data);
        
        updateOITable(data.oi_data);
    } catch (error) {
        console.error('[TRENDS] Error loading OI data:', error);
    }
}

// Update OI table
function updateOITable(oiData) {
    const tbody = document.getElementById('oiBody');
    if (!tbody) return;
    
    tbody.innerHTML = oiData.map(row => `
        <tr>
            <td>${formatNumber(row.strike, 0)}</td>
            <td>${formatNumber(row.call_oi, 0)}</td>
            <td>${formatNumber(row.put_oi, 0)}</td>
            <td class="${getColorClass(row.diff)}">${formatNumber(row.diff, 0)}</td>
        </tr>
    `).join('');
}

// Load history data
async function loadHistoryData() {
    try {
        const response = await fetch('/trends/api/history');
        if (!response.ok) throw new Error('Failed to fetch history');
        
        const data = await response.json();
        console.log('[TRENDS] History loaded:', data);
        
        updateHistoryTable(data.history);
    } catch (error) {
        console.error('[TRENDS] Error loading history:', error);
    }
}

// Update history table
function updateHistoryTable(history) {
    const tbody = document.getElementById('historyBody');
    if (!tbody) return;
    
    tbody.innerHTML = history.map(row => `
        <tr>
            <td>${row.date}</td>
            <td>${row.signal}</td>
            <td>${formatNumber(row.pcr, 2)}</td>
            <td>${formatNumber(row.price, 0)}</td>
        </tr>
    `).join('');
    
    // Also render the chart
    renderTrendChart(history);
}

// Render trend chart
function renderTrendChart(history) {
    const ctx = document.getElementById('trendChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (window.trendChartInstance) {
        window.trendChartInstance.destroy();
    }
    
    // Prepare data
    const dates = history.map(h => h.date).reverse();
    const prices = history.map(h => h.price).reverse();
    
    // Create chart
    window.trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Nifty 50 Price',
                data: prices,
                borderColor: '#0066cc',
                backgroundColor: 'rgba(0, 102, 204, 0.1)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#0066cc',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#333',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 14 },
                    bodyFont: { size: 13 }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        color: '#666',
                        callback: function(value) {
                            return formatNumber(value, 0);
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#666'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
    console.log('[TRENDS] Chart rendered');
}

// Tab switching
document.addEventListener('DOMContentLoaded', () => {
    console.log('[TRENDS] Initializing');
    
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            console.log('[TRENDS] Switching to tab:', tabId);
            
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active from all buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            
            // Show selected tab
            const tab = document.getElementById(tabId);
            if (tab) tab.classList.add('active');
            btn.classList.add('active');
        });
    });
    
    // Load initial data
    loadTrendAnalysis();
    loadOIData();
    loadHistoryData();
    
    // Refresh every 60 seconds
    setInterval(() => {
        loadTrendAnalysis();
        loadOIData();
        loadHistoryData();
    }, 60000);
});

console.log('[TRENDS] Script loaded');
