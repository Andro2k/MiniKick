/**
 * MiniKick Chat Overlay - Main Client Runtime
 * Handles URL configuration, message DOM rendering, emote parsing,
 * color contrast correction, and WebSocket event stream.
 */

// 1. Configuration & URL Parameters
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token') || '';
const urlOrientation = urlParams.get('orientation');

const MAX_SAFE_DOM_NODES = 50;
const VALID_THEMES = new Set(['dark', 'light', 'minimal']);
let rawTheme = urlParams.get('theme') || 'dark';
let theme = VALID_THEMES.has(rawTheme) ? rawTheme : 'dark';
let fadeTime = urlParams.get('fade') !== null ? parseInt(urlParams.get('fade'), 10) : 15;
let fontSize = urlParams.get('size') || '14px';
let showBots = urlParams.get('show_bots') !== 'false';
let showTime = urlParams.get('show_time') === 'true';
let orientation = urlOrientation || 'vertical';
let defaultFlow = orientation === 'horizontal' ? 'right-to-left' : 'bottom-to-top';
let flow = urlParams.get('flow') || defaultFlow;
let bigEmotes = urlParams.get('big_emotes') !== 'false';
let animIn = urlParams.get('anim_in') || 'fade';
let showGifs = urlParams.get('show_gifs') !== 'false';
let hideCommands = urlParams.get('hide_commands') === 'true';
let showBadges = urlParams.get('show_badges') !== 'false';
let showPlatform = urlParams.get('show_platform') !== 'false';

// Apply theme and base styles
const themeStyle = document.getElementById('theme-style');
if (themeStyle) {
    themeStyle.href = `/css/${theme}.css`;
}
document.documentElement.style.setProperty('--font-size', fontSize);

const container = document.getElementById('chat-container');
if (container) {
    container.classList.add(`orientation-${orientation}`, `flow-${flow}`);
}

/**
 * Applies live configuration changes dispatched from MiniKick via WebSocket.
 * Supports individual styles for vertical and horizontal orientations.
 * @param {Object} cfg Active chat overlay settings from server
 */
function applyLiveConfig(cfg) {
    if (!cfg || typeof cfg !== 'object') return;

    // Resolve orientation: locked by URL if provided, or updated live
    if (!urlOrientation && cfg.orientation) {
        orientation = cfg.orientation;
    }

    // Extract profile specific to current orientation (vertical or horizontal)
    const modeConfig = (cfg[orientation] && typeof cfg[orientation] === 'object')
        ? cfg[orientation]
        : cfg;
    const commonConfig = (cfg.common && typeof cfg.common === 'object')
        ? cfg.common
        : cfg;

    if (modeConfig.theme && !urlParams.has('theme')) {
        let newTheme = String(modeConfig.theme).trim().toLowerCase();
        if (!VALID_THEMES.has(newTheme)) newTheme = 'dark';
        theme = newTheme;
        if (themeStyle) themeStyle.href = `/css/${theme}.css`;
    }

    if (modeConfig.size && !urlParams.has('size')) {
        const rawSize = String(modeConfig.size).trim();
        fontSize = rawSize.endsWith('px') ? rawSize : `${rawSize}px`;
        document.documentElement.style.setProperty('--font-size', fontSize);
    }

    if (modeConfig.fade !== undefined && !urlParams.has('fade')) {
        fadeTime = parseInt(modeConfig.fade, 10) || 0;
    }

    if (modeConfig.anim_in && !urlParams.has('anim_in')) {
        animIn = modeConfig.anim_in;
    }

    if (!urlParams.has('flow')) {
        flow = modeConfig.flow || (orientation === 'horizontal' ? 'right-to-left' : 'bottom-to-top');
    }

    if (commonConfig.show_bots !== undefined && !urlParams.has('show_bots')) {
        showBots = Boolean(commonConfig.show_bots);
    }

    if (commonConfig.show_time !== undefined && !urlParams.has('show_time')) {
        showTime = Boolean(commonConfig.show_time);
    }

    if (commonConfig.big_emotes !== undefined && !urlParams.has('big_emotes')) {
        bigEmotes = Boolean(commonConfig.big_emotes);
    }

    if (commonConfig.show_gifs !== undefined && !urlParams.has('show_gifs')) {
        showGifs = Boolean(commonConfig.show_gifs);
    }

    if (commonConfig.hide_commands !== undefined && !urlParams.has('hide_commands')) {
        hideCommands = Boolean(commonConfig.hide_commands);
    }

    if (commonConfig.show_badges !== undefined && !urlParams.has('show_badges')) {
        showBadges = Boolean(commonConfig.show_badges);
    }

    if (commonConfig.show_platform !== undefined && !urlParams.has('show_platform')) {
        showPlatform = Boolean(commonConfig.show_platform);
    }

    if (container) {
        container.className = `orientation-${orientation} flow-${flow}`;
    }
}

// Precompiled regular expressions for high throughput
const REGEX_ESCAPE = /[&<>"']/g;
const ESCAPE_MAP = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
const REGEX_KICK_EMOTE = /\[emote:(\d+):([^\]]+)\]/g;
const REGEX_TIKTOK_STICKER = /\[([a-zA-Z0-9_\-]+)\]/g;

// 2. Color Contrast & String Utilities
/**
 * O(1) W3C relative luminance check. If the username color is too dark for
 * dark overlay backgrounds, it automatically boosts the luminance to ensure
 * high readability without altering the original user tint.
 * @param {string} hex
 * @returns {string} Safe readable hex color
 */
function ensureReadableColor(hex) {
    if (!hex || typeof hex !== 'string' || !hex.startsWith('#')) {
        return hex || '#FAFAFA';
    }
    let clean = hex.slice(1);
    if (clean.length === 3) {
        clean = clean.split('').map(c => c + c).join('');
    }
    if (clean.length !== 6) return hex;

    const r = parseInt(clean.substring(0, 2), 16);
    const g = parseInt(clean.substring(2, 4), 16);
    const b = parseInt(clean.substring(4, 6), 16);
    if (isNaN(r) || isNaN(g) || isNaN(b)) return hex;

    // Standard relative luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    if (luminance < 0.38) {
        const boost = c => Math.min(255, Math.round(c + (255 - c) * 0.55));
        const nr = boost(r).toString(16).padStart(2, '0');
        const ng = boost(g).toString(16).padStart(2, '0');
        const nb = boost(b).toString(16).padStart(2, '0');
        return `#${nr}${ng}${nb}`;
    }
    return hex;
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(REGEX_ESCAPE, m => ESCAPE_MAP[m]);
}

// 3. Emote Parsing Pipeline
function parseTwitchEmotes(rawMessage, emotesTag) {
    if (!emotesTag || typeof emotesTag !== 'string' || !emotesTag.includes(':') || emotesTag.startsWith('[')) {
        return null;
    }

    const ranges = [];
    const groups = emotesTag.split('/');
    for (let i = 0; i < groups.length; i++) {
        const group = groups[i];
        if (!group.includes(':')) continue;
        const [emoteId, rangeStr] = group.split(':');
        if (!rangeStr) continue;

        const rangeList = rangeStr.split(',');
        for (let j = 0; j < rangeList.length; j++) {
            const r = rangeList[j];
            if (!r.includes('-')) continue;
            const [start, end] = r.split('-').map(Number);
            if (!isNaN(start) && !isNaN(end)) {
                ranges.push({ emoteId, start, end });
            }
        }
    }

    if (ranges.length === 0) return null;

    ranges.sort((a, b) => a.start - b.start);
    const chars = Array.from(rawMessage);
    let result = '';
    let lastIdx = 0;

    for (let i = 0; i < ranges.length; i++) {
        const { emoteId, start, end } = ranges[i];
        if (start >= lastIdx) {
            const beforeText = chars.slice(lastIdx, start).join('');
            const emoteCode = chars.slice(start, end + 1).join('');
            result += escapeHtml(beforeText);
            result += `<img src="https://static-cdn.jtvnw.net/emoticons/v2/${emoteId}/default/dark/2.0" alt="${escapeHtml(emoteCode)}" title="${escapeHtml(emoteCode)}" class="chat-emote" loading="lazy" decoding="async" />`;
            lastIdx = end + 1;
        }
    }
    result += escapeHtml(chars.slice(lastIdx).join(''));
    return result;
}

