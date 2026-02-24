/* ============================================
   Guide Page JavaScript
   ============================================ */

console.log('[GUIDE] Loading guide page');

// Guide navigation
document.addEventListener('DOMContentLoaded', () => {
    console.log('[GUIDE] Initializing');
    
    const navBtns = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.guide-section');
    
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const sectionId = btn.dataset.section;
            console.log('[GUIDE] Navigating to:', sectionId);
            
            // Remove active from all
            navBtns.forEach(b => b.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // Add active to selected
            btn.classList.add('active');
            const section = document.getElementById(sectionId);
            if (section) section.classList.add('active');
        });
    });
});

console.log('[GUIDE] Script loaded');
