// version 1.1
let effectList = [];
let currentEffectKey = null;
let debounceTimers = {};
let isUpdatingFromStatus = false;
let lastSentValues = {
    brightness: 50,
    speed: 1.0,
    frequency: 5
};

// Debounce function to prevent rapid firing of commands
function debounce(func, wait) {
    return function(...args) {
        const context = this;
        clearTimeout(debounceTimers[func.name]);
        debounceTimers[func.name] = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

// Throttle function for slider updates
function throttle(func, wait) {
    let inThrottle;
    return function(...args) {
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, wait);
        }
    };
}

function updateStatus() {
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'offline') {
                document.getElementById('offline-warning').style.display = 'block';
                document.getElementById('controls').style.display = 'none';
                return;
            }
            
            document.getElementById('offline-warning').style.display = 'none';
            document.getElementById('controls').style.display = 'block';

            // Prevent slider updates from triggering commands while we update from status
            isUpdatingFromStatus = true;

            // Update display values
            document.getElementById('current-effect').textContent = data.effect || '-';
            document.getElementById('state').textContent = data.state || '-';
            document.getElementById('brightness-display').textContent = data.brightness || '-';
            document.getElementById('speed-display').textContent = data.speed || '-';
            document.getElementById('frequency-display').textContent = data.frequency || '-';

            // Update mode display
            const mode = data.mode || 'playlist';
            document.getElementById('mode-display').textContent = mode.charAt(0).toUpperCase() + mode.slice(1);

            // Update playlist display
            const playlistDisplay = document.getElementById('current-playlist-display');
            if (playlistDisplay && data.playlist) {
                playlistDisplay.textContent = data.playlist;
            } else if (playlistDisplay) {
                playlistDisplay.textContent = 'None';
            }

            // Update dropdown to match current effect
            const effectKey = data.effect_key;
            const dropdown = document.getElementById('effect-select');
            if (effectKey && dropdown.value !== effectKey) {
                dropdown.value = effectKey;
            }

            // Only update sliders if values differ significantly from what we last sent
            const brightness = parseInt(data.brightness) || 50;
            const speed = parseFloat(data.speed) || 1.0;
            const frequency = parseInt(data.frequency) || 5;

            if (Math.abs(brightness - lastSentValues.brightness) > 5) {
                document.getElementById('brightness').value = brightness;
                document.getElementById('brightness-value').textContent = brightness;
                lastSentValues.brightness = brightness;
            }

            if (Math.abs(speed - lastSentValues.speed) > 0.5) {
                document.getElementById('speed').value = Math.round(speed * 10);
                document.getElementById('speed-value').textContent = speed.toFixed(1);
                lastSentValues.speed = speed;
            }

            if (Math.abs(frequency - lastSentValues.frequency) > 1) {
                document.getElementById('frequency').value = frequency;
                document.getElementById('frequency-value').textContent = frequency;
                lastSentValues.frequency = frequency;
            }

            // Load effect options if effect changed or mode is single
            if (mode === 'single' && effectKey && effectKey !== currentEffectKey) {
                loadEffectOptions(effectKey);
                currentEffectKey = effectKey;
            } else if (mode !== 'single') {
                // Hide effect options in playlist mode
                document.getElementById('effect-options-section').style.display = 'none';
                currentEffectKey = null;
            }

            // Re-enable slider updates
            setTimeout(() => {
                isUpdatingFromStatus = false;
            }, 100);
        })
        .catch(err => {
            console.error('Status update failed:', err);
            // If we can't reach the server, show offline warning
            document.getElementById('offline-warning').style.display = 'block';
            document.getElementById('controls').style.display = 'none';
        });
}

function loadEffects() {
    fetch('/api/effects')
        .then(response => response.json())
        .then(data => {
            effectList = data.effects || [];
            const select = document.getElementById('effect-select');
            select.innerHTML = '<option value="">Select Effect...</option>';
            effectList.forEach(effect => {
                const option = document.createElement('option');
                option.value = effect;
                option.textContent = effect;
                select.appendChild(option);
            });
        });
}

