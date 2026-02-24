/* Guide Page Script */

console.log('[GUIDE] Guide page loaded');

// Initialize guide navigation
document.addEventListener('DOMContentLoaded', () => {
    console.log('[GUIDE] Initializing guide page');
    
    const navButtons = document.querySelectorAll('.guide-nav-btn');
    const sections = document.querySelectorAll('.guide-section');
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const sectionId = btn.dataset.section;
            console.log('[GUIDE] Navigating to section:', sectionId);
            
            // Remove active class from all buttons and sections
            navButtons.forEach(b => b.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked button and corresponding section
            btn.classList.add('active');
            const section = document.getElementById(sectionId);
            if (section) section.classList.add('active');
            
            // Scroll to top of content
            document.querySelector('.guide-content').scrollTop = 0;
        });
    });
    
    // Initialize FAQ collapsible items
    const faqItems = document.querySelectorAll('.faq-item h5');
    faqItems.forEach(item => {
        item.addEventListener('click', () => {
            item.classList.toggle('collapsed');
            const answer = item.nextElementSibling;
            if (answer) {
                answer.style.display = answer.style.display === 'none' ? 'block' : 'none';
            }
        });
    });
    
    // Load guide content from API
    loadGuideContent();
});

// Load guide content from API
async function loadGuideContent() {
    console.log('[GUIDE] Loading guide content from API...');
    try {
        const response = await fetch('/guide/api/get-guide');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        console.log('[GUIDE] Guide content loaded:', data);
        
        // Update sections if needed
        updateGuideContent(data);
    } catch (error) {
        console.error('[GUIDE] Failed to load guide content:', error);
    }
}

// Update guide content dynamically
function updateGuideContent(guideData) {
    if (!guideData.sections) return;
    
    guideData.sections.forEach(section => {
        const el = document.getElementById(section.id);
        if (el) {
            const contentDiv = el.querySelector('div') || el;
            if (section.content) {
                contentDiv.innerHTML += section.content;
            }
        }
    });
}

// Load FAQ data
async function loadFAQData() {
    console.log('[GUIDE] Loading FAQ from API...');
    try {
        const response = await fetch('/guide/api/faq');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        console.log('[GUIDE] FAQ data loaded');
        
        // Update FAQ section
        const faqSection = document.getElementById('faq');
        if (faqSection && data.faqs) {
            const faqContent = data.faqs.map(faq => `
                <div class="faq-item">
                    <h5>${faq.question}</h5>
                    <p style="display: none;">${faq.answer}</p>
                </div>
            `).join('');
            
            const contentArea = faqSection.querySelector('div');
            if (contentArea) {
                contentArea.innerHTML += faqContent;
            }
        }
    } catch (error) {
        console.error('[GUIDE] Failed to load FAQ:', error);
    }
}

// Load glossary data
async function loadGlossaryData() {
    console.log('[GUIDE] Loading glossary from API...');
    try {
        const response = await fetch('/guide/api/glossary');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        console.log('[GUIDE] Glossary data loaded');
        
        // Update glossary section
        const glossarySection = document.getElementById('glossary');
        if (glossarySection && data.terms) {
            const glossaryContent = Object.entries(data.terms).map(([term, definition]) => `
                <div class="glossary-item">
                    <h5>${term}</h5>
                    <p>${definition}</p>
                </div>
            `).join('');
            
            const contentArea = glossarySection.querySelector('div');
            if (contentArea) {
                contentArea.innerHTML += glossaryContent;
            }
        }
    } catch (error) {
        console.error('[GUIDE] Failed to load glossary:', error);
    }
}

// Search guide content
function searchGuide(query) {
    console.log('[GUIDE] Searching for:', query);
    
    const sections = document.querySelectorAll('.guide-section');
    const lowerQuery = query.toLowerCase();
    
    sections.forEach(section => {
        const text = section.textContent.toLowerCase();
        section.style.display = text.includes(lowerQuery) ? 'block' : 'none';
    });
}

// Add search functionality if search element exists
const searchInput = document.querySelector('[data-search-guide]');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        searchGuide(e.target.value);
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Quick jump to glossary (Ctrl+G)
    if (e.ctrlKey && e.key === 'g') {
        console.log('[GUIDE] Jump to glossary');
        document.querySelector('[data-section="glossary"]').click();
        e.preventDefault();
    }
    
    // Quick jump to FAQ (Ctrl+F)
    if (e.ctrlKey && e.key === 'f') {
        console.log('[GUIDE] Jump to FAQ');
        document.querySelector('[data-section="faq"]').click();
        e.preventDefault();
    }
});

console.log('[GUIDE] Guide page initialization complete');
