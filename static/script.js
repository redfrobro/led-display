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

            // Update mood display and dropdown
            const mood = data.mood || 'default';
            document.getElementById('mood-display').textContent = mood;
            const moodSelect = document.getElementById('mood-select');
            if (moodSelect && moodSelect.value !== mood) {
                moodSelect.value = mood;
            }

            // Update daemon control buttons based on effects_running
            const effectsRunning = data.effects_running !== false;
            const stopBtn = document.getElementById('stop-btn');
            const startBtn = document.getElementById('start-btn');
            if (stopBtn) stopBtn.style.display = effectsRunning ? 'block' : 'none';
            if (startBtn) startBtn.style.display = effectsRunning ? 'none' : 'block';

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

function setMood() {
    const mood = document.getElementById('mood-select').value;
    sendCommand('mood', mood);
}

function stopEffects() {
    sendCommand('stop');
}

function startEffects() {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = 'Starting effects...';
    messageDiv.className = 'message';
    messageDiv.style.display = 'block';

    fetch('/api/start', {method: 'POST', headers: {'Content-Type': 'application/json'}})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                messageDiv.textContent = data.message || 'Effects started';
                messageDiv.className = 'message success';
                setTimeout(updateStatus, 500);
            } else {
                messageDiv.textContent = data.message || 'Failed to start effects';
                messageDiv.className = 'message error';
            }
            setTimeout(() => { messageDiv.style.display = 'none'; }, 3000);
        })
        .catch(err => {
            messageDiv.textContent = 'Error: ' + err.message;
            messageDiv.className = 'message error';
            setTimeout(() => { messageDiv.style.display = 'none'; }, 3000);
        });
}

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

// Effect editor slider functions
function updateEffectSlider(type) {
    const slider = document.getElementById('effect-' + type);
    const valueSpan = document.getElementById('effect-' + type + '-value');

    if (!slider || !valueSpan) return;

    const value = slider.value;
    if (type === 'speed') {
        // Speed slider: 1-50 represents 0.1-5.0
        const speedValue = (value / 10).toFixed(1);
        valueSpan.textContent = speedValue;
    } else {
        valueSpan.textContent = value;
    }
}

function updateEffectOptionSlider(sliderId) {
    const slider = document.getElementById(sliderId);
    const valueSpan = document.getElementById(sliderId + '-value');
    if (slider && valueSpan) {
        valueSpan.textContent = slider.value;
    }
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
let currentEffectIndex = null; // For editing existing effect

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
        document.getElementById('editor-playlist-description').textContent = currentPlaylistData.description || 'No description';
        document.getElementById('editor-playlist-count').textContent = currentPlaylistData.effects.length;
        document.getElementById('editor-mood').value = currentPlaylistData.mood || '';
        renderPlaylistEffects();
        document.getElementById('playlist-editor-modal').style.display = 'flex';
    } catch (error) {
        showMessage('Error loading playlist', 'error');
    }
}

function renderPlaylistEffects() {
    const container = document.getElementById('playlist-effects-list');
    container.innerHTML = '';

    if (currentPlaylistData.effects.length === 0) {
        container.innerHTML = '<div class="empty-message">No effects in playlist. Click "Add Effect" to get started.</div>';
        return;
    }

    currentPlaylistData.effects.forEach((effect, idx) => {
        const div = document.createElement('div');
        div.className = 'effect-item';
        div.setAttribute('data-index', idx);
        div.setAttribute('draggable', 'true');

        // Add drag event listeners
        div.addEventListener('dragstart', handleDragStart);
        div.addEventListener('dragover', handleDragOver);
        div.addEventListener('dragleave', handleDragLeave);
        div.addEventListener('drop', handleDrop);
        div.addEventListener('dragend', handleDragEnd);

        // Build parameter display
        const params = [];
        if (effect.duration && effect.duration > 0) {
            params.push(`Duration: ${effect.duration}s`);
        }
        if (effect.params) {
            if (effect.params.brightness !== undefined) params.push(`Brightness: ${effect.params.brightness}`);
            if (effect.params.frequency !== undefined) params.push(`Frequency: ${effect.params.frequency}`);
            if (effect.params.speed !== undefined) params.push(`Speed: ${effect.params.speed}`);
        }
        if (effect.options && Object.keys(effect.options).length > 0) {
            params.push(`Options: ${Object.keys(effect.options).length}`);
        }

        div.innerHTML = `
            <div style="flex: 1;">
                <div class="effect-item-header">
                    <span class="effect-name">${effect.key}</span>
                    <span class="drag-handle">⋮⋮</span>
                </div>
                <div class="effect-params">
                    ${params.map(p => `<span class="effect-param has-value">${p}</span>`).join('')}
                </div>
            </div>
            <div class="effect-item-controls">
                <button onclick="showEditEffectForm(${idx})">Edit</button>
                <button onclick="removeEffectFromPlaylist(${idx})">Remove</button>
            </div>
        `;
        container.appendChild(div);
    });
}

// Drag and drop functions
let draggedItem = null;

function handleDragStart(e) {
    draggedItem = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.getAttribute('data-index'));
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('drag-over');
}

