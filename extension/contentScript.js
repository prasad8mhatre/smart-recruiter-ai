function convertToMarkdown(element) {
    let markdown = '';
    
    // Process children recursively
    Array.from(element.childNodes).forEach(node => {
        if (node.nodeType === Node.TEXT_NODE) {
            markdown += node.textContent.trim();
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            const tag = node.tagName.toLowerCase();
            const content = convertToMarkdown(node).trim();
            
            if (!content) return;

            switch (tag) {
                case 'h1': markdown += `# ${content}\n\n`; break;
                case 'h2': markdown += `## ${content}\n\n`; break;
                case 'h3': markdown += `### ${content}\n\n`; break;
                case 'p': markdown += `${content}\n\n`; break;
                case 'ul':
                    markdown += content.split('\n')
                        .filter(line => line.trim())
                        .map(line => `- ${line}\n`)
                        .join('') + '\n';
                    break;
                case 'li': markdown += `${content}\n`; break;
                case 'strong':
                case 'b': markdown += `**${content}**`; break;
                case 'em':
                case 'i': markdown += `*${content}*`; break;
                case 'br': markdown += '\n'; break;
                case 'div':
                case 'span':
                    markdown += `${content} `;
                    break;
                default: markdown += content;
            }
        }
    });
    return markdown;
}

function getAllPageContent() {
    // Get entire page content as text first
    const fullText = document.body.innerText;
    
    // Get specific sections
    const mainContent = document.querySelector('main');
    const articleContent = document.querySelector('article');
    
    return {
        fullText,
        mainContent: mainContent?.innerText || '',
        articleContent: articleContent?.innerText || ''
    };
}

async function extractLinkedInProfile() {
    try {
        await waitForElements(['h1', 'main', '.pv-top-card']);
        
        // Get all profile sections
        const allContent = {};
        const sections = document.querySelectorAll('section.artdeco-card');
        sections.forEach(section => {
            const sectionId = section.id || 'section_' + Math.random().toString(36).substr(2, 9);
            allContent[sectionId] = getAllVisibleText(section);
        });

        // Basic profile info
        const introCard = document.querySelector('.pv-top-card');
        const profileData = {
            type: 'linkedin',
            name: document.querySelector('h1')?.innerText?.trim() || '',
            headline: document.querySelector('div.text-body-medium')?.innerText?.trim() || '',
            about: document.querySelector('#about ~ div .pv-shared-text-with-see-more')?.innerText?.trim() || '',
            experience: Array.from(document.querySelectorAll('#experience ~ div .pvs-list .pvs-entity')).map(exp => ({
                title: exp.querySelector('.t-bold span')?.innerText?.trim() || '',
                company: exp.querySelector('.t-normal span')?.innerText?.trim() || '',
                duration: exp.querySelector('.pvs-entity__caption-wrapper')?.innerText?.trim() || '',
                location: exp.querySelector('.pvs-entity__sub-navigational-text')?.innerText?.trim() || '',
                description: exp.querySelector('.pvs-list__item--with-top-padding')?.innerText?.trim() || ''
            })),
            education: Array.from(document.querySelectorAll('#education ~ div .pvs-list .pvs-entity')).map(edu => ({
                school: edu.querySelector('.t-bold span')?.innerText?.trim() || '',
                degree: edu.querySelector('.t-normal span')?.innerText?.trim() || '',
                duration: edu.querySelector('.pvs-entity__caption-wrapper')?.innerText?.trim() || ''
            })),
            skills: Array.from(document.querySelectorAll('#skills ~ div .pvs-list .pvs-entity')).map(skill => 
                skill.querySelector('.t-bold span')?.innerText?.trim() || ''
            ).filter(Boolean),
            rawContent: {
                intro: getAllVisibleText(introCard),
                sections: allContent,
                fullPage: document.body.innerText
            },
            // Include the entire page content in multiple formats
            content: document.body.innerText,
            pageContent: {
                text: document.body.innerText,
                markdown: convertToMarkdown(document.body),
                sections: allContent
            }
        };

        console.log('Extracted LinkedIn Profile:', profileData);
        return profileData;

    } catch (error) {
        console.error('Profile extraction error:', error);
        // Return error with full page content as fallback
        return {
            type: 'linkedin',
            error: error.message,
            content: document.body.innerText,
            rawHtml: document.documentElement.innerHTML
        };
    }
}

function getAllSections() {
    // Get all main sections from the profile
    const sections = {};
    const sectionElements = document.querySelectorAll('section[data-section]');
    
    sectionElements.forEach(section => {
        const sectionId = section.id || section.getAttribute('data-section');
        if (sectionId) {
            sections[sectionId] = {
                title: section.querySelector('h2')?.innerText || '',
                content: getAllVisibleText(section)
            };
        }
    });
    
    return sections;
}

