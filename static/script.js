// Language translations - глобальная переменная
const translations = {
    ru: {
        'Get Statistics': 'Получить статистику',
        'Steam URL': 'Steam URL',
        'Loading statistics...': 'Загрузка статистики...',
        'Main Statistics': 'Основная статистика',
        'Additional Statistics': 'Дополнительная статистика',
        'Match History': 'История матчей',
        'Date': 'Дата',
        'Mode': 'Режим',
        'Result': 'Результат',
        'Score': 'Счёт',
        'Map': 'Карта',
        'Bans History': 'История банов',
        'Win': 'Победа',
        'Loss': 'Поражение',
        'Unknown': 'Неизвестно',
        'Permanent ban': 'Постоянный бан',
        'навсегда': 'навсегда',
        'About': 'О нас',
        'Support': 'Поддержка',
        'Legal': 'Правовая информация',
        'GitHub': 'GitHub',
        'Telegram': 'Telegram',
        'Donate': 'Donate',
        'Yoomoney': 'Yoomoney',
        'Discord': 'Yoomoney',
        'Privacy Policy': 'Политика конфиденциальности',
        'Terms of Service': 'Условия использования',
        'All rights reserved': 'Все права защищены',
        'Player not found on FACEIT': 'Игрок не найден на FACEIT',
        'Recent Searches': 'Последние поиски',
        'Loading recent searches...': 'Загрузка последних поисков...',
        'No searches yet': 'Пока нет поисков',
        'Loading error': 'Ошибка загрузки',
        'just_now': 'только что',
        'minutes_ago': 'мин. назад',
        'hours_ago': 'ч. назад',
        'days_ago': 'дн. назад',
        'Player has active bans': 'У игрока есть активные баны',
        'Chrome Extension': 'Расширение Chrome',
        'Chrome Extension Available': 'Доступно расширение Chrome',
        'Get FACEIT stats directly on Steam profiles': 'Получайте статистику FACEIT прямо в профилях Steam',
        'Install': 'Установить'
    },
    en: {
        'Get Statistics': 'Get Statistics',
        'Steam URL': 'Steam URL',
        'Loading statistics...': 'Loading statistics...',
        'Main Statistics': 'Main Statistics',
        'Additional Statistics': 'Additional Statistics',
        'Match History': 'Match History',
        'Date': 'Date',
        'Mode': 'Mode',
        'Result': 'Result',
        'Score': 'Score',
        'Map': 'Map',
        'Bans History': 'Bans History',
        'Win': 'Win',
        'Loss': 'Loss',
        'Unknown': 'Unknown',
        'Permanent ban': 'Permanent ban',
        'навсегда': 'never',
        'About': 'About',
        'Support': 'Support',
        'Legal': 'Legal',
        'GitHub': 'GitHub',
        'Telegram': 'Telegram',
        'Donate': 'Donate',
        'Yoomoney': 'Yoomoney',
        'Discord': 'Yoomoney',
        'Privacy Policy': 'Privacy Policy',
        'Terms of Service': 'Terms of Service',
        'All rights reserved': 'All rights reserved',
        'Player not found on FACEIT': 'Player not found on FACEIT',
        'Recent Searches': 'Recent Searches',
        'Loading recent searches...': 'Loading recent searches...',
        'No searches yet': 'No searches yet',
        'Loading error': 'Loading error',
        'just_now': 'just now',
        'minutes_ago': 'minutes ago',
        'hours_ago': 'hours ago',
        'days_ago': 'days ago',
        'Player has active bans': 'Player has active bans',
        'Chrome Extension': 'Chrome Extension',
        'Chrome Extension Available': 'Chrome Extension Available',
        'Get FACEIT stats directly on Steam profiles': 'Get FACEIT stats directly on Steam profiles',
        'Install': 'Install'
    }
};

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('statsForm');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    const errorText = error.querySelector('span');
    const playerAvatar = document.getElementById('player-avatar');
    const playerNickname = document.getElementById('player-nickname');
    const cs2Elo = document.getElementById('cs2-elo');
    const cs2Level = document.getElementById('cs2-level');
    const csgoElo = document.getElementById('csgo-elo');
    const kdRatio = document.getElementById('kd-ratio');
    const cs2Avg = document.getElementById('cs2-avg');
    const matchList = document.getElementById('match-list');

    // Theme switching function
    const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme) {
        document.documentElement.setAttribute('data-theme', currentTheme);
        if (currentTheme === 'dark') {
            toggleSwitch.checked = true;
        }
    }

    function switchTheme(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    }

    toggleSwitch.addEventListener('change', switchTheme);

    // Language switching function
    function setLanguage(lang) {
        document.documentElement.setAttribute('data-language', lang);
        localStorage.setItem('language', lang);
        
        // Update all translatable elements
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            if (translations[lang][key]) {
                element.textContent = translations[lang][key];
            }
        });
        
        // Обновляем live ленту при смене языка
        if (document.getElementById('recent-searches-list')) {
            loadRecentSearches();
        }
    }

    // Инициализация языка
    const savedLanguage = localStorage.getItem('language') || 'ru';
    setLanguage(savedLanguage);
    updateFlag(savedLanguage);



    // Обработчик переключения языка
    document.getElementById('languageToggle').addEventListener('click', function() {
        const currentLang = document.documentElement.getAttribute('data-language') || 'ru';
        const newLang = currentLang === 'ru' ? 'en' : 'ru';
        setLanguage(newLang);
        updateFlag(newLang);
        localStorage.setItem('language', newLang);
    });

    function updateFlag(lang) {
        const flagPath = lang === 'ru' ? '/static/flags/ru.svg' : '/static/flags/us.svg';
        document.getElementById('currentFlag').src = flagPath;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const steamUrl = document.getElementById('steamUrl').value;
        
        // Show loading, hide errors and results
        loading.classList.remove('d-none');
        error.classList.add('d-none');
        result.style.display = 'none';
        
        try {
            const response = await fetch('/find-faceit-by-steam', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ steam_url: steamUrl })
            });
            
            const data = await response.json();
            console.log('Received data:', data);
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Player not found on FACEIT');
                }
                throw new Error(data.detail || 'Error getting data');
            }

            // Проверка на валидность профиля
            if (!data.player_id || !data.nickname) {
                throw new Error('Профиль не существует или был удален');
            }

            // Проверка на наличие основных данных
            const isProfileValid = data.faceit && (
                data.faceit.elo !== null || 
                data.faceit.level !== null || 
                data.faceit.csgo_elo !== null ||
                (data.stats && data.stats.matches > 0)
            );

            if (!isProfileValid) {
                throw new Error('Профиль не существует или был удален');
            }
            
            // Удаляем SVG-заглушку, если она есть
            const existingSvg = document.getElementById('avatar-placeholder-svg');
            if (existingSvg) existingSvg.remove();
            if (data.avatar) {
                playerAvatar.src = data.avatar;
                playerAvatar.style.display = '';
            } else {
                // Вставляем SVG-заглушку, если её ещё нет
                const svgPlaceholder = `<svg id="avatar-placeholder-svg" width="152" height="152" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><circle cx="24" cy="24" r="24" fill="#3d3d4c"></circle><path d="M12.6744 36C12.4045 36 12.135 35.8165 12.0449 35.5412C11.9797 35.3648 11.9857 35.1692 12.0615 34.9973C12.1374 34.8253 12.2769 34.6911 12.4496 34.6239L18.6519 32.0559C19.3261 31.7809 19.7754 31.093 19.7754 30.3132C19.7754 30.2217 19.7754 30.1757 19.8204 30.0842C19.0298 29.4846 18.3727 28.721 17.8924 27.8435C17.4121 26.966 17.1195 25.9946 17.0338 24.9934C16.4497 24.5352 16.1348 23.893 16.1348 23.1135C16.1348 22.3797 16.4494 21.7378 16.9887 21.279V19.1238C16.9887 16.9224 17.9774 14.9047 19.6406 13.529C21.3031 12.1532 23.5057 11.6944 25.6181 12.1992C28.6743 12.9783 30.9212 15.9595 30.9212 19.3529V21.3249C31.4606 21.7834 31.8202 22.4257 31.8202 23.1595C31.8202 23.893 31.4606 24.5812 30.9212 25.0397C30.7417 27.0573 29.708 28.8919 28.1346 30.0838C28.1799 30.1757 28.1799 30.2217 28.1799 30.3136C28.1799 31.0927 28.6292 31.7353 29.3034 32.0103L35.5504 34.5324C35.7231 34.5995 35.8626 34.7338 35.9385 34.9057C36.0143 35.0776 36.0203 35.2732 35.9551 35.4496C35.8892 35.6258 35.7577 35.7682 35.5892 35.8456C35.4207 35.923 35.229 35.929 35.0561 35.8625L28.809 33.3401C28.3248 33.1399 27.8957 32.8223 27.5589 32.4147C27.2221 32.0072 26.9878 31.5219 26.8764 31.0011H26.337C26.0224 31.0011 25.7079 30.772 25.6628 30.4507C25.5281 30.1298 25.7079 29.8088 26.0224 29.6713C28.0448 28.8456 29.4382 26.8279 29.5282 24.5809C29.5282 24.3058 29.7077 24.0764 29.9328 23.9849C30.2471 23.8474 30.4268 23.5261 30.4268 23.1592C30.4268 22.7926 30.2474 22.5172 29.9325 22.3338C29.708 22.1963 29.5729 21.9669 29.5729 21.6919V19.3073C29.5729 16.6014 27.775 14.1709 25.3033 13.5749C23.5954 13.162 21.8428 13.5749 20.4945 14.6297C19.1463 15.7301 18.3821 17.3352 18.3821 19.1238V21.6919C18.3821 21.9669 18.2473 22.1963 18.0225 22.3338C17.7079 22.4713 17.5281 22.7926 17.5281 23.1595C17.5281 23.5261 17.7079 23.8014 18.0225 23.9849C18.1267 24.0502 18.2165 24.1369 18.2861 24.2395C18.3558 24.3421 18.4038 24.4583 18.4271 24.5809C18.5168 26.8283 19.8651 28.8 21.9326 29.6713C22.2471 29.8088 22.4269 30.1298 22.3372 30.4507C22.2921 30.772 21.9776 31.0011 21.663 31.0011H21.0339C20.9224 31.5219 20.6882 32.0072 20.3514 32.4147C20.0146 32.8223 19.5855 33.1399 19.1012 33.3401L12.8989 35.9081C12.8542 36 12.7641 36 12.6744 36Z" fill="#242432"></path></svg>`;
                playerAvatar.style.display = 'none';
                playerAvatar.insertAdjacentHTML('afterend', svgPlaceholder);
            }
            // Обновляем никнейм с флагом страны
            if (data.country) {
                playerNickname.innerHTML = `<img src="/static/flags/${data.country.toLowerCase()}.svg" alt="${data.country}" style="margin-right:7px;border-radius:3px;vertical-align:middle;width:24px;height:18px;">${data.nickname}`;
            } else {
                playerNickname.textContent = data.nickname;
            }

            // Update login info (только новая структура API)
            const profileLogin = document.getElementById('profile-login');
            const faceitProfileUrl = data.faceit && data.faceit.url ? data.faceit.url : '';
            const steamNickname = data.steam && data.steam.nickname ? data.steam.nickname : '';
            const steamId64 = data.steam && data.steam.id_64 ? data.steam.id_64 : '';
            const steamProfileUrl = data.steam && data.steam.profile_url ? data.steam.profile_url : (steamId64 ? `https://steamcommunity.com/profiles/${steamId64}` : '');
            if (faceitProfileUrl || (steamNickname && steamProfileUrl)) {
                profileLogin.innerHTML = `
                    ${faceitProfileUrl ? `
                    <a href="${faceitProfileUrl}" alt="faceit profile" rel="nofollow noreferrer" target="_blank" style="display:inline-flex;align-items:center;text-decoration:none;font-weight:500;font-size:1.1em;">
                        <img src="/static/faceit-icon.svg" alt="Faceit" style="width:22px;height:22px;margin-right:7px;vertical-align:middle;">
                        Faceit <i class="fa fa-external-link" style="margin-left:7px;font-size:0.95em;"></i>
                    </a>
                    ` : ''}
                    ${steamNickname && steamProfileUrl ? `
                    <a href="${steamProfileUrl}" alt="steam profile" rel="nofollow noreferrer" target="_blank" style="display:inline-flex;align-items:center;text-decoration:none;font-weight:500;font-size:1.1em;">
                        <i class="fab fa-steam" aria-hidden="true" style="font-size:22px;margin-right:7px;vertical-align:middle;"></i>
                        Steam <i class="fa fa-external-link" style="margin-left:7px;font-size:0.95em;"></i>
                    </a>
                    ` : ''}
                `;
            } else {
                profileLogin.innerHTML = '';
            }

            // Update player banner
            const playerBanner = document.getElementById('player-banner');
            if (data.banner) {
                // Добавляем обработчик ошибки загрузки изображения
                playerBanner.onerror = function() {
                    console.warn('Failed to load banner image:', data.banner);
                    this.style.display = 'none';
                    this.src = '';
                };
                playerBanner.onload = function() {
                    this.style.display = 'block';
                };
                playerBanner.src = data.banner;
            } else {
                playerBanner.style.display = 'none';
                playerBanner.src = '';
                playerBanner.onerror = null;
                playerBanner.onload = null;
            }

            // Update CS2 level with SVG icon - показываем invalid.svg если есть баны
            const cs2LevelElement = document.getElementById('cs2-level');
            
            // Проверяем есть ли активные баны
            if (data.bans && data.bans.length > 0) {
                // Если есть баны, показываем invalid.svg
                const currentLang = document.documentElement.getAttribute('data-language') || 'ru';
                const banTooltip = translations[currentLang]['Player has active bans'] || 'У игрока есть активные баны';
                
                cs2LevelElement.removeAttribute('data-level');
                cs2LevelElement.innerHTML = `<img src="/static/invalid.svg" alt="Banned" style="width: 24px; height: 24px;" title="${banTooltip}">`;
            } else {
                // Если банов нет, показываем обычный уровень
                cs2LevelElement.innerHTML = '';
                if (data.faceit && data.faceit.level !== undefined && data.faceit.level !== null) {
                    cs2LevelElement.setAttribute('data-level', data.faceit.level);
                } else if (data.games && data.games.cs2 && data.games.cs2.skill_level !== undefined && data.games.cs2.skill_level !== null) {
                    cs2LevelElement.setAttribute('data-level', data.games.cs2.skill_level);
                } else {
                    cs2LevelElement.removeAttribute('data-level');
                }
            }
            
            // Main Statistics (CS2 ELO, CS:GO ELO) с улучшенной обработкой null
            const mainStatsSection = document.querySelector('.main-statistics-title').parentElement;
            const cs2EloValue = data.faceit && data.faceit.elo !== null ? data.faceit.elo : 
                              (data.stats && data.stats.matches > 0 ? 'Недоступно' : '-');
            const csgoEloValue = data.faceit && data.faceit.csgo_elo !== null ? data.faceit.csgo_elo : 
                               (data.stats && data.stats.matches > 0 ? 'Недоступно' : '-');
            mainStatsSection.innerHTML = `
                <h5 data-translate="Main Statistics" class="main-statistics-title">Main Statistics</h5>
                <div class="d-flex justify-content-between mb-2">
                    <span class="stats-label">CS2 ELO</span>
                    <span class="stats-value" id="cs2-elo">${cs2EloValue}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="stats-label">CS:GO ELO</span>
                    <span class="stats-value" id="csgo-elo">${csgoEloValue}</span>
                </div>
            `;

            // Улучшенная обработка статистики с проверкой на null и 0
            const winRate = data.stats && data.stats.win_rate_percent !== null ? 
                          (data.stats.win_rate_percent > 0 ? data.stats.win_rate_percent : '0') : '-';
            const headshotPercent = data.stats && data.stats.headshot_percent !== null ? 
                                  (data.stats.headshot_percent > 0 ? data.stats.headshot_percent : '0') : '-';
            const adr = data.stats && data.stats.adr !== null ? 
                       (data.stats.adr > 0 ? data.stats.adr.toFixed(2) : '0') : '-';
            const kdRatio = data.stats && data.stats.kd_ratio !== null ? 
                           (data.stats.kd_ratio > 0 ? data.stats.kd_ratio.toFixed(2) : '0') : '-';
            const avgKills = data.stats && data.stats.last_30_matches_avg_kills !== null ? 
                           (data.stats.last_30_matches_avg_kills > 0 ? data.stats.last_30_matches_avg_kills : '0') : '-';
            const totalMatches = data.stats && data.stats.matches !== null ? 
                               (data.stats.matches > 0 ? data.stats.matches : '0') : '-';

            // Additional Statistics с улучшенной обработкой null и 0
            const additionalStatsSection = document.querySelector('.additional-statistics-title').parentElement;
            additionalStatsSection.innerHTML = `
                <h5 data-translate="Additional Statistics" class="additional-statistics-title">Additional Statistics</h5>
                <div class="d-flex justify-content-between mb-2">
                    <span class="stats-label">K/D Ratio</span>
                    <span class="stats-value" id="kd-ratio">${kdRatio}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="stats-label">Avg. Kills</span>
                    <span class="stats-value" id="cs2-avg">${avgKills}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="stats-label">Win Rate</span>
                    <span class="stats-value">${winRate !== '-' ? winRate + '%' : '-'}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="stats-label">Headshot %</span>
                    <span class="stats-value">${headshotPercent !== '-' ? headshotPercent + '%' : '-'}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="stats-label">ADR</span>
                    <span class="stats-value">${adr}</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="stats-label">Total Matches</span>
                    <span class="stats-value" id="total-matches">${totalMatches}</span>
                </div>
            `;
            
            // Update match history
            matchList.innerHTML = '';
            if (data.match_history && data.match_history.length > 0) {
                const matchHistoryContainer = document.getElementById('match-list');
                if (!matchHistoryContainer) {
                    console.error('Element with id "match-list" not found');
                    return;
                }
                matchHistoryContainer.innerHTML = '';
                
                data.match_history.forEach(match => {
                    const matchElement = document.createElement('div');
                    matchElement.className = 'match-item';
                    matchElement.style.cursor = 'pointer';
                    
                    // Добавляем обработчик клика для перехода на страницу матча
                    if (match.match_url) {
                        matchElement.addEventListener('click', () => {
                            window.open(match.match_url, '_blank');
                        });
                    }
                    
                    const date = new Date(match.date * 1000);
                    const formattedDate = date.toLocaleDateString();
                    
                    const resultText = match.result || 'Unknown';
                    const resultClass = (resultText.toLowerCase() === 'lose') ? 'loss' : resultText.toLowerCase();
                    matchElement.innerHTML = `
                        <div class="match-date">${formattedDate}</div>
                        <div class="match-mode">${match.mode}</div>
                        <div class="match-result ${resultClass}" data-translate="${resultText}">${resultText}</div>
                        <div class="match-score">${match.score}</div>
                        <div class="match-map">${match.map}</div>
                        <div class="match-kda">${match.kills}/${match.deaths}/${match.assists}</div>
                    `;
                    
                    matchHistoryContainer.appendChild(matchElement);
                });
            } else {
                const matchHistoryContainer = document.getElementById('match-list');
                if (matchHistoryContainer) {
                    matchHistoryContainer.innerHTML = '<div class="text-center">No matches found</div>';
                }
            }
            
            // Update bans section
            const bansSection = document.getElementById('bans-section');
            const bansList = document.getElementById('bans-list');
            bansList.innerHTML = '';
            
            if (data.bans && data.bans.length > 0) {
                bansSection.style.display = 'block';
                data.bans.forEach(ban => {
                    console.log('Processing ban:', ban);
                    const banElement = document.createElement('div');
                    banElement.className = 'ban-item';
                    
                    // Новая структура банов: reason, start_date, end_date
                    const currentLang = document.documentElement.getAttribute('data-language') || 'ru';
                    const banReason = ban.reason || 'Unknown';
                    const startDate = ban.start_date || 'Unknown date';
                    const endDate = ban.end_date === 'permanent' ? 
                        (translations[currentLang]['навсегда'] || 'never') : 
                        (ban.end_date || 'never');
                    
                    const banTypeInfo = {
                        ru: {
                            'login': 'Бан связан с нарушениями безопасности аккаунта или подозрением на взлом',
                            'cheating': 'Бан за использование читов или других запрещённых программ',
                            'abuse': 'Бан за оскорбления, токсичное поведение или нарушение правил общения',
                            'smurfing': 'Бан за использование мультиаккаунтов (смурфинг)',
                            'unsportsmanlike conduct': 'Бан за неспортивное поведение (оскорбления, неуважение, провокации и т.д.)',
                            'toxic': 'Бан за токсичное поведение в игре или чате',
                            'boosting': 'Бан за бустинг (искусственное повышение рейтинга)',
                            'matchmaking': 'Бан за нарушение правил матчмейкинга',
                            'queue': 'Бан за нарушение правил очереди на игру',
                            'report': 'Бан по результатам рассмотрения жалоб',
                            'manual': 'Бан, выданный администрацией вручную',
                            'game': 'Бан за нарушение правил игры',
                            'community': 'Бан за нарушение правил сообщества',
                            'afk': 'Бан за частые уходы из игры (AFK)',
                            'leaving': 'Бан за преждевременный выход из матча',
                            'griefing': 'Бан за намеренное ухудшение игрового процесса',
                            'harassment': 'Бан за преследование других игроков',
                            'spam': 'Бан за спам в чате или голосовом канале',
                            'exploit': 'Бан за использование игровых багов или эксплойтов',
                            'trading': 'Бан за нарушение правил торговли',
                            'payment': 'Бан за проблемы с оплатой или мошенничество',
                            'verification': 'Бан за неподтверждённую личность',
                            'temporary': 'Временный бан за нарушение правил',
                            'permanent': 'Постоянный бан за серьёзное нарушение',
                            'hardware': 'Бан за использование запрещённого оборудования',
                            'vpn': 'Бан за использование VPN или прокси',
                            'region': 'Бан за нарушение региональных ограничений',
                            'language': 'Бан за нарушение правил общения на определённом языке',
                            'custom': 'Бан по индивидуальному решению администрации',
                            'smurf': 'Бан за использование второго аккаунта (смурфинг)',
                            'platform abuse': 'Бан за злоупотребление возможностями платформы',
                            'Platform Abuse': 'Бан за злоупотребление возможностями платформы',
                            'multiaccount': 'Бан за создание нескольких аккаунтов',
                            'ban evasion': 'Бан за обход блокировки',
                            'account sharing': 'Бан за передачу аккаунта третьим лицам',
                            'offensive nickname': 'Бан за оскорбительный никнейм',
                            'offensive avatar': 'Бан за оскорбительный аватар',
                            'inappropriate content': 'Бан за неприемлемый контент',
                            'abusive language': 'Бан за оскорбительную лексику',
                            'teamkilling': 'Бан за убийство тиммейтов',
                            'leaver': 'Бан за регулярные ливы',
                            'throwing': 'Бан за намеренный слив игр',
                            'botting': 'Бан за использование ботов',
                            'macro': 'Бан за использование макросов',
                            'script': 'Бан за использование скриптов',
                            'hacking': 'Бан за взлом или попытку взлома',
                            'account theft': 'Бан за попытку кражи аккаунта',
                            'impersonation': 'Бан за выдачу себя за другого игрока',
                            'advertising': 'Бан за рекламу',
                            'scamming': 'Бан за мошенничество',
                            'inactivity': 'Бан за неактивность',
                            'unverified': 'Бан за неподтверждённый аккаунт',
                            'other': 'Бан по другой причине',
                            'policy breach': 'Бан за нарушение политики FACEIT. Это может быть связано с нарушением пользовательского соглашения, кодекса поведения или других официальных правил платформы.'
                        },
                        en: {
                            'login': 'Ban related to account security violations or suspected hacking',
                            'cheating': 'Ban for using cheats or other prohibited programs',
                            'abuse': 'Ban for insults, toxic behavior or communication rule violations',
                            'smurfing': 'Ban for using multiple accounts (smurfing)',
                            'unsportsmanlike conduct': 'Ban for unsportsmanlike behavior (insults, disrespect, provocations, etc.)',
                            'toxic': 'Ban for toxic behavior in game or chat',
                            'boosting': 'Ban for boosting (artificial rating increase)',
                            'matchmaking': 'Ban for matchmaking rule violations',
                            'queue': 'Ban for queue rule violations',
                            'report': 'Ban based on complaint review results',
                            'manual': 'Ban issued manually by administration',
                            'game': 'Ban for game rule violations',
                            'community': 'Ban for community rule violations',
                            'afk': 'Ban for frequent AFK behavior',
                            'leaving': 'Ban for premature match exit',
                            'griefing': 'Ban for intentional gameplay disruption',
                            'harassment': 'Ban for harassing other players',
                            'spam': 'Ban for spam in chat or voice channel',
                            'exploit': 'Ban for using game bugs or exploits',
                            'trading': 'Ban for trading rule violations',
                            'payment': 'Ban for payment issues or fraud',
                            'verification': 'Ban for unverified identity',
                            'temporary': 'Temporary ban for rule violations',
                            'permanent': 'Permanent ban for serious violations',
                            'hardware': 'Ban for using prohibited equipment',
                            'vpn': 'Ban for using VPN or proxy',
                            'region': 'Ban for regional restriction violations',
                            'language': 'Ban for language communication rule violations',
                            'custom': 'Ban by individual administration decision',
                            'smurf': 'Ban for using second account (smurfing)',
                            'platform abuse': 'Ban for platform feature abuse',
                            'Platform Abuse': 'Ban for platform feature abuse',
                            'multiaccount': 'Ban for creating multiple accounts',
                            'ban evasion': 'Ban for ban evasion',
                            'account sharing': 'Ban for sharing account with third parties',
                            'offensive nickname': 'Ban for offensive nickname',
                            'offensive avatar': 'Ban for offensive avatar',
                            'inappropriate content': 'Ban for inappropriate content',
                            'abusive language': 'Ban for abusive language',
                            'teamkilling': 'Ban for killing teammates',
                            'leaver': 'Ban for regular leaving',
                            'throwing': 'Ban for intentional game throwing',
                            'botting': 'Ban for using bots',
                            'macro': 'Ban for using macros',
                            'script': 'Ban for using scripts',
                            'hacking': 'Ban for hacking or hacking attempts',
                            'account theft': 'Ban for account theft attempts',
                            'impersonation': 'Ban for impersonating other players',
                            'advertising': 'Ban for advertising',
                            'scamming': 'Ban for fraud',
                            'inactivity': 'Ban for inactivity',
                            'unverified': 'Ban for unverified account',
                            'other': 'Ban for other reasons',
                            'policy breach': 'Ban for FACEIT policy violation. This may be related to user agreement, code of conduct or other official platform rules violation.'
                        }
                    };

                    // Добавляем переводы для типов банов
                    const banTypeTranslations = {
                        ru: {
                            'login': 'Вход',
                            'Platform Abuse': 'Злоупотребление платформой',
                            'platform abuse': 'Злоупотребление платформой',
                            'cheating': 'Читы',
                            'smurfing': 'Смурфинг',
                            'abuse': 'Оскорбления'
                        },
                        en: {
                            'login': 'Login',
                            'Platform Abuse': 'Platform Abuse',
                            'platform abuse': 'Platform Abuse',
                            'cheating': 'Cheating',
                            'smurfing': 'Smurfing',
                            'abuse': 'Abuse'
                        }
                    };

                    const translatedReason = banTypeTranslations[currentLang][banReason] || banReason;
                    const banDescription = banTypeInfo[currentLang][banReason] || banTypeInfo[currentLang]['other'] || 'Ban for rule violation';

                    banElement.innerHTML = `
                        <span class="ban-type">
                            ${translatedReason}
                            ${banDescription ? 
                                `<i class="fas fa-question-circle ms-1" data-bs-toggle="tooltip" data-bs-placement="top" title="${banDescription}"></i>` 
                                : ''}
                        </span>
                        <span class="ban-reason">${translatedReason}</span>
                        <span class="ban-date">
                            ${startDate} - ${endDate}
                        </span>
                    `;
                    bansList.appendChild(banElement);
                });

                // Инициализируем tooltips для новых элементов
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            } else {
                bansSection.style.display = 'none';
            }
            
            // Show result
            result.style.display = 'block';
            
            // Скрываем live-feed и карточку расширения при успешном поиске
            const liveFeed = document.querySelector('.live-feed');
            if (liveFeed) {
                liveFeed.style.display = 'none';
            }
            
            // Скрываем карточку расширения при показе результатов
            const extensionCard = document.querySelector('.extension-info-card');
            if (extensionCard) {
                extensionCard.style.display = 'none';
            }
            
            // Обновляем URL если есть Steam ID
            const steamId = data.steam && data.steam.id_64 ? data.steam.id_64 : null;
            if (steamId) {
                // Обновляем URL без перезагрузки страницы
                const newUrl = `${window.location.origin}/${steamId}`;
                window.history.pushState({ steamId: steamId }, '', newUrl);
            } else {
                // Если нет Steam ID, возвращаемся на главную
                window.history.pushState({}, '', window.location.origin);
            }
            
        } catch (err) {
            console.error('Error:', err);
            errorText.textContent = err.message;
            error.classList.remove('d-none');
            
            // При ошибке показываем live-feed и карточку расширения, если мы на главной странице
            if (window.location.pathname === '/') {
                const liveFeed = document.querySelector('.live-feed');
                if (liveFeed) {
                    liveFeed.style.display = 'block';
                }
                
                // Показываем карточку расширения на главной при ошибке
                const extensionCard = document.querySelector('.extension-info-card');
                if (extensionCard) {
                    extensionCard.style.display = 'block';
                }
            }
        } finally {
            loading.classList.add('d-none');
        }
    });

    // Обработчик выбора языка
    document.querySelectorAll('.dropdown-item[data-lang]').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('data-lang');
            setLanguage(lang);
            updateFlag(lang);
            localStorage.setItem('language', lang);
        });
    });
    
    // Обработчик кнопки "Назад" в браузере
    window.addEventListener('popstate', function(event) {
        if (event.state && event.state.steamId) {
            // Если вернулись к профилю, загружаем его данные
            const steamUrl = `https://steamcommunity.com/profiles/${event.state.steamId}`;
            document.getElementById('steamUrl').value = steamUrl;
            document.getElementById('statsForm').dispatchEvent(new Event('submit'));
        } else {
            // Если вернулись на главную, очищаем результаты и показываем live-feed
            document.getElementById('steamUrl').value = '';
            document.getElementById('result').style.display = 'none';
            document.getElementById('error').classList.add('d-none');
            
            // Показываем live-feed и карточку расширения снова
            const liveFeed = document.querySelector('.live-feed');
            if (liveFeed) {
                liveFeed.style.display = 'block';
            }
            
            // Показываем карточку расширения на главной
            const extensionCard = document.querySelector('.extension-info-card');
            if (extensionCard) {
                extensionCard.style.display = 'block';
            }
        }
    });

    // Загружаем recent searches при загрузке страницы
    loadRecentSearches();
    
    // Обновляем каждые 30 секунд
    setInterval(loadRecentSearches, 30000);
});

