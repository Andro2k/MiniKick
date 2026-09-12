/**
 * MiniKick Chat Overlay - Main Client Runtime
 * Handles URL configuration, message DOM rendering, emote parsing,
 * color contrast correction, and WebSocket event stream.
 */

// 1. Configuration & URL Parameters
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token') || '';
const theme = urlParams.get('theme') || 'glass';
const fadeTime = urlParams.get('fade') !== null ? parseInt(urlParams.get('fade'), 10) : 15;
const fontSize = urlParams.get('size') || '14px';
const maxMessages = parseInt(urlParams.get('max'), 10) || 15;
const showBots = urlParams.get('show_bots') !== 'false';
const showTime = urlParams.get('show_time') === 'true';
const orientation = urlParams.get('orientation') || 'vertical';
const defaultFlow = orientation === 'horizontal' ? 'right-to-left' : 'bottom-to-top';
const flow = urlParams.get('flow') || defaultFlow;
const defaultEntry = orientation === 'horizontal' ? 'right' : 'bottom';
const entryDir = urlParams.get('entry') || defaultEntry;
const bigEmotes = urlParams.get('big_emotes') !== 'false';
const edgeFade = urlParams.get('edge_fade') !== 'false';
const animIn = urlParams.get('anim_in') || 'fade';

// Apply theme and base styles
const themeStyle = document.getElementById('theme-style');
if (themeStyle) {
    themeStyle.href = `/css/${theme}.css`;
}
document.documentElement.style.setProperty('--font-size', fontSize);

const container = document.getElementById('chat-container');
if (container) {
    container.classList.add(`orientation-${orientation}`, `flow-${flow}`);
    if (edgeFade) {
        container.classList.add('edge-fade');
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

// 4. DOM Construction & Message Rendering
function addMessage(data) {
    if (!showBots && data.badges && data.badges.includes('bot')) {
        return;
    }

    let animClass = `anim-entry-${entryDir}`;
    if (animIn === 'pop') {
        animClass = 'anim-pop';
    } else if (animIn === 'slide') {
        animClass = 'anim-slide';
    }

    const roleClass = getRoleClass(data.badges);
    const msgBox = document.createElement('div');
    msgBox.className = `message-box theme-${theme} role-${roleClass} ${animClass}`;
    msgBox.style.fontSize = fontSize;

    // Highlighted message support (Channel points, bits, special events)
    if (data.is_highlighted || data.highlighted) {
        msgBox.classList.add('highlighted');
    }

    const safeUsernameColor = ensureReadableColor(data.color);

    // Theme-specific glow accents
    const accentColor = safeUsernameColor || '#2ECD70';
    if (theme === 'neon') {
        msgBox.style.borderColor = accentColor;
        msgBox.style.boxShadow = `0 0 10px ${accentColor}, inset 0 0 5px ${accentColor}`;
    } else if (theme === 'minimal') {
        msgBox.style.setProperty('--author-color', accentColor);
    } else if (theme === 'cyber') {
        msgBox.style.setProperty('--cyber-color', accentColor);
    }

    // Header construction
    const header = document.createElement('div');
    header.className = 'message-header';

    if (showTime) {
        const timeSpan = document.createElement('span');
        timeSpan.className = 'timestamp';
        const now = new Date();
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        const ss = String(now.getSeconds()).padStart(2, '0');
        timeSpan.innerText = `[${hh}:${mm}:${ss}]`;
        header.appendChild(timeSpan);
    }

    // Platform badge
    const platform = (data.platform || 'kick').toLowerCase();
    const platformSpan = document.createElement('span');
    platformSpan.className = `badge badge-platform badge-platform-${platform}`;
    platformSpan.innerHTML = (typeof ICONS !== 'undefined' && ICONS[platform]) ? ICONS[platform] : (typeof ICONS !== 'undefined' ? ICONS.kick : '');
    platformSpan.title = platform.charAt(0).toUpperCase() + platform.slice(1);
    header.appendChild(platformSpan);

    // Badges & Roles resolution (O(1) lookups via resolveBadge)
    if (data.badges && Array.isArray(data.badges) && typeof resolveBadge === 'function') {
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
            header.appendChild(badgeSpan);
        }
    }

    // Username construction
    const nameSpan = document.createElement('span');
    nameSpan.className = 'username';
    nameSpan.style.color = safeUsernameColor;
    nameSpan.innerText = data.user || '';
    if (theme === 'neon') {
        nameSpan.style.textShadow = `0 0 8px ${accentColor}, 0 1px 2px rgba(0, 0, 0, 0.9)`;
    } else if (theme === 'cyber') {
        nameSpan.style.textShadow = `0 0 8px ${accentColor}, 0 1px 2px rgba(0, 0, 0, 0.9)`;
    } else if (theme === 'minimal') {
        nameSpan.style.textShadow = `0 0 10px ${accentColor}, 0 1px 3px rgba(0, 0, 0, 0.95), 0 2px 6px rgba(0, 0, 0, 0.85)`;
    }
    header.appendChild(nameSpan);
    msgBox.appendChild(header);

    // Content construction
    const { formattedHtml, isAction } = formatChatMessage(data);
    const content = document.createElement('div');
    content.className = `message-content${isAction ? ' action' : ''}`;
    const textSpan = document.createElement('span');
    textSpan.innerHTML = formattedHtml;
    content.appendChild(textSpan);
    msgBox.appendChild(content);

    if (bigEmotes && isOnlyEmotes(formattedHtml)) {
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
    while (container.children.length > maxMessages) {
        const first = container.firstElementChild;
        if (!first) break;
        if (first.classList.contains('fade-out')) {
            container.removeChild(first);
        } else {
            removeMessage(first);
            if (container.children.length > maxMessages + 5) {
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