function sendCommand(cmd, args = null) {
    const payload = args ? {command: cmd, args: args} : {command: cmd};
    
    // Show loading state
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = 'Sending command...';
    messageDiv.className = 'message';
    messageDiv.style.display = 'block';

    fetch('/api/command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            messageDiv.textContent = data.message || 'Command sent successfully';
            messageDiv.className = 'message success';
            setTimeout(updateStatus, 300); // Wait a bit before updating status
        } else {
            messageDiv.textContent = data.message || 'Command failed';
            messageDiv.className = 'message error';
        }
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    })
    .catch(err => {
        messageDiv.textContent = 'Command failed: ' + err.message;
        messageDiv.className = 'message error';
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
        console.error('Command error:', err);
    });
}

// Debounced version of sendCommand for sliders
const debouncedSendCommand = debounce(sendCommand, 300);

function selectEffect() {
    const effect = document.getElementById('effect-select').value;
    if (effect) {
        sendCommand('set', effect);
    }
}

function updateSlider(type) {
    if (isUpdatingFromStatus) return;
    
    const slider = document.getElementById(type);
    const value = slider.value;
    const valueSpan = document.getElementById(type + '-value');
    
    if (type === 'speed') {
        const speedValue = (value / 10).toFixed(1);
        valueSpan.textContent = speedValue;
        lastSentValues.speed = parseFloat(speedValue);
    } else {
        valueSpan.textContent = value;
        if (type === 'brightness') {
            lastSentValues.brightness = parseInt(value);
        } else if (type === 'frequency') {
            lastSentValues.frequency = parseInt(value);
        }
    }
}

function setBrightness() {
    if (isUpdatingFromStatus) return;
    const value = document.getElementById('brightness').value;
    debouncedSendCommand('brightness', value);
}

function setSpeed() {
    if (isUpdatingFromStatus) return;
    const value = (document.getElementById('speed').value / 10).toFixed(1);
    debouncedSendCommand('speed', value);
}

function setFrequency() {
    if (isUpdatingFromStatus) return;
    const value = document.getElementById('frequency').value;
    debouncedSendCommand('frequency', value);
}