function switchTheme(e) {
    if (e.target.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    }
}

// Функциональность для Live ленты
async function loadRecentSearches() {
    try {
        const response = await fetch('/api/recent-searches');
        const data = await response.json();
        
        const recentSearchesList = document.getElementById('recent-searches-list');
        if (!recentSearchesList) return;
        
        if (data.searches && data.searches.length > 0) {
            const currentLang = document.documentElement.getAttribute('data-language') || 'ru';
            
            recentSearchesList.innerHTML = data.searches.map(search => {
                const avatarHtml = search.avatar 
                    ? `<img src="${search.avatar}" alt="${search.nickname}" class="recent-search-avatar" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                       <div class="recent-search-avatar-placeholder" style="display: none;">
                           <i class="fas fa-user" style="color: var(--text-secondary); font-size: 14px;"></i>
                       </div>`
                    : `<div class="recent-search-avatar-placeholder">
                           <i class="fas fa-user" style="color: var(--text-secondary); font-size: 14px;"></i>
                       </div>`;
                
                // Создаем элемент уровня
                let levelHtml = '';
                if (search.has_bans) {
                    const currentLang = document.documentElement.getAttribute('data-language') || 'ru';
                    const banTooltip = translations[currentLang]['Player has active bans'] || 'У игрока есть активные баны';
                    levelHtml = `<div class="recent-search-level banned" title="${banTooltip}">
                                   <img src="/static/invalid.svg" alt="Banned">
                                 </div>`;
                } else if (search.level) {
                    levelHtml = `<div class="recent-search-level" title="Level ${search.level}">
                                   <img src="/static/lvl${search.level}.svg" alt="Level ${search.level}">
                                 </div>`;
                }
                
                // Создаем элемент флага
                const flagHtml = search.country 
                    ? `<img src="/static/flags/${search.country.toLowerCase()}.svg" alt="${search.country}" class="recent-search-flag">`
                    : '';
                
                // Переводим время
                let timeText = '';
                if (typeof search.time_ago === 'object' && search.time_ago.key) {
                    const timeKey = search.time_ago.key;
                    const timeValue = search.time_ago.value;
                    
                    if (timeKey === 'just_now') {
                        timeText = translations[currentLang]['just_now'] || 'только что';
                    } else {
                        const timeUnit = translations[currentLang][timeKey] || timeKey;
                        timeText = `${timeValue} ${timeUnit}`;
                    }
                } else {
                    // Fallback для старого формата
                    timeText = search.time_ago;
                }
                
                return `
                    <div class="recent-search-item" onclick="loadPlayerBySteamId('${search.steam_id}')">
                        <div class="recent-search-info">
                            <div class="recent-search-status ${search.success ? 'success' : 'failed'}"></div>
                            ${avatarHtml}
                            <div class="recent-search-player-info">
                                <div class="recent-search-nickname" title="${search.nickname}">${search.nickname}</div>
                                ${levelHtml}
                                ${flagHtml}
                            </div>
                        </div>
                        <div class="recent-search-time">${timeText}</div>
                    </div>
                `;
            }).join('');
        } else {
            const currentLang = document.documentElement.getAttribute('data-language') || 'ru';
            const noSearchesText = translations[currentLang]['No searches yet'] || 'Пока нет поисков';
            recentSearchesList.innerHTML = `<div class="no-searches">${noSearchesText}</div>`;
        }
    } catch (error) {
        console.error('Error loading recent searches:', error);
        const recentSearchesList = document.getElementById('recent-searches-list');
        if (recentSearchesList) {
            const currentLang = document.documentElement.getAttribute('data-language') || 'ru';
            const errorText = translations[currentLang]['Loading error'] || 'Ошибка загрузки';
            recentSearchesList.innerHTML = `<div class="no-searches">${errorText}</div>`;
        }
    }
}

function loadPlayerBySteamId(steamId) {
    const steamUrl = `https://steamcommunity.com/profiles/${steamId}`;
    document.getElementById('steamUrl').value = steamUrl;
    document.getElementById('statsForm').dispatchEvent(new Event('submit'));
} 