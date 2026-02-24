/* ============================================
   Dashboard Page JavaScript
   ============================================ */

console.log('[DASHBOARD] Loading dashboard');

// Load and display all dashboard data
async function loadDashboardData() {
    try {
        const [trendsRes, moversRes, stocksRes] = await Promise.all([
            fetch('/dashboard/api/trend'),
            fetch('/dashboard/api/movers'),
            fetch('/dashboard/api/stocks')
        ]);
        
        if (!trendsRes.ok || !moversRes.ok || !stocksRes.ok) {
            throw new Error('Failed to fetch dashboard data');
        }
        
        const trend = await trendsRes.json();
        const movers = await moversRes.json();
        const stocks = await stocksRes.json();
        
        updateTrendDisplay(trend);
        updateMoversTable(movers.movers);
        updateStocksTable(stocks.stocks);
        
        console.log('[DASHBOARD] Data loaded successfully');
    } catch (error) {
        console.error('[DASHBOARD] Error loading data:', error);
    }
}

// Update trend cards
function updateTrendDisplay(trend) {
    const trendEl = document.getElementById('marketTrend');
    const avgEl = document.getElementById('avgChange');
    const advDecEl = document.getElementById('advDec');
    const bullBearEl = document.getElementById('bullBear');
    
    if (trendEl) {
        trendEl.textContent = trend.trend;
        trendEl.className = `trend-badge ${trend.trend.toLowerCase().replace(' ', '-')}`;
    }
    
    if (avgEl) avgEl.textContent = formatPercent(trend.avg_change);
    if (advDecEl) advDecEl.textContent = `${trend.advancers}/${trend.decliners}`;
    if (bullBearEl) bullBearEl.textContent = `${formatNumber(trend.bull_power, 1)}/${formatNumber(trend.bear_power, 1)}`;
}

// Update movers table
function updateMoversTable(movers) {
    const tbody = document.getElementById('moversBody');
    if (!tbody) return;
    
    if (!movers || movers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = movers.slice(0, 5).map(stock => `
        <tr>
            <td><strong>${stock.symbol}</strong></td>
            <td>${formatNumber(stock.lastPrice, 2)}</td>
            <td class="${getColorClass(stock.change)}">${formatNumber(stock.change, 2)}</td>
            <td class="${getColorClass(stock.pChange)}">${formatPercent(stock.pChange)}</td>
            <td>${formatNumber(stock.weight, 2)}</td>
        </tr>
    `).join('');
}

// Update stocks table
function updateStocksTable(stocks) {
    const tbody = document.getElementById('stocksBody');
    if (!tbody) return;
    
    if (!stocks || stocks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No stocks available</td></tr>';
        return;
    }
    
    tbody.innerHTML = stocks.map(stock => `
        <tr>
            <td><strong>${stock.symbol}</strong></td>
            <td>${formatNumber(stock.lastPrice, 2)}</td>
            <td class="${getColorClass(stock.change)}">${formatNumber(stock.change, 2)}</td>
            <td class="${getColorClass(stock.pChange)}">${formatPercent(stock.pChange)}</td>
            <td>${formatNumber(stock.weight || 0, 2)}</td>
            <td>${(stock.totalTradedVolume || 0).toLocaleString()}</td>
        </tr>
    `).join('');
}

// Search functionality
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#stocksBody tr');
        
        rows.forEach(row => {
            const symbol = row.querySelector('strong')?.textContent.toLowerCase() || '';
            row.style.display = symbol.includes(query) ? '' : 'none';
        });
    });
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('[DASHBOARD] Initializing');
    loadDashboardData();
    
    // Refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
});

console.log('[DASHBOARD] Script loaded');