function loadEffectOptions(effectKey) {
    fetch('/api/effect/' + effectKey + '/options')
        .then(response => response.json())
        .then(data => {
            if (!data.options || data.options.length === 0) {
                document.getElementById('effect-options-section').style.display = 'none';
                return;
            }

            document.getElementById('effect-options-section').style.display = 'block';
            const container = document.getElementById('effect-options-container');
            container.innerHTML = '';

            data.options.forEach(option => {
                const optDiv = document.createElement('div');
                optDiv.className = 'slider-container';

                if (option.type === 'boolean') {
                    optDiv.innerHTML = `
                        <div class="slider-label">
                            <span>${option.description}</span>
                            <span id="${option.key}-value">${option.default ? 'On' : 'Off'}</span>
                        </div>
                        <button id="${option.key}-toggle" onclick="toggleEffectOption('${option.key}')"
                                style="width: 100%;">${option.default ? 'On' : 'Off'}</button>
                    `;
                } else if (option.type === 'enum') {
                    // Dropdown for enum types (e.g., font selection)
                    optDiv.innerHTML = `
                        <div class="slider-label">
                            <span>${option.description}</span>
                        </div>
                        <select id="${option.key}" class="effect-selector" onchange="setEnumEffectOption('${option.key}')">
                            <option value="">Loading...</option>
                        </select>
                    `;
                    // Populate dropdown based on the key
                    if (option.key === 'font_name') {
                        fetch('/api/fonts')
                            .then(response => response.json())
                            .then(fontData => {
                                const select = document.getElementById(option.key);
                                select.innerHTML = '';
                                fontData.fonts.forEach(font => {
                                    const opt = document.createElement('option');
                                    opt.value = font;
                                    opt.textContent = font;
                                    if (font === option.default) {
                                        opt.selected = true;
                                    }
                                    select.appendChild(opt);
                                });
                            })
                            .catch(err => {
                                console.error('Failed to load fonts:', err);
                                const select = document.getElementById(option.key);
                                select.innerHTML = '<option value="6x10.bdf">6x10.bdf</option>';
                            });
                    }
                } else if (option.type === 'number') {
                    // Determine appropriate min/max based on default value
                    let min = 0;
                    let max = 100;
                    let step = 1;

                    if (typeof option.default === 'number') {
                        if (option.default <= 1) {
                            min = 0;
                            max = 1;
                            step = 0.1;
                        } else if (option.default <= 10) {
                            min = 0;
                            max = Math.max(20, option.default * 2);
                        } else if (option.default <= 100) {
                            min = 0;
                            max = Math.max(200, option.default * 2);
                        } else {
                            min = 0;
                            max = Math.max(500, option.default * 2);
                        }

                        // Special handling for known option ranges
                        if (option.key === 'intensity' || option.key === 'cooling') {
                            min = 1;
                            max = 10;
                        } else if (option.key === 'frequency') {
                            min = 1;
                            max = 10;
                        } else if (option.key === 'speed') {
                            min = 0.1;
                            max = 5.0;
                            step = 0.1;
                        } else if (option.key === 'saturation') {
                            min = 0;
                            max = 1;
                            step = 0.1;
                        } else if (option.key === 'gravity') {
                            min = 0.01;
                            max = 0.5;
                            step = 0.01;
                        } else if (option.key === 'color_hue') {
                            // Color hue uses full 0-360 range
                            min = 0;
                            max = 360;
                            step = 1;
                        } else if (option.key === 'scroll_speed') {
                            min = 0;
                            max = 200;
                            step = 0.1;
                        }
                    }

                    optDiv.innerHTML = `
                        <div class="slider-label">
                            <span>${option.description}</span>
                            <span id="${option.key}-value">${option.default}</span>
                        </div>
                        <input type="range" id="${option.key}"
                               min="${min}" max="${max}" step="${step}" value="${option.default}"
                               oninput="updateEffectOption('${option.key}')"
                               onchange="setEffectOption('${option.key}')">
                    `;
                } else if (option.type === 'text') {
                    optDiv.innerHTML = `
                        <div class="slider-label">
                            <span>${option.description}</span>
                        </div>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="${option.key}" value="${option.default}"
                                   style="flex: 1; padding: 10px; border-radius: 5px; border: 2px solid #00ff88; background: #1a1a1a; color: #e0e0e0; font-size: 14px;"
                                   placeholder="Enter text to display"
                                   onkeypress="if(event.key==='Enter') setTextEffectOption('${option.key}')">
                            <button onclick="setTextEffectOption('${option.key}')"
                                    style="padding: 10px 20px; min-width: 100px;">
                                💾 Save
                            </button>
                        </div>
                    `;
                }
                container.appendChild(optDiv);
            });
        })
        .catch(err => {
            console.error('Failed to load effect options:', err);
            document.getElementById('effect-options-section').style.display = 'none';
        });
}

function updateEffectOption(key) {
    const value = document.getElementById(key).value;
    document.getElementById(key + '-value').textContent = value;
}

function setEffectOption(key) {
    if (isUpdatingFromStatus) return;
    const value = document.getElementById(key).value;
    debouncedSendCommand('opt', key + '=' + value);
}

function setTextEffectOption(key) {
    if (isUpdatingFromStatus) return;
    const value = document.getElementById(key).value;
    if (!value.trim()) {
        showMessage('Please enter some text', 'error');
        return;
    }
    // Show immediate feedback
    showMessage('Saving text...', 'success');
    sendCommand('opt', key + '=' + value);
}

function setEnumEffectOption(key) {
    if (isUpdatingFromStatus) return;
    const value = document.getElementById(key).value;
    if (!value) {
        showMessage('Please select a value', 'error');
        return;
    }
    // Show immediate feedback
    showMessage('Updating ' + key + '...', 'success');
    sendCommand('opt', key + '=' + value);
}

function toggleEffectOption(key) {
    if (isUpdatingFromStatus) return;
    const button = document.getElementById(key + '-toggle');
    const valueSpan = document.getElementById(key + '-value');
    const currentValue = button.textContent === 'On';
    const newValue = !currentValue;

    button.textContent = newValue ? 'On' : 'Off';
    valueSpan.textContent = newValue ? 'On' : 'Off';
    sendCommand('opt', key + '=' + newValue);
}

function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.textContent = text;
    msg.className = 'message ' + type;
    msg.style.display = 'block';
    setTimeout(() => {
        msg.style.display = 'none';
    }, 3000);
}