function parseYouTubeEmotes(messageHtml, emotesTag) {
    if (!emotesTag) return messageHtml;
    try {
        let ytEmotes = [];
        if (typeof emotesTag === 'string' && emotesTag.trim().startsWith('[')) {
            ytEmotes = JSON.parse(emotesTag);
        } else if (Array.isArray(emotesTag)) {
            ytEmotes = emotesTag;
        }

        if (Array.isArray(ytEmotes) && ytEmotes.length > 0) {
            const seenNames = new Set();
            for (let i = 0; i < ytEmotes.length; i++) {
                const em = ytEmotes[i];
                if (em && em.name && em.url && !seenNames.has(em.name)) {
                    seenNames.add(em.name);
                    const cleanLabel = escapeHtml(em.name.replace(/^:+|:+$/g, ''));
                    const escUrl = escapeHtml(em.url);
                    const escapedBase = em.name.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
                    const regex = new RegExp(escapedBase, 'g');
                    messageHtml = messageHtml.replace(regex, `<img src="${escUrl}" alt="${cleanLabel}" title="${cleanLabel}" class="chat-emote" loading="lazy" decoding="async" />`);
                }
            }
        }
    } catch (e) {
        console.warn("[Chat Overlay] Error parseando emotes de YouTube:", e);
    }
    return messageHtml;
}

function parseTikTokEmotes(messageHtml, emotesTag) {
    if (!emotesTag) return messageHtml;
    try {
        let ttEmotes = [];
        if (typeof emotesTag === 'string' && emotesTag.trim().startsWith('[')) {
            ttEmotes = JSON.parse(emotesTag);
        } else if (Array.isArray(emotesTag)) {
            ttEmotes = emotesTag;
        }

        if (Array.isArray(ttEmotes) && ttEmotes.length > 0) {
            const seenNames = new Set();
            for (let i = 0; i < ttEmotes.length; i++) {
                const em = ttEmotes[i];
                if (em && em.name && em.url) {
                    const rawName = String(em.name).trim();
                    if (seenNames.has(rawName)) continue;
                    seenNames.add(rawName);

                    const cleanName = rawName.replace(/^\[+|\]+$/g, '');
                    const cleanLabel = escapeHtml(cleanName);
                    const escUrl = escapeHtml(em.url);
                    const escapedBase = cleanName.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
                    const regex = new RegExp(`\\[${escapedBase}\\]|\\b${escapedBase}\\b`, 'g');
                    messageHtml = messageHtml.replace(regex, `<img src="${escUrl}" alt="${cleanLabel}" title="${cleanLabel}" class="chat-emote" loading="lazy" decoding="async" />`);
                }
            }
        }
    } catch (e) {
        console.warn("[Chat Overlay] Error parseando emotes de TikTok:", e);
    }
    return messageHtml;
}

function parseKickEmotes(messageHtml) {
    return messageHtml.replace(REGEX_KICK_EMOTE, (match, id, name) => {
        return `<img src="https://files.kick.com/emotes/${id}/fullsize" alt="${escapeHtml(name)}" title="${escapeHtml(name)}" class="chat-emote" loading="lazy" decoding="async" />`;
    });
}