function handleDragLeave(e) {
    this.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    this.classList.remove('drag-over');

    const fromIndex = parseInt(e.dataTransfer.getData('text/plain'));
    const toIndex = parseInt(this.getAttribute('data-index'));

    if (fromIndex === toIndex) return;

    // Reorder effects array
    const [movedEffect] = currentPlaylistData.effects.splice(fromIndex, 1);
    currentPlaylistData.effects.splice(toIndex, 0, movedEffect);

    // Re-render
    renderPlaylistEffects();
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    document.querySelectorAll('.effect-item').forEach(item => {
        item.classList.remove('drag-over');
    });
    draggedItem = null;
}

function removeEffectFromPlaylist(idx) {
    if (!confirm(`Remove ${currentPlaylistData.effects[idx].key} from playlist?`)) return;
    currentPlaylistData.effects.splice(idx, 1);
    renderPlaylistEffects();
}

function showAddEffectForm() {
    currentEffectIndex = null; // Adding new effect
    document.getElementById('effect-editor-title').textContent = 'Add Effect';

    // Reset form
    document.getElementById('effect-selector').value = '';
    document.getElementById('effect-duration').value = '8';
    document.getElementById('effect-brightness').value = '';
    document.getElementById('effect-brightness-value').textContent = '';
    document.getElementById('effect-frequency').value = '';
    document.getElementById('effect-frequency-value').textContent = '';
    document.getElementById('effect-speed').value = '';
    document.getElementById('effect-speed-value').textContent = '';
    document.getElementById('effect-options-container').innerHTML = '';

    // Populate effect selector
    const selector = document.getElementById('effect-selector');
    selector.innerHTML = '<option value="">Select an effect...</option>';
    effectList.forEach(effect => {
        const option = document.createElement('option');
        option.value = effect;
        option.textContent = effect;
        selector.appendChild(option);
    });

    // Add event listener for effect selection
    selector.onchange = function() {
        if (this.value) {
            loadEffectOptionsForEditor(this.value);
        } else {
            document.getElementById('effect-options-container').innerHTML = '';
        }
    };

    // Show modal
    document.getElementById('effect-editor-modal').style.display = 'flex';
}

function showEditEffectForm(idx) {
    currentEffectIndex = idx;
    const effect = currentPlaylistData.effects[idx];
    document.getElementById('effect-editor-title').textContent = `Edit ${effect.key}`;

    // Populate form
    document.getElementById('effect-selector').value = effect.key;
    document.getElementById('effect-duration').value = effect.duration || '8';

    // Set brightness slider if value exists
    if (effect.params && effect.params.brightness !== undefined) {
        document.getElementById('effect-brightness').value = effect.params.brightness;
        document.getElementById('effect-brightness-value').textContent = effect.params.brightness;
    } else {
        document.getElementById('effect-brightness').value = '';
        document.getElementById('effect-brightness-value').textContent = '';
    }

    // Set frequency slider if value exists
    if (effect.params && effect.params.frequency !== undefined) {
        document.getElementById('effect-frequency').value = effect.params.frequency;
        document.getElementById('effect-frequency-value').textContent = effect.params.frequency;
    } else {
        document.getElementById('effect-frequency').value = '';
        document.getElementById('effect-frequency-value').textContent = '';
    }

    // Set speed slider if value exists (convert to slider value: speed * 10)
    if (effect.params && effect.params.speed !== undefined) {
        const sliderValue = Math.round(effect.params.speed * 10);
        document.getElementById('effect-speed').value = sliderValue;
        document.getElementById('effect-speed-value').textContent = effect.params.speed.toFixed(1);
    } else {
        document.getElementById('effect-speed').value = '';
        document.getElementById('effect-speed-value').textContent = '';
    }

    // Load effect-specific options
    loadEffectOptionsForEditor(effect.key, effect.options || {});

    // Show modal
    document.getElementById('effect-editor-modal').style.display = 'flex';
}

async function loadEffectOptionsForEditor(effectKey, currentOptions = {}) {
    const container = document.getElementById('effect-options-container');
    container.innerHTML = '<p>Loading effect options...</p>';

    try {
        const response = await fetch('/api/effect/' + effectKey + '/options');
        const data = await response.json();

        if (!data.options || data.options.length === 0) {
            container.innerHTML = '<p>This effect has no additional options.</p>';
            return;
        }

        container.innerHTML = '<h4>Effect-Specific Options</h4>';

        data.options.forEach(option => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'option-group';

            const currentValue = currentOptions[option.key] !== undefined ? currentOptions[option.key] : option.default;

            if (option.type === 'boolean') {
                optionDiv.innerHTML = `
                    <label>${option.description}</label>
                    <select id="option-${option.key}" class="effect-selector">
                        <option value="true" ${currentValue === true ? 'selected' : ''}>On</option>
                        <option value="false" ${currentValue === false ? 'selected' : ''}>Off</option>
                    </select>
                    <small>Default: ${option.default ? 'On' : 'Off'}</small>
                `;
            } else if (option.type === 'number') {
                // Determine min/max/step based on option key
                let min = 0, max = 100, step = 1;
                if (option.key === 'speed') { min = 1; max = 50; step = 1; } // 0.1-5.0
                else if (option.key === 'intensity' || option.key === 'cooling') { min = 1; max = 10; }
                else if (option.key === 'color_hue') { min = 0; max = 360; }
                else if (option.key === 'scroll_speed') { min = 0; max = 200; step = 0.1; }
                else if (option.key === 'gravity') { min = 1; max = 50; step = 1; } // 0.01-0.5

                optionDiv.innerHTML = `
                    <label>${option.description}</label>
                    <input type="range" id="option-${option.key}"
                           min="${min}" max="${max}" step="${step}" value="${currentValue}"
                           oninput="document.getElementById('option-${option.key}-value').textContent = this.value">
                    <div class="slider-value">Value: <span id="option-${option.key}-value">${currentValue}</span></div>
                    <small>Default: ${option.default}</small>
                `;
            } else if (option.type === 'text') {
                optionDiv.innerHTML = `
                    <label>${option.description}</label>
                    <input type="text" id="option-${option.key}" value="${currentValue}" class="form-input">
                    <small>Default: ${option.default}</small>
                `;
            } else if (option.type === 'enum' && option.key === 'font_name') {
                // Special handling for font selection
                optionDiv.innerHTML = `
                    <label>${option.description}</label>
                    <select id="option-${option.key}" class="effect-selector">
                        <option value="">Loading fonts...</option>
                    </select>
                    <small>Default: ${option.default}</small>
                `;
                // Load fonts
                fetch('/api/fonts')
                    .then(response => response.json())
                    .then(fontData => {
                        const select = document.getElementById(`option-${option.key}`);
                        select.innerHTML = '';
                        fontData.fonts.forEach(font => {
                            const opt = document.createElement('option');
                            opt.value = font;
                            opt.textContent = font;
                            if (font === currentValue) opt.selected = true;
                            select.appendChild(opt);
                        });
                    });
            } else {
                // Generic dropdown for enum
                optionDiv.innerHTML = `
                    <label>${option.description}</label>
                    <input type="text" id="option-${option.key}" value="${currentValue}" class="form-input">
                    <small>Default: ${option.default}</small>
                `;
            }

            container.appendChild(optionDiv);
        });
    } catch (error) {
        container.innerHTML = '<p>Failed to load effect options.</p>';
        console.error('Error loading effect options:', error);
    }
}

function saveEffect() {
    // Get basic values
    const effectKey = document.getElementById('effect-selector').value;
    if (!effectKey) {
        showMessage('Please select an effect', 'error');
        return;
    }

    const duration = parseInt(document.getElementById('effect-duration').value) || 8;

    // Get global parameters (empty string means use default)
    const brightness = document.getElementById('effect-brightness').value;
    const frequency = document.getElementById('effect-frequency').value;
    const speedSlider = document.getElementById('effect-speed').value;
    const speed = speedSlider ? (parseInt(speedSlider) / 10).toFixed(1) : '';

    // Build effect object
    const effect = {
        key: effectKey,
        duration: duration,
        params: {},
        options: {}
    };

    // Add global parameters if specified
    if (brightness) effect.params.brightness = parseInt(brightness);
    if (frequency) effect.params.frequency = parseInt(frequency);
    if (speed) effect.params.speed = parseFloat(speed);

    // Collect effect-specific options
    const optionGroups = document.querySelectorAll('.option-group');
    optionGroups.forEach(group => {
        const input = group.querySelector('input, select');
        if (input) {
            const key = input.id.replace('option-', '');
            let value = input.value;

            // Convert string values to appropriate types
            if (input.type === 'range') {
                value = parseFloat(value);
            } else if (input.type === 'checkbox') {
                value = input.checked;
            } else if (input.tagName === 'SELECT') {
                if (value === 'true') value = true;
                else if (value === 'false') value = false;
                else value = isNaN(value) ? value : parseFloat(value);
            } else {
                // Try to parse as number if it looks like one
                if (!isNaN(value) && value.trim() !== '') {
                    value = parseFloat(value);
                }
            }

            effect.options[key] = value;
        }
    });

    // Add or update effect in playlist
    if (currentEffectIndex === null) {
        // Add new effect
        currentPlaylistData.effects.push(effect);
    } else {
        // Update existing effect
        currentPlaylistData.effects[currentEffectIndex] = effect;
    }

    // Update UI and close editor
    renderPlaylistEffects();
    closeEffectEditor();
    showMessage(`Effect ${effectKey} ${currentEffectIndex === null ? 'added' : 'updated'}`, 'success');
}

function closeEffectEditor() {
    document.getElementById('effect-editor-modal').style.display = 'none';
    currentEffectIndex = null;
}

async function savePlaylistChanges() {
    const name = document.getElementById('editor-playlist-name').textContent;
    const mood = document.getElementById('editor-mood').value || null;
    currentPlaylistData.mood = mood;
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
    currentPlaylistData = null;
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

// Initialize
function init() {
    updateStatus();
    loadEffects();
    loadPlaylists();
    setInterval(updateStatus, 2000);
}

// Start when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
