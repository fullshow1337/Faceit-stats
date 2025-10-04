/**
 * Faceit Stats Chrome Extension
 * Displays FACEIT statistics on Steam profile pages
 * Version: 4.0.0
 * Author: fullshow
 */

// Configuration
const CONFIG = {
    API_URL: 'https://api.fullshow.uz/extension/find-faceit-by-steam',
    TIMEOUT: 30000,
    SELECTORS: {
        PROFILE_AREA: '.profile_customization_area',
        PROFILE_LEFT: '.profile_leftcol',
        FACEIT_CONTAINER: '#facex'
    }
};

// Global state
let state = {
    nickname: '-',
    country: '-',
    level: '-',
    levelImg: '',
    faceitUrl: '#',
    elo: '-',
    matches: '-',
    winrate: '-',
    headshot: '-',
    kd: '-',
    avgKills: '-',
    avatar: '',
    banned: false,
    banReason: '',
    banEndDate: '',
    currentController: null,
    isDataLoaded: false,
    isLoading: false,
    wasAborted: false
};

/**
 * Shows loading preloader
 */
function showPreloader() {
    const customize = getProfileContainer();
    if (!customize) return;
    
    const preloaderHTML = `
        <div class="profile_customization">
            <div class="profile_customization_header">
                Faceit Stats by <a href="https://fullshow.uz" target="_blank" style="color:#ffffff; text-decoration:none; font-weight:bold; text-shadow: 0 0 8px rgba(0,0,0,0.8), 0 0 4px rgba(0,0,0,0.6), 0 1px 2px rgba(0,0,0,0.9); padding: 2px 4px; border-radius: 3px; background: rgba(0,0,0,0.3); transition: all 0.2s ease;">fullshow</a>
            </div>
            <div class="profile_customization_block">
                <div class="facex_stats_box" style="padding: 20px 24px 16px 24px; background: rgba(0, 0, 0, 0.5); border: 1.5px solid rgb(0, 0, 0); border-radius: 12px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.35); min-height: 70px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: #c7d5e0; font-size: 1.1em;">Loading...</span>
                </div>
            </div>
        </div>`;
    
    updateFaceitContainer(preloaderHTML);
}

/**
 * Gets the profile container element
 */
function getProfileContainer() {
    return document.querySelector(CONFIG.SELECTORS.PROFILE_AREA) || 
           document.querySelector(CONFIG.SELECTORS.PROFILE_LEFT);
}

/**
 * Updates the FACEIT container with new HTML
 */
function updateFaceitContainer(html) {
    const customize = getProfileContainer();
    if (!customize) return;
    
    let faceitElement = document.getElementById(CONFIG.SELECTORS.FACEIT_CONTAINER.slice(1));
    
    if (faceitElement) {
        faceitElement.innerHTML = html;
    } else {
        let textNode = document.createElement('div');
        textNode.id = CONFIG.SELECTORS.FACEIT_CONTAINER.slice(1);
        textNode.innerHTML = html;
        customize.prepend(textNode);
    }
}

/**
 * Checks if data is already loaded
 */
function isDataAlreadyLoaded() {
    const facexElement = document.getElementById(CONFIG.SELECTORS.FACEIT_CONTAINER.slice(1));
    if (!facexElement) return false;
    
    const statsBox = facexElement.querySelector('.facex_stats_box');
    if (!statsBox) return false;
    
    // Check if stats are displayed (not loading or error)
    return statsBox.querySelector('div[style*="display: flex; align-items: center; gap: 32px"]') !== null;
}

/**
 * Checks if tab is visible
 */
function isTabVisible() {
    return document.visibilityState === 'visible';
}

/**
 * Loads data if tab is visible and data not already loaded
 */
function loadDataIfVisible() {
    if (isTabVisible() && !isDataAlreadyLoaded() && !state.isLoading) {
        // Reset abort flag when starting new request
        state.wasAborted = false;
        loadFaceITProfile(window.location.href);
    }
}

/**
 * Handles tab visibility changes
 */
function handleVisibilityChange() {
    if (isTabVisible()) {
        // Tab became visible - try to load data if needed
        if (!isDataAlreadyLoaded() && !state.isLoading) {
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                loadDataIfVisible();
            }, 100);
        }
    } else {
        // Tab became hidden - abort current request
        if (state.currentController && state.isLoading) {
            state.currentController.abort();
            state.wasAborted = true;
        }
    }
}

/**
 * Handles page unload
 */
