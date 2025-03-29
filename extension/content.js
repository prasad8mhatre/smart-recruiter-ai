function extractProfileData() {
    let profileData = {};
    
    if (window.location.hostname.includes('linkedin.com')) {
        profileData = {
            type: 'linkedin',
            name: document.querySelector('.text-heading-xlarge')?.textContent,
            headline: document.querySelector('.text-body-medium')?.textContent,
            experience: Array.from(document.querySelectorAll('.experience-section li')).map(el => el.textContent)
        };
    } else if (window.location.hostname.includes('github.com')) {
        profileData = {
            type: 'github',
            username: document.querySelector('[itemprop="name"]')?.textContent,
            bio: document.querySelector('[itemprop="description"]')?.textContent,
            repos: Array.from(document.querySelectorAll('[itemprop="owns"]')).map(el => el.textContent)
        };
    }
    
    return profileData;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'extractProfile') {
        sendResponse(extractProfileData());
    }
});