// Playlist Management
let currentPlaylistData = null;

async function loadPlaylists() {
    try {
        const response = await fetch('/api/playlists');
        const data = await response.json();
        const select = document.getElementById('playlist-select');
        select.innerHTML = '<option value="">Select Playlist...</option>';
        data.playlists.forEach(p => {
            const option = document.createElement('option');
            option.value = p.name;
            option.textContent = p.name + ' (' + p.effect_count + ' effects)';
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading playlists:', error);
    }
}

async function loadPlaylist() {
    const name = document.getElementById('playlist-select').value;
    if (!name) return;

    try {
        const response = await fetch('/api/playlist/' + name + '/load', {method: 'POST'});
        const data = await response.json();
        if (data.success) {
            showMessage('Loaded playlist: ' + name, 'success');
            setTimeout(updateStatus, 300);
        } else {
            showMessage(data.error || 'Failed to load playlist', 'error');
        }
    } catch (error) {
        showMessage('Error loading playlist', 'error');
    }
}

async function showPlaylistEditor() {
    const name = document.getElementById('playlist-select').value;
    if (!name) {
        showMessage('Select a playlist first', 'error');
        return;
    }

    try {
        const response = await fetch('/api/playlist/' + name);
        currentPlaylistData = await response.json();
        document.getElementById('editor-playlist-name').textContent = name;
        renderPlaylistEffects();
        document.getElementById('playlist-editor-modal').style.display = 'flex';
    } catch (error) {
        showMessage('Error loading playlist', 'error');
    }
}

function renderPlaylistEffects() {
    const container = document.getElementById('playlist-effects-list');
    container.innerHTML = '';
    currentPlaylistData.effects.forEach((effect, idx) => {
        const div = document.createElement('div');
        div.className = 'effect-item';

        // Build parameter info string
        let paramInfo = 'Duration: ' + (effect.duration || 8) + 's';
        if (effect.params) {
            if (effect.params.brightness !== undefined) paramInfo += ', Brightness: ' + effect.params.brightness;
            if (effect.params.frequency !== undefined) paramInfo += ', Frequency: ' + effect.params.frequency;
            if (effect.params.speed !== undefined) paramInfo += ', Speed: ' + effect.params.speed;
        }

        div.innerHTML = '<div><div style="font-weight: bold;">' + effect.key + '</div>' +
            '<div style="font-size: 0.9em; color: #888;">' + paramInfo + '</div></div>' +
            '<div class="effect-item-controls">' +
            '<button onclick="removeEffectFromPlaylist(' + idx + ')">Remove</button>' +
            '<button onclick="editEffectParams(' + idx + ')">Edit</button>' +
            '</div>';
        container.appendChild(div);
    });
}

function removeEffectFromPlaylist(idx) {
    currentPlaylistData.effects.splice(idx, 1);
    renderPlaylistEffects();
}

function editEffectParams(idx) {
    const effect = currentPlaylistData.effects[idx];

    // Edit duration
    const durationStr = prompt('Duration for ' + effect.key + ' (seconds):', effect.duration || 8);
    if (durationStr !== null) {
        effect.duration = parseInt(durationStr);
    }

    // Edit brightness
    const currentBrightness = effect.params && effect.params.brightness !== undefined ? effect.params.brightness : '';
    const brightnessStr = prompt('Brightness for ' + effect.key + ' (0-100, leave empty for default):', currentBrightness);
    if (brightnessStr !== null && brightnessStr !== '') {
        if (!effect.params) effect.params = {};
        effect.params.brightness = parseInt(brightnessStr);
    } else if (brightnessStr === '') {
        if (effect.params) delete effect.params.brightness;
    }

    // Edit frequency
    const currentFrequency = effect.params && effect.params.frequency !== undefined ? effect.params.frequency : '';
    const frequencyStr = prompt('Frequency for ' + effect.key + ' (1-10, leave empty for default):', currentFrequency);
    if (frequencyStr !== null && frequencyStr !== '') {
        if (!effect.params) effect.params = {};
        effect.params.frequency = parseInt(frequencyStr);
    } else if (frequencyStr === '') {
        if (effect.params) delete effect.params.frequency;
    }

    // Edit speed
    const currentSpeed = effect.params && effect.params.speed !== undefined ? effect.params.speed : '';
    const speedStr = prompt('Speed for ' + effect.key + ' (0.1-5.0, leave empty for default):', currentSpeed);
    if (speedStr !== null && speedStr !== '') {
        if (!effect.params) effect.params = {};
        effect.params.speed = parseFloat(speedStr);
    } else if (speedStr === '') {
        if (effect.params) delete effect.params.speed;
    }

    // Re-render to show updated values
    renderPlaylistEffects();
}

async function savePlaylistChanges() {
    const name = document.getElementById('editor-playlist-name').textContent;
    try {
        const response = await fetch('/api/playlist/' + name, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(currentPlaylistData)
        });
        const data = await response.json();
        if (data.success) {
            showMessage('Playlist saved', 'success');
            closePlaylistEditor();
            loadPlaylists();
        } else {
            showMessage(data.error || 'Failed to save playlist', 'error');
        }
    } catch (error) {
        showMessage('Error saving playlist', 'error');
    }
}

function closePlaylistEditor() {
    document.getElementById('playlist-editor-modal').style.display = 'none';
}

async function showCreatePlaylist() {
    const name = prompt('Enter playlist name:');
    if (!name) return;
    const description = prompt('Enter description (optional):') || '';

    try {
        const response = await fetch('/api/playlist', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, description})
        });
        const data = await response.json();
        if (data.success) {
            showMessage('Created playlist: ' + name, 'success');
            await loadPlaylists();

            // Auto-select the new playlist and open editor
            const select = document.getElementById('playlist-select');
            select.value = name;

            // Open the editor for the new playlist
            setTimeout(() => showPlaylistEditor(), 300);
        } else {
            showMessage(data.error || 'Failed to create playlist', 'error');
        }
    } catch (error) {
        showMessage('Error creating playlist', 'error');
    }
}