function handleBeforeUnload() {
    if (state.currentController) {
        state.currentController.abort();
    }
}

/**
 * Loads FACEIT profile data
 */
async function loadFaceITProfile(steamUrl) {
    if (isDataAlreadyLoaded() || state.isLoading) {
        return;
    }

    state.isLoading = true;
    state.wasAborted = false;

    try {
        // Abort previous request if exists
        if (state.currentController) {
            state.currentController.abort();
        }
        
        state.currentController = new AbortController();
        const timeoutId = setTimeout(() => {
            if (state.currentController) {
                state.currentController.abort();
            }
        }, CONFIG.TIMEOUT);

        const response = await fetch(CONFIG.API_URL, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ steam_url: steamUrl }),
            signal: state.currentController.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            if (response.status === 404) {
                console.log('Player not found on FACEIT');
                updateDOM(true);
                return;
            }
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        onFaceITProfileLoaded(data);
    } catch (error) {
        console.error('Error fetching API data:', error);
        
        // Don't show error if request was aborted due to tab switching
        if (error.name === 'AbortError' && state.wasAborted) {
            console.log('Request was aborted due to tab switching');
            return;
        }
        
        handleError(error);
    } finally {
        state.isLoading = false;
        state.currentController = null;
    }
}

/**
 * Handles API errors
 */
function handleError(error) {
    let errorMessage = 'Error loading data';
    
    if (error.name === 'AbortError') {
        errorMessage = 'Request timeout. Please try again.';
    } else if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
        errorMessage = 'Connection failed. Please check your internet connection.';
    }

    const errorHTML = `
        <div class="profile_customization">
            <div class="profile_customization_header">
                Faceit Stats by <a href="https://fullshow.uz" target="_blank" style="color:#ffffff; text-decoration:none; font-weight:bold; text-shadow: 0 0 8px rgba(0,0,0,0.8), 0 0 4px rgba(0,0,0,0.6), 0 1px 2px rgba(0,0,0,0.9); padding: 2px 4px; border-radius: 3px; background: rgba(0,0,0,0.3); transition: all 0.2s ease;">fullshow</a>
            </div>
            <div class="profile_customization_block">
                <div class="facex_stats_box" style="padding: 20px 24px 16px 24px; background: rgba(0, 0, 0, 0.5); border: 1.5px solid rgb(0, 0, 0); border-radius: 12px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.35); min-height: 70px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: #ff6b6b; font-size: 1.1em;">${errorMessage}</span>
                </div>
            </div>
        </div>`;
    
    updateFaceitContainer(errorHTML);
}

/**
 * Processes loaded FACEIT profile data
 */
function onFaceITProfileLoaded(data) {
    if (!data || !data.faceit || !data.faceit.level) {
        // Unrated/unranked player
        state.nickname = data?.nickname || '-';
        state.country = data?.country || '-';
        state.level = 'unrated';
        state.faceitUrl = '#';
        state.elo = '-';
        state.matches = '-';
        state.winrate = '-';
        state.headshot = '-';
        state.kd = '-';
        state.avgKills = '-';
        state.avatar = data?.avatar || '';
        state.banned = false;
        state.banReason = '';
        state.banEndDate = '';
        updateDOM(true);
        return;
    }
    
    // Ranked player
    state.nickname = data.nickname || '-';
    state.country = data.country || '-';
    state.level = data.faceit.level || '-';
    state.faceitUrl = data.faceit.url || '#';
    state.elo = data.faceit.elo || '-';
    state.matches = data.stats.matches || '-';
    state.winrate = data.stats.win_rate_percent || '-';
    state.headshot = data.stats.headshot_percent || '-';
    state.kd = data.stats.kd_ratio || '-';
    state.avgKills = data.stats.last_30_matches_avg_kills || '-';
    state.avatar = data.avatar || '';
    state.banned = (data.bans && data.bans.length > 0);
    state.banReason = state.banned ? data.bans[0].reason : '';
    state.banEndDate = state.banned && data.bans[0].formatted_end ? 
        formatDate(data.bans[0].formatted_end) : 'permanent';
    
    updateDOM(false);
}

/**
 * Formats date string
 */
function formatDate(dateStr) {
    const months = {
        '01': 'January', '02': 'February', '03': 'March', '04': 'April',
        '05': 'May', '06': 'June', '07': 'July', '08': 'August',
        '09': 'September', '10': 'October', '11': 'November', '12': 'December'
    };
    const [day, month, year] = dateStr.split('.');
    return `${day} ${months[month]} ${year}`;
}