function getAllVisibleText(element) {
    if (!element) return '';
    
    const style = window.getComputedStyle(element);
    if (style.display === 'none' || style.visibility === 'hidden') return '';
    
    let text = '';
    for (const node of element.childNodes) {
        if (node.nodeType === Node.TEXT_NODE) {
            text += node.textContent.trim() + ' ';
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            text += getAllVisibleText(node) + ' ';
        }
    }
    return text.trim();
}

function getIntroSection() {
    const intro = document.querySelector('.pv-text-details__about-this-profile-entrypoint');
    return {
        name: document.querySelector('h1')?.innerText?.trim(),
        headline: intro?.innerText?.trim(),
        location: document.querySelector('.pv-text-details__left-panel .text-body-small')?.innerText?.trim(),
        connections: document.querySelector('.pv-top-card--list-bullet')?.innerText?.trim(),
        profileImage: document.querySelector('.pv-top-card-profile-picture__image')?.src
    };
}

function getAboutSection() {
    return document.querySelector('#about ~ div .pv-shared-text-with-see-more')?.innerText?.trim() || '';
}

function getExperienceSection() {
    const section = document.querySelector('#experience ~ div .pvs-list');
    return Array.from(section?.querySelectorAll('.pvs-entity') || []).map(exp => ({
        fullText: getAllVisibleText(exp),
        title: exp.querySelector('.t-bold .visually-hidden')?.innerText?.trim(),
        company: exp.querySelector('.t-normal .visually-hidden')?.innerText?.trim(),
        duration: exp.querySelector('.pvs-entity__caption-wrapper .visually-hidden')?.innerText?.trim(),
        description: exp.querySelector('.pvs-list__item--with-top-padding .visually-hidden')?.innerText?.trim()
    }));
}

function getEducationSection() {
    const section = document.querySelector('#education ~ div .pvs-list');
    return Array.from(section?.querySelectorAll('.pvs-entity') || []).map(edu => ({
        fullText: getAllVisibleText(edu),
        school: edu.querySelector('.t-bold .visually-hidden')?.innerText?.trim(),
        degree: edu.querySelector('.t-normal .visually-hidden')?.innerText?.trim(),
        duration: edu.querySelector('.date-range .visually-hidden')?.innerText?.trim()
    }));
}

function getSkillsSection() {
    const section = document.querySelector('#skills ~ div .pvs-list');
    return Array.from(section?.querySelectorAll('.pvs-entity') || [])
        .map(skill => getAllVisibleText(skill))
        .filter(Boolean);
}

function getCertificationsSection() {
    const section = document.querySelector('#licenses_and_certifications ~ div .pvs-list');
    return Array.from(section?.querySelectorAll('.pvs-entity') || []).map(cert => ({
        fullText: getAllVisibleText(cert),
        name: cert.querySelector('.t-bold .visually-hidden')?.innerText?.trim(),
        issuer: cert.querySelector('.t-normal .visually-hidden')?.innerText?.trim()
    }));
}

function getProjectsSection() {
    const section = document.querySelector('#projects ~ div .pvs-list');
    return Array.from(section?.querySelectorAll('.pvs-entity') || []).map(proj => ({
        fullText: getAllVisibleText(proj),
        title: proj.querySelector('.t-bold .visually-hidden')?.innerText?.trim(),
        description: proj.querySelector('.pvs-list__item--with-top-padding .visually-hidden')?.innerText?.trim()
    }));
}

function getPublicationsSection() {
    const section = document.querySelector('#publications ~ div .pvs-list');
    return Array.from(section?.querySelectorAll('.pvs-entity') || []).map(pub => ({
        fullText: getAllVisibleText(pub),
        title: pub.querySelector('.t-bold .visually-hidden')?.innerText?.trim(),
        publisher: pub.querySelector('.t-normal .visually-hidden')?.innerText?.trim()
    }));
}

function getRecommendationsSection() {
    const section = document.querySelector('#recommendations ~ div .pvs-list');
    return Array.from(section?.querySelectorAll('.pvs-entity') || [])
        .map(rec => getAllVisibleText(rec))
        .filter(Boolean);
}

function waitForElements(selectors, timeout = 10000) {
    return Promise.race([
        Promise.all(selectors.map(selector => {
            return new Promise(resolve => {
                if (document.querySelector(selector)) {
                    resolve();
                }
                const observer = new MutationObserver(() => {
                    if (document.querySelector(selector)) {
                        observer.disconnect();
                        resolve();
                    }
                });
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            });
        })),
        new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout waiting for elements')), timeout)
        )
    ]);
}

// Message listener for popup requests
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'extractProfile') {
        extractLinkedInProfile()
            .then(profileData => sendResponse(profileData))
            .catch(error => sendResponse({ error: error.message }));
        return true; // Keep message channel open for async response
    }
});
