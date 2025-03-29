document.addEventListener('DOMContentLoaded', function() {
  // Define sanitizeAndRender at the top
  const sanitizeAndRender = (markdown) => {
    return marked.parse(markdown || '', { sanitize: true });
  };

  const jobUrlInput = document.getElementById('job-url');
  const jobDescription = document.getElementById('job-description');
  const fetchJobButton = document.getElementById('fetch-job');
  const analyzeButton = document.getElementById('analyze');
  const loader = document.getElementById('loader');
  const results = document.getElementById('results');
  const qualificationsContent = document.getElementById('qualifications-content');
  const messageContent = document.getElementById('message-content');

  // Configure marked options for GitHub-like markdown
  marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: true,
    highlight: function(code, lang) {
      return code;
    },
    langPrefix: 'language-'
  });

  fetchJobButton.addEventListener('click', async () => {
    const url = jobUrlInput.value.trim();
    if (!url) {
      showError('Please enter a valid URL');
      return;
    }

    try {
      loader.classList.remove('hidden');
      const response = await fetch(url);
      const html = await response.text();
      
      // Extract job description from HTML (this is a simple example)
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const jobText = doc.querySelector('.job-description')?.textContent || '';
      
      jobDescription.value = jobText;
      loader.classList.add('hidden');
    } catch (error) {
      loader.classList.add('hidden');
      showError('Failed to fetch job description');
    }
  });

  analyzeButton.addEventListener('click', async () => {
    const jobText = jobDescription.value.trim();
    if (!jobText) {
      showError('Please enter or fetch a job description');
      return;
    }

    try {
      loader.classList.remove('hidden');
      results.classList.add('hidden');
      
      // Get active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab.url.includes('linkedin.com') && !tab.url.includes('github.com')) {
        throw new Error('Please navigate to a LinkedIn or GitHub profile page');
      }

      // Inject content script if not already injected
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['contentScript.js']
        });
      } catch (e) {
        console.log('Content script already injected');
      }

      // Try to get profile data with retries
      let profileData;
      for (let i = 0; i < 3; i++) {
        try {
          profileData = await new Promise((resolve, reject) => {
            chrome.tabs.sendMessage(tab.id, { action: 'extractProfile' }, response => {
              if (chrome.runtime.lastError) {
                reject(chrome.runtime.lastError);
              } else {
                resolve(response);
              }
            });
          });
          if (profileData) break;
        } catch (e) {
          console.log(`Attempt ${i + 1} failed:`, e);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }

      if (!profileData) {
        throw new Error('Could not extract profile data after multiple attempts');
      }

      // Send to backend for analysis
      const response = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: profileData, jobDescription: jobText })
      });

      const data = await response.json();
      console.log('Analysis response:', data); // Debug logging
      
      // Ensure matchScore is a valid number
      const matchPercentage = Number.isInteger(data.matchScore) ? data.matchScore : 0;
      console.log('Match percentage:', matchPercentage); // Debug logging
      
      const matchElement = document.getElementById('match-percentage');
      const matchValue = document.getElementById('match-value');
      const matchLabel = document.getElementById('match-label');
      const debugInfo = document.getElementById('debug-info');

      // Update UI elements with validation and fallbacks
      matchElement.style.width = `${matchPercentage}%`;
      matchValue.textContent = `${matchPercentage}%`;
      matchLabel.innerHTML = data.scoreReasoning ? 
        sanitizeAndRender(data.scoreReasoning) : 
        'Score calculation failed';

      // Show debug info
      debugInfo.textContent = `Raw score: ${data.matchScore}, Parsed: ${matchPercentage}, Success: ${data.success}`;
      debugInfo.classList.remove('hidden');

      // Display results with sanitization
      qualificationsContent.innerHTML = sanitizeAndRender(data.analysis);
      messageContent.innerHTML = sanitizeAndRender(data.message);
      
      // Show results
      loader.classList.add('hidden');
      results.classList.remove('hidden');
    } catch (error) {
      console.error('Analysis error:', error); // Debug logging
      loader.classList.add('hidden');
      results.classList.remove('hidden');
      qualificationsContent.innerHTML = `
        <div class="error-message">
          <span class="material-icons">error</span>
          <p>${error.message || 'Error analyzing profile. Please try again.'}</p>
        </div>
      `;
    } finally {
      analyzeButton.disabled = false;
    }
  });

  function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
      <span class="material-icons">error</span>
      <p>${message}</p>
    `;
    
    const existingError = document.querySelector('.error-message');
    if (existingError) {
      existingError.remove();
    }
    
    document.querySelector('main').insertBefore(errorDiv, loader);
    setTimeout(() => errorDiv.remove(), 3000);
  }
});