/**
 * Updates DOM with FACEIT statistics
 */
function updateDOM(isUnrated = false) {
    const customize = getProfileContainer();
    if (!customize) return;

    // Asset URLs
    const flagSrc = `https://api.fullshow.uz/static/flags/${state.country.toLowerCase()}.svg`;
    const levelIcon = isUnrated
        ? 'https://api.fullshow.uz/static/unranked.svg'
        : `https://api.fullshow.uz/static/lvl${state.level}.svg`;

    const statsHTML = `
        <div class="profile_customization">
            <div class="profile_customization_header">
                Faceit Stats by <a href="https://fullshow.uz" target="_blank" style="color:#ffffff; text-decoration:none; font-weight:bold; text-shadow: 0 0 8px rgba(0,0,0,0.8), 0 0 4px rgba(0,0,0,0.6), 0 1px 2px rgba(0,0,0,0.9); padding: 2px 4px; border-radius: 3px; background: rgba(0,0,0,0.3); transition: all 0.2s ease;">fullshow</a>
            </div>
            <div class="profile_customization_block">
                <div class="facex_stats_box" style="padding: 20px 24px 16px 24px; background: rgba(0, 0, 0, 0.5); border: 1.5px solid rgb(0, 0, 0); border-radius: 12px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.35);">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                        <img class="levelbox" src="${levelIcon}" style="width:32px;height:32px;" alt="Level ${state.level}">
                        ${!isUnrated ? `<img class="facex_country" title="${state.country}" src="${flagSrc}" style="width:28px;height:20px;" alt="${state.country} flag">` : ''}
                        ${isUnrated
                            ? `<span class="facex_nickname" style="font-size: 1.2em; font-weight: bold; color: #c7d5e0;">${state.nickname}</span>`
                            : `<a href="${state.faceitUrl}" target="_blank" style="text-decoration: none;"><span class="facex_nickname" style="font-size: 1.2em; font-weight: bold; color: #c7d5e0;">${state.nickname}</span></a>`}
                    </div>
                    <div style="display: flex; align-items: center; gap: 32px; margin-bottom: 8px; font-size: 1em; color: #c7d5e0;">
                        <div><b>HS%:</b> ${state.headshot}%</div>
                        <div><b>K/D:</b> ${state.kd}</div>
                        <div><b>ELO:</b> ${state.elo}</div>
                        <div><b>Matches:</b> ${state.matches}</div>
                        <div><b>Winrate:</b> ${state.winrate}%</div>
                        <div><b>AVG Kills (last 30):</b> ${state.avgKills}</div>
                    </div>
                    ${isUnrated ? `<div style='color:#9b9b9b; margin-top:8px;'><b>unrated</b></div>` : ''}
                    ${state.banned && !isUnrated ? `<div style='color:red; margin-top:8px;'><b>Banned:</b> ${state.banReason}${state.banEndDate === 'permanent' ? ' (permanent)' : ` (until ${state.banEndDate})`}</div>` : ''}
                </div>
            </div>
        </div>`;

    updateFaceitContainer(statsHTML);
    state.isDataLoaded = true;
}

// Initialize extension
function init() {
    // Check if we're on a valid Steam profile page
    const currentUrl = window.location.href;
    
    // Exclude specific Steam pages where extension shouldn't work
    const excludedPages = [
        'tradeoffers',
        'inventory',
        'friends',
        'groups',
        'screenshots',
        'videos',
        'artwork',
        'workshop',
        'myworkshopfiles',
        'filedetails',
        'edit',
        'settings',
        'badges',
        'gamecards',
        'tradingcards',
        'allcomments'
    ];
    
    // Check if current URL contains any excluded pages
    const isExcludedPage = excludedPages.some(page => currentUrl.includes(`/${page}`));
    
    // Check if we're on a Steam profile page (either /id/ or /profiles/)
    const isSteamProfilePage = currentUrl.includes('steamcommunity.com/id/') || 
                              currentUrl.includes('steamcommunity.com/profiles/');
    
    if (!isSteamProfilePage || isExcludedPage) {
        console.log('Faceit Stats: Not a valid Steam profile page, extension disabled');
        console.log('Current URL:', currentUrl);
        return;
    }
    
    console.log('Faceit Stats: Valid Steam profile page detected, initializing...');
    showPreloader();
    loadDataIfVisible();
    
    // Event listeners
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);
}

// Start the extension
init();