async function deleteCurrentPlaylist() {
    const name = document.getElementById('playlist-select').value;
    if (!name) {
        showMessage('Select a playlist first', 'error');
        return;
    }
    if (!confirm('Delete playlist "' + name + '"?')) return;

    try {
        const response = await fetch('/api/playlist/' + name, {method: 'DELETE'});
        const data = await response.json();
        if (data.success) {
            showMessage('Playlist deleted', 'success');
            loadPlaylists();
        } else {
            showMessage(data.error || 'Failed to delete playlist', 'error');
        }
    } catch (error) {
        showMessage('Error deleting playlist', 'error');
    }
}

function showAddEffectDialog() {
    if (!effectList || effectList.length === 0) {
        showMessage('No effects available', 'error');
        return;
    }

    // Create a simple dialog to select effect
    const effectKey = prompt('Enter effect name:\n\nAvailable effects:\n' + effectList.join(', '));
    if (!effectKey) return;

    // Validate effect exists
    if (!effectList.includes(effectKey)) {
        showMessage('Invalid effect: ' + effectKey, 'error');
        return;
    }

    // Ask for optional parameters
    const durationStr = prompt('Duration in seconds (default: 8):');
    const duration = durationStr ? parseInt(durationStr) : 8;

    const brightnessStr = prompt('Brightness 0-100 (leave empty for default):');
    const brightness = brightnessStr ? parseInt(brightnessStr) : null;

    const frequencyStr = prompt('Frequency 1-10 (leave empty for default):');
    const frequency = frequencyStr ? parseInt(frequencyStr) : null;

    const speedStr = prompt('Speed 0.1-5.0 (leave empty for default):');
    const speed = speedStr ? parseFloat(speedStr) : null;

    // Add effect to current playlist data
    const newEffect = {
        key: effectKey,
        duration: duration,
        params: {},
        options: {}
    };

    if (brightness !== null) newEffect.params.brightness = brightness;
    if (frequency !== null) newEffect.params.frequency = frequency;
    if (speed !== null) newEffect.params.speed = speed;

    currentPlaylistData.effects.push(newEffect);
    renderPlaylistEffects();
    showMessage('Added ' + effectKey + ' to playlist', 'success');
}

// Initialize
function init() {
    updateStatus();
    loadEffects();
    loadPlaylists();
    setInterval(updateStatus, 2000);
}

// Start when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
