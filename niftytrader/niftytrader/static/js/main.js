/* ============================================
   Main Application JavaScript
   ============================================ */

console.log('[APP] NiftyTrader initialized');

// Utility: Format numbers
window.formatNumber = (num, decimals = 2) => parseFloat(num).toFixed(decimals);

// Utility: Format percentage
window.formatPercent = (value) => {
    const num = parseFloat(value);
    const sign = num >= 0 ? '+' : '';
    return `${sign}${window.formatNumber(num, 2)}%`;
};

// Utility: Get color class
window.getColorClass = (value) => {
    const num = parseFloat(value);
    if (num > 0) return 'positive';
    if (num < 0) return 'negative';
    return 'neutral';
};

// Utility: Format time
window.formatTime = () => {
    const date = new Date();
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
};

// Update time display
setInterval(() => {
    const timeEls = document.querySelectorAll('#updateTime');
    timeEls.forEach(el => el.textContent = window.formatTime());
}, 1000);

console.log('[APP] Utilities loaded');
