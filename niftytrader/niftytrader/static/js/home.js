/* ============================================
   Home Page JavaScript
   ============================================ */

console.log('[HOME] Loading home page');

// Load market overview stats
async function loadMarketStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const data = await response.json();
        console.log('[HOME] Stats loaded:', data);
        
        document.getElementById('marketStatus').textContent = data.status;
    } catch (error) {
        console.error('[HOME] Error loading stats:', error);
    }
}

// Load dashboard summary on home
async function loadDashboardSummary() {
    try {
        const response = await fetch('/dashboard/api/summary');
        if (!response.ok) throw new Error('Failed to fetch summary');
        
        const data = await response.json();
        console.log('[HOME] Summary loaded:', data);
        
        const trendEl = document.getElementById('marketTrend');
        const avgChangeEl = document.getElementById('avgChange');
        
        if (trendEl && data.trend) {
            trendEl.textContent = data.trend.trend;
        }
        
        if (avgChangeEl && data.trend) {
            avgChangeEl.textContent = formatPercent(data.trend.avg_change);
        }
    } catch (error) {
        console.error('[HOME] Error loading summary:', error);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[HOME] DOM loaded');
    loadMarketStats();
    loadDashboardSummary();
});