function parseTikTokStickers(messageHtml) {
    if (typeof TIKTOK_STICKERS === 'undefined') return messageHtml;
    return messageHtml.replace(REGEX_TIKTOK_STICKER, (match, code) => {
        const key = code.toLowerCase();
        const item = TIKTOK_STICKERS[key];
        if (item) {
            const label = escapeHtml(code);
            return `<img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/${item.svg}.svg" alt="${label}" title="${label}" class="chat-emote" loading="lazy" decoding="async" onerror="this.outerHTML='${item.emoji}'" />`;
        }
        return match;
    });
}

function formatChatMessage(data) {
    let rawText = data.message || '';
    let isAction = false;

    // IRC /me or ACTION detection
    if (rawText.startsWith('\u0001ACTION ') && rawText.endsWith('\u0001')) {
        isAction = true;
        rawText = rawText.slice(8, -1).trim();
    } else if (rawText.startsWith('/me ')) {
        isAction = true;
        rawText = rawText.slice(4).trim();
    }

    let safeMsg = '';

    // Suppress Twitch GIF placeholder, Giphy links, or redundant gif_url from text display if gif_url is present
    if (data.gif_url) {
        rawText = rawText.replace(/\[.*? GIF by .*?\]/gi, '').trim();
        if (rawText.includes(data.gif_url)) {
            rawText = rawText.replace(data.gif_url, '').trim();
        }
        const giphyIdMatch = data.gif_url.match(/\/media\/([a-zA-Z0-9_-]+)/i);
        if (giphyIdMatch && giphyIdMatch[1]) {
            const gid = giphyIdMatch[1];
            const gidRegex = new RegExp(`https?:\\/\\/[^\\s]*${gid}[^\\s]*`, 'gi');
            rawText = rawText.replace(gidRegex, '').trim();
        }
        if (data.gif_url.includes('giphy.com')) {
            rawText = rawText.replace(/https?:\/\/(www\.)?giphy\.com\/gifs\/[^\s]+/gi, '').trim();
            rawText = rawText.replace(/https?:\/\/media[0-9]*\.giphy\.com\/[^\s]+/gi, '').trim();
        }
        const cleanBaseUrl = data.gif_url.split('?')[0];
        if (cleanBaseUrl && rawText.includes(cleanBaseUrl)) {
            rawText = rawText.replace(cleanBaseUrl, '').trim();
        }
    }

    // 1. Twitch native emotes if provided
    if (data.platform === 'twitch' && data.emotes_tag) {
        const twitchHtml = parseTwitchEmotes(rawText, data.emotes_tag);
        if (twitchHtml !== null) {
            safeMsg = twitchHtml;
        }
    }

    // 2. Default HTML escaping if not formatted by Twitch
    if (!safeMsg) {
        safeMsg = escapeHtml(rawText);
    }

    // 3. YouTube custom emotes
    if (data.platform === 'youtube' && data.emotes_tag) {
        safeMsg = parseYouTubeEmotes(safeMsg, data.emotes_tag);
    }

    // 4. TikTok custom emotes
    if (data.platform === 'tiktok' && data.emotes_tag) {
        safeMsg = parseTikTokEmotes(safeMsg, data.emotes_tag);
    }

    // 5. Kick emotes
    safeMsg = parseKickEmotes(safeMsg);

    // 6. TikTok twemoji stickers
    safeMsg = parseTikTokStickers(safeMsg);

    return { formattedHtml: safeMsg, isAction };
}

