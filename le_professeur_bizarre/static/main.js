/**
 * Le Professeur Bizarre - Frontend JavaScript
 * Handles translation requests and UI updates
 */

// DOM Elements
const englishInput = document.getElementById('english-input');
const translateBtn = document.getElementById('translate-btn');
const responseSection = document.getElementById('response-section');
const loadingSection = document.getElementById('loading-section');
const errorSection = document.getElementById('error-section');
const frenchTranslation = document.getElementById('french-translation');
const pronunciationTip = document.getElementById('pronunciation-tip');
const culturalFact = document.getElementById('cultural-fact');
const errorMessage = document.getElementById('error-message');
const quickBtns = document.querySelectorAll('.quick-btn');

// API endpoint (relative to Reachy Mini daemon)
const API_BASE = window.location.origin;

// State
let isTranslating = false;

/**
 * Send translation request to the backend
 */
async function translateText(text) {
    if (!text.trim() || isTranslating) return;

    isTranslating = true;
    translateBtn.disabled = true;

    // Show loading, hide others
    hideAllSections();
    loadingSection.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/apps/le_professeur_bizarre/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text.trim() })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Update UI with response
        displayTranslation(data);

    } catch (error) {
        console.error('Translation error:', error);
        displayError(error.message);
    } finally {
        isTranslating = false;
        translateBtn.disabled = false;
    }
}

/**
 * Display translation result
 */
function displayTranslation(data) {
    hideAllSections();

    // Set French translation
    frenchTranslation.textContent = data.french_translation || 'Translation not available';

    // Set pronunciation tip if available
    if (data.pronunciation_tip) {
        pronunciationTip.textContent = `💡 ${data.pronunciation_tip}`;
        pronunciationTip.classList.remove('hidden');
    } else {
        pronunciationTip.classList.add('hidden');
    }

    // Set cultural fact
    culturalFact.textContent = data.cultural_fact || 'No fact available';

    // Show response section with animation
    responseSection.classList.remove('hidden');
}

/**
 * Display error message
 */
function displayError(message) {
    hideAllSections();
    errorMessage.textContent = message;
    errorSection.classList.remove('hidden');
}

/**
 * Hide all result sections
 */
function hideAllSections() {
    responseSection.classList.add('hidden');
    loadingSection.classList.add('hidden');
    errorSection.classList.add('hidden');
}

/**
 * Handle translate button click
 */
translateBtn.addEventListener('click', () => {
    translateText(englishInput.value);
});

/**
 * Handle Enter key in textarea
 */
englishInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        translateText(englishInput.value);
    }
});

/**
 * Handle quick phrase buttons
 */
quickBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const phrase = btn.dataset.phrase;
        englishInput.value = phrase;
        translateText(phrase);
    });
});

/**
 * Demo mode - for testing without backend
 */
const DEMO_RESPONSES = [
    {
        french_translation: "Bonjour, comment allez-vous?",
        cultural_fact: "In France, it's considered extremely rude to enter a shop without saying 'Bonjour'. Americans often skip this, causing French shopkeepers to silently judge them for their barbarian ways.",
        pronunciation_tip: "Say 'bone-JOOR' like you're slightly annoyed to be awake"
    },
    {
        french_translation: "J'adore le fromage",
        cultural_fact: "France has over 1,200 varieties of cheese. Charles de Gaulle once said 'How can you govern a country that has 246 varieties of cheese?' He was actually being conservative with that number.",
        pronunciation_tip: "Say 'fro-MAHJ' - let the 'j' sound like you're purring"
    },
    {
        french_translation: "Où sont les toilettes?",
        cultural_fact: "Many French public toilets are unisex and some still use the famous 'Turkish toilets' (holes in the ground). American tourists have been known to flee in confusion.",
        pronunciation_tip: "Say 'too-ah-LET' - stress the last syllable dramatically"
    },
    {
        french_translation: "Ce vin est excellent",
        cultural_fact: "In France, serving wine at the wrong temperature is considered a minor crime against humanity. Also, putting ice cubes in wine will get you deported.",
        pronunciation_tip: "Say 'vaN' - the 'n' should barely exist, just nasalize it"
    },
    {
        french_translation: "L'addition, s'il vous plaît",
        cultural_fact: "In France, the waiter will NEVER bring you the check unless you ask. They consider it rude to rush you. Americans sit waiting for hours, thinking the service is terrible.",
        pronunciation_tip: "Say 'seel voo PLAY' - sound slightly impatient for authenticity"
    }
];

/**
 * Check if backend is available, fall back to demo mode
 */
async function checkBackend() {
    try {
        const response = await fetch(`${API_BASE}/api/state/full`, { timeout: 2000 });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Initialize - check for demo mode
 */
async function init() {
    const backendAvailable = await checkBackend();

    if (!backendAvailable) {
        console.log('Backend not available - running in demo mode');

        // Override translateText for demo mode
        window.translateText = async function(text) {
            if (!text.trim() || isTranslating) return;

            isTranslating = true;
            translateBtn.disabled = true;

            hideAllSections();
            loadingSection.classList.remove('hidden');

            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000));

            // Pick a random response
            const demoResponse = DEMO_RESPONSES[Math.floor(Math.random() * DEMO_RESPONSES.length)];

            displayTranslation(demoResponse);

            isTranslating = false;
            translateBtn.disabled = false;
        };
    }
}

// Initialize on load
init();