function isOnlyEmotes(htmlContent) {
    if (!htmlContent || typeof htmlContent !== 'string') return false;
    const stripped = htmlContent
        .replace(/<img[^>]*>/gi, '')
        .replace(/&nbsp;/gi, '')
        .replace(/[\s\r\n\t]+/g, '');
    if (stripped.length > 0) {
        return false;
    }
    const emoteMatches = htmlContent.match(/<img[^>]*class=["'][^"']*chat-emote[^"']*["'][^>]*>/gi);
    const count = emoteMatches ? emoteMatches.length : 0;
    return count >= 1 && count <= 6;
}

function getRoleClass(badges) {
    if (!badges || !Array.isArray(badges)) return 'default';
    if (badges.includes('broadcaster')) return 'broadcaster';
    if (badges.includes('moderator') || badges.includes('mod')) return 'moderator';
    if (badges.includes('vip')) return 'vip';
    if (badges.includes('subscriber') || badges.includes('sub') || badges.includes('premium') || badges.includes('prime')) return 'subscriber';
    if (badges.includes('bot') || badges.includes('twitchbot')) return 'bot';
    return 'default';
}


const AVATAR_GRADIENTS = [
    'linear-gradient(135deg, #3b82f6, #1d4ed8)',
    'linear-gradient(135deg, #8b5cf6, #6d28d9)',
    'linear-gradient(135deg, #ec4899, #be185d)',
    'linear-gradient(135deg, #10b981, #047857)',
    'linear-gradient(135deg, #f59e0b, #b45309)',
    'linear-gradient(135deg, #06b6d4, #0e7490)',
    'linear-gradient(135deg, #f43f5e, #be123c)',
    'linear-gradient(135deg, #6366f1, #4338ca)'
];

function getAvatarGradient(user) {
    if (!user) return AVATAR_GRADIENTS[0];
    let hash = 0;
    for (let i = 0; i < user.length; i++) {
        hash = ((hash << 5) - hash) + user.charCodeAt(i);
        hash |= 0;
    }
    return AVATAR_GRADIENTS[Math.abs(hash) % AVATAR_GRADIENTS.length];
}

function getAvatarPlatformBadgeSvg(platform) {
    const plat = (platform || 'kick').toLowerCase();
    const iconSvg = (typeof ICONS !== 'undefined' && ICONS[plat]) ? ICONS[plat] : (typeof ICONS !== 'undefined' ? ICONS.kick : '');
    const title = plat.charAt(0).toUpperCase() + plat.slice(1);
    return `<span class="avatar-badge avatar-platform-${plat}" title="${title}">${iconSvg}</span>`;
}

const clientAvatarCache = new Map();

function resolveAvatarUrl(platform, username) {
    if (!username) return Promise.resolve('');
    const cleanUser = username.trim().toLowerCase();
    const key = `${platform}:${cleanUser}`;
    if (clientAvatarCache.has(key)) {
        return Promise.resolve(clientAvatarCache.get(key));
    }

    if (platform === 'twitch') {
        return fetch(`https://decapi.me/twitch/avatar/${encodeURIComponent(cleanUser)}`)
            .then(res => res.ok ? res.text() : '')
            .then(url => {
                const clean = url && url.trim().startsWith('http') ? url.trim() : '';
                if (clean) clientAvatarCache.set(key, clean);
                return clean;
            })
            .catch(() => '');
    } else if (platform === 'kick') {
        return fetch(`https://kick.com/api/v1/channels/${encodeURIComponent(cleanUser)}`)
            .then(res => res.ok ? res.json() : null)
            .then(json => {
                const pic = (json && json.user && json.user.profile_pic) ? json.user.profile_pic : '';
                if (pic) clientAvatarCache.set(key, pic);
                return pic;
            })
            .catch(() => '');
    }
    return Promise.resolve('');
}

// 4. DOM Construction & Message Rendering
function addMessage(data) {
    if (!showBots && data.badges && data.badges.includes('bot')) {
        return;
    }
    if (hideCommands && data.content && typeof data.content === 'string' && data.content.trim().startsWith('!')) {
        return;
    }

    let animClass = 'anim-fade';
    if (animIn === 'pop') {
        animClass = 'anim-pop';
    } else if (animIn === 'slide') {
        animClass = 'anim-slide';
    }

    const roleClass = getRoleClass(data.badges);
    const msgBox = document.createElement('div');
    msgBox.className = `message-box theme-${theme} role-${roleClass} ${animClass}`;
    msgBox.style.fontSize = fontSize;

    if (data.is_highlighted || data.highlighted) {
        msgBox.classList.add('highlighted');
    }

    const safeUsernameColor = ensureReadableColor(data.color);

    // 1. Avatar construction (image or initial letter fallback)
    const avatarWrap = document.createElement('div');
    avatarWrap.className = 'avatar-wrap';

    const platform = (data.platform || 'kick').toLowerCase();
    const cleanUser = (data.user || '').trim().toLowerCase();
    const clientAvatarKey = `${platform}:${cleanUser}`;

    let effectiveAvatarUrl = (data.avatar_url && typeof data.avatar_url === 'string') ? data.avatar_url.trim() : '';
    if (!effectiveAvatarUrl && clientAvatarCache.has(clientAvatarKey)) {
        effectiveAvatarUrl = clientAvatarCache.get(clientAvatarKey);
    }

    const firstLetter = (data.user || '?').charAt(0).toUpperCase();
    const fallbackBg = getAvatarGradient(data.user);
    const avatarBadgeSvg = showPlatform ? getAvatarPlatformBadgeSvg(platform) : '';

    if (effectiveAvatarUrl) {
        clientAvatarCache.set(clientAvatarKey, effectiveAvatarUrl);
        const escAvatar = escapeHtml(effectiveAvatarUrl);
        avatarWrap.innerHTML = `
            <img src="${escAvatar}" alt="${escapeHtml(data.user)}" class="avatar-img" onerror="this.outerHTML='<div class=\\'avatar-fallback\\' style=\\'background: ${fallbackBg}\\'>${firstLetter}</div>'"/>
            ${avatarBadgeSvg}
        `;
    } else {
        avatarWrap.innerHTML = `
            <div class="avatar-fallback" style="background: ${fallbackBg}">${firstLetter}</div>
            ${avatarBadgeSvg}
        `;
        if (cleanUser) {
            resolveAvatarUrl(platform, data.user).then(resolvedUrl => {
                if (resolvedUrl && avatarWrap && avatarWrap.isConnected) {
                    const img = new Image();
                    img.className = 'avatar-img';
                    img.alt = escapeHtml(data.user);
                    img.onload = () => {
                        const fallbackEl = avatarWrap.querySelector('.avatar-fallback');
                        if (fallbackEl && fallbackEl.parentNode === avatarWrap) {
                            avatarWrap.replaceChild(img, fallbackEl);
                        }
                    };
                    img.src = resolvedUrl;
                }
            });
        }
    }
    msgBox.appendChild(avatarWrap);

    // 2. Body wrapper
    const bodyWrap = document.createElement('div');
    bodyWrap.className = 'message-body-wrap';

    // Header construction
    const header = document.createElement('div');
    header.className = 'message-header';

    const headerLeft = document.createElement('div');
    headerLeft.className = 'header-left';

    // Badges & Roles resolution (O(1) lookups via resolveBadge)
    if (showBadges && data.badges && Array.isArray(data.badges) && typeof resolveBadge === 'function') {
        for (let i = 0; i < data.badges.length; i++) {
            const badgeKey = data.badges[i];
            const resolved = resolveBadge(platform, badgeKey);
            if (!resolved) continue;

            const badgeSpan = document.createElement('span');
            if (resolved.isLevel) {
                if (resolved.isGeneric) {
                    badgeSpan.className = 'badge badge-level badge-level-generic';
                    badgeSpan.innerText = resolved.text;
                } else {
                    badgeSpan.className = 'badge badge-level';
                    badgeSpan.innerHTML = resolved.html;
                }
            } else {
                badgeSpan.className = `badge badge-${badgeKey}${resolved.isGeneric ? ' badge-generic' : ''}`;
                badgeSpan.innerHTML = resolved.html;
            }
            badgeSpan.title = resolved.title;
            headerLeft.appendChild(badgeSpan);
        }
    }

    // Username construction
    const nameSpan = document.createElement('span');
    nameSpan.className = 'username';
    nameSpan.style.color = safeUsernameColor;
    nameSpan.innerText = data.user || '';
    headerLeft.appendChild(nameSpan);
    header.appendChild(headerLeft);

    // Timestamp without seconds: [HH:MM]
    if (showTime) {
        const timeSpan = document.createElement('span');
        timeSpan.className = 'timestamp';
        const now = new Date();
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        timeSpan.innerText = `[${hh}:${mm}]`;
        header.appendChild(timeSpan);
    }

    bodyWrap.appendChild(header);

    // Content construction
    const { formattedHtml, isAction } = formatChatMessage(data);
    const content = document.createElement('div');
    content.className = `message-content${isAction ? ' action' : ''}`;

    if (formattedHtml && formattedHtml.trim().length > 0) {
        const textSpan = document.createElement('span');
        textSpan.innerHTML = formattedHtml;
        content.appendChild(textSpan);
    }

    if (showGifs && data.gif_url) {
        const gifWrapper = document.createElement('div');
        gifWrapper.className = 'chat-gif-wrapper';
        const gifImg = document.createElement('img');
        gifImg.className = 'chat-gif';
        gifImg.src = data.gif_url;
        gifImg.alt = 'GIF';
        gifImg.loading = 'lazy';
        gifImg.onload = () => {
            autoScroll();
        };
        gifWrapper.appendChild(gifImg);
        content.appendChild(gifWrapper);
    }

    bodyWrap.appendChild(content);
    msgBox.appendChild(bodyWrap);

    if (bigEmotes && (!showGifs || !data.gif_url) && isOnlyEmotes(formattedHtml)) {
        msgBox.classList.add('only-emotes');
    }

    container.appendChild(msgBox);

    // Prune DOM and maintain limits
    pruneMessages();

    // Auto-scroll
    autoScroll();

    // Auto-fade timer
    if (fadeTime > 0) {
        setTimeout(() => {
            removeMessage(msgBox);
        }, fadeTime * 1000);
    }
}

// 5. Message Lifecycle & Auto-Scroll
function pruneMessages() {
    while (container.children.length > MAX_SAFE_DOM_NODES) {
        const first = container.firstElementChild;
        if (!first) break;
        if (first.classList.contains('fade-out')) {
            container.removeChild(first);
        } else {
            removeMessage(first);
            if (container.children.length > MAX_SAFE_DOM_NODES + 5) {
                container.removeChild(first);
            } else {
                break;
            }
        }
    }
}

function removeMessage(msgBox) {
    if (!msgBox || msgBox.classList.contains('fade-out')) return;
    msgBox.classList.add('fade-out');
    setTimeout(() => {
        if (msgBox.parentNode === container) {
            container.removeChild(msgBox);
        }
    }, 400);
}

function autoScroll() {
    if (orientation === 'horizontal') {
        container.scrollLeft = (flow === 'right-to-left') ? container.scrollWidth : 0;
    } else {
        container.scrollTop = (flow === 'bottom-to-top') ? container.scrollHeight : 0;
    }
}

// 6. WebSocket Connection & Heartbeat Manager
let ws = null;
let reconnectTimer = null;
let heartbeatTimer = null;

function connectWS() {
    if (ws) {
        try { ws.close(); } catch (e) { }
        ws = null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?topic=chat&token=${encodeURIComponent(token)}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = function () {
        console.log("[Chat Overlay] WebSocket conectado exitosamente.");
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        heartbeatTimer = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 15000);
    };

    ws.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'pong') return;
            if (data.event === 'chat_config' && data.config) {
                applyLiveConfig(data.config);
                return;
            }
            addMessage(data);
        } catch (e) {
            console.error("[Chat Overlay] Error parseando evento de chat:", e);
        }
    };

    ws.onerror = function () {
        cleanup();
        scheduleReconnect();
    };

    ws.onclose = function () {
        cleanup();
        scheduleReconnect();
    };
}

function cleanup() {
    if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
        heartbeatTimer = null;
    }
}

function scheduleReconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(connectWS, 3000);
}

// Start WebSocket connection
connectWS();
