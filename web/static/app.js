/**
 * AIRefiner — Frontend JavaScript
 * Handles API calls, UI state, and interactivity.
 * No external dependencies — vanilla JS only.
 */

'use strict';

/* ================================================================
   Constants
   ================================================================ */
const TASK_META = {
  '1': { icon: '✍️', desc: 'Polish emails, articles, and business docs' },
  '2': { icon: '📊', desc: 'Convert content into presentation bullet points' },
  '3': { icon: '🌐', desc: 'Auto-detect language and translate EN ↔ ZH' },
};

/* ================================================================
   State
   ================================================================ */
const state = {
  models: [],
  tasks: [],
  selectedModel: '',
  selectedTaskKey: '1',
  processing: false,
};

/* ================================================================
   DOM refs
   ================================================================ */
const $ = (id) => document.getElementById(id);
const modelSelect   = $('modelSelect');
const taskCards     = $('taskCards');
const inputText     = $('inputText');
const charCount     = $('charCount');
const processBtn    = $('processBtn');
const btnContent    = $('btnContent');
const btnSpinner    = $('btnSpinner');
const processMeta   = $('processMeta');
const outputSection = $('outputSection');
const outputText    = $('outputText');
const errorBanner   = $('errorBanner');
const errorMessage  = $('errorMessage');
const copyBtn       = $('copyBtn');
const clearInputBtn = $('clearInputBtn');
const statusBadge   = $('statusBadge');
const statusText    = $('statusText');
const providerBadges   = $('providerBadges');
const refreshModelsBtn = $('refreshModelsBtn');
const refreshIcon      = $('refreshIcon');
const refreshLabel     = $('refreshLabel');
const errorDismissBtn  = $('errorDismissBtn');

/* ================================================================
   Utility helpers
   ================================================================ */

function setStatus(text, state) {
  statusText.textContent = text;
  statusBadge.className = 'status-badge ' + (state || '');
}

function showError(msg) {
  errorMessage.textContent = msg;
  errorBanner.style.display = 'flex';
  outputSection.style.display = 'none';
}

function hideError() {
  errorBanner.style.display = 'none';
  errorMessage.textContent = '';
}

function setProcessing(isProcessing) {
  state.processing = isProcessing;
  processBtn.disabled = isProcessing;
  btnContent.hidden = isProcessing;
  btnSpinner.hidden = !isProcessing;
  inputText.disabled = isProcessing;
  modelSelect.disabled = isProcessing;
}

function extractProviders(models) {
  const providers = new Set();
  models.forEach((m) => {
    const slash = m.indexOf('/');
    if (slash !== -1) providers.add(m.slice(0, slash).toLowerCase());
  });
  return [...providers];
}

function renderProviderBadges(providers) {
  providerBadges.innerHTML = '';
  if (providers.length === 0) {
    providerBadges.innerHTML = '<span style="font-size:0.8rem;color:var(--text-muted)">No providers available</span>';
    return;
  }
  providers.forEach((p) => {
    const badge = document.createElement('button');
    badge.type = 'button';
    badge.className = `provider-badge ${p}`;
    badge.textContent = p;
    badge.dataset.provider = p;
    badge.setAttribute('aria-label', `Filter to ${p} models`);
    badge.addEventListener('click', () => selectProvider(p));
    providerBadges.appendChild(badge);
  });
}

/** Jump the dropdown to the first model belonging to `provider` and highlight the badge. */
function selectProvider(provider) {
  const firstModel = state.models.find((m) => m.toLowerCase().startsWith(provider.toLowerCase() + '/'));
  if (!firstModel) return;
  modelSelect.value = firstModel;
  state.selectedModel = firstModel;
  syncBadgeToModel(firstModel);
}

/** Highlight the provider badge that matches the currently selected model. */
function syncBadgeToModel(modelKey) {
  const slash = modelKey.indexOf('/');
  const currentProvider = slash !== -1 ? modelKey.slice(0, slash).toLowerCase() : '';
  document.querySelectorAll('.provider-badge').forEach((badge) => {
    const isMatch = badge.dataset.provider.toLowerCase() === currentProvider;
    badge.classList.toggle('selected', isMatch);
  });
}

function renderModelSelect(models) {
  modelSelect.innerHTML = '';
  if (models.length === 0) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = 'No models available';
    modelSelect.appendChild(opt);
    return;
  }

  // Group by provider
  const grouped = {};
  models.forEach((m) => {
    const slash = m.indexOf('/');
    const provider = slash !== -1 ? m.slice(0, slash) : 'Other';
    if (!grouped[provider]) grouped[provider] = [];
    grouped[provider].push(m);
  });

  Object.entries(grouped).forEach(([provider, providerModels]) => {
    const group = document.createElement('optgroup');
    group.label = provider.charAt(0).toUpperCase() + provider.slice(1);
    providerModels.forEach((m) => {
      const opt = document.createElement('option');
      opt.value = m;
      // Pretty display: strip "provider/" prefix
      const slash = m.indexOf('/');
      opt.textContent = slash !== -1 ? m.slice(slash + 1) : m;
      group.appendChild(opt);
    });
    modelSelect.appendChild(group);
  });

  // Default selection
  state.selectedModel = models[0];
  modelSelect.value = models[0];
  syncBadgeToModel(models[0]);
}

function renderTaskCards(tasks) {
  taskCards.innerHTML = '';
  tasks.forEach((task) => {
    const meta = TASK_META[task.key] || { icon: '⚙️', desc: '' };
    const card = document.createElement('div');
    card.className = 'task-card' + (task.key === state.selectedTaskKey ? ' active' : '');
    card.setAttribute('role', 'button');
    card.setAttribute('aria-pressed', task.key === state.selectedTaskKey ? 'true' : 'false');
    card.setAttribute('tabindex', '0');
    card.dataset.key = task.key;
    card.innerHTML = `
      <span class="task-icon" aria-hidden="true">${meta.icon}</span>
      <span class="task-info">
        <span class="task-name">${task.name}</span>
        <span class="task-desc">${meta.desc}</span>
      </span>`;

    card.addEventListener('click', () => selectTask(task.key));
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectTask(task.key); }
    });

    taskCards.appendChild(card);
  });
}

function selectTask(key) {
  state.selectedTaskKey = key;
  document.querySelectorAll('.task-card').forEach((card) => {
    const isActive = card.dataset.key === key;
    card.classList.toggle('active', isActive);
    card.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });
  // Update process button label
  const task = state.tasks.find((t) => t.key === key);
  if (task) {
    const meta = TASK_META[key] || {};
    btnContent.innerHTML = `<span class="btn-icon" aria-hidden="true">${meta.icon || '✨'}</span><span>${task.name.split('(')[0].trim()}</span>`;
  }
}

/* ================================================================
   API calls
   ================================================================ */

async function loadStatus() {
  setStatus('Connecting…', '');
  try {
    const res = await fetch('/api/status');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data.ok) {
      setStatus('Error — check .env', 'error');
      showError(data.error || 'Server initialization failed. Check that your API keys are set in .env');
      return;
    }

    state.models = data.models;
    state.tasks  = data.tasks;

    renderModelSelect(data.models);
    renderTaskCards(data.tasks);
    renderProviderBadges(extractProviders(data.models));
    selectTask(state.selectedTaskKey);

    setStatus(`${data.models.length} models ready`, 'online');
    hideError();
  } catch (err) {
    setStatus('Offline', 'error');
    showError('Could not reach the server. Make sure web_main.py is running.');
  }
}

async function processText() {
  if (state.processing) return;
  hideError();

  const text = inputText.value.trim();
  if (!text) {
    showError('Please enter some text before refining.');
    inputText.focus();
    return;
  }
  if (!state.selectedModel) {
    showError('Please select a model.');
    return;
  }

  setProcessing(true);
  outputSection.hidden = true;
  processMeta.textContent = '';

  const t0 = Date.now();

  try {
    const res = await fetch('/api/refine', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: state.selectedModel,
        task_key: state.selectedTaskKey,
        text: text,
      }),
    });

    const data = await res.json();
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

    if (!data.ok) {
      showError(data.error || 'An error occurred.');
      return;
    }

    outputText.textContent = data.result;
    outputSection.hidden = false;
    processMeta.textContent = `Completed in ${elapsed}s · ${data.model}`;

    // Smooth scroll to output
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (err) {
    showError('Network error: ' + err.message);
  } finally {
    setProcessing(false);
  }
}

/* ================================================================
   Refresh Models
   ================================================================ */
async function refreshModels() {
  if (refreshModelsBtn.disabled) return;
  refreshModelsBtn.disabled = true;
  refreshIcon.classList.add('spinning');
  refreshLabel.textContent = 'Refreshing…';
  hideError();

  try {
    // Ask the server to clear its cache and re-fetch
    const res = await fetch('/api/refresh', { method: 'POST' });
    const data = await res.json();

    if (!data.ok) {
      showError(data.error || 'Refresh failed.');
      return;
    }

    // Re-render model list and provider badges with fresh data
    state.models = data.models;
    renderModelSelect(data.models);
    renderProviderBadges(extractProviders(data.models));
    syncBadgeToModel(state.selectedModel || data.models[0]);
    setStatus(`${data.models.length} models ready`, 'online');
    refreshLabel.textContent = '✓ Done';
    setTimeout(() => { refreshLabel.textContent = 'Refresh'; }, 2000);
  } catch (err) {
    showError('Refresh failed: ' + err.message);
    refreshLabel.textContent = 'Refresh';
  } finally {
    refreshIcon.classList.remove('spinning');
    refreshModelsBtn.disabled = false;
  }
}


async function copyResult() {
  const text = outputText.textContent;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    copyBtn.textContent = '✅ Copied!';
    setTimeout(() => { copyBtn.textContent = '⎘ Copy'; }, 2000);
  } catch {
    // Fallback for older browsers
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    copyBtn.textContent = '✅ Copied!';
    setTimeout(() => { copyBtn.textContent = '⎘ Copy'; }, 2000);
  }
}

/* ================================================================
   Global helpers
   ================================================================ */

function scrollToApp() {
  $('appSection').scrollIntoView({ behavior: 'smooth' });
  setTimeout(() => inputText.focus(), 600);
}

/* ================================================================
   Event Listeners
   ================================================================ */

refreshModelsBtn.addEventListener('click', refreshModels);

errorDismissBtn.addEventListener('click', hideError);

modelSelect.addEventListener('change', () => {
  state.selectedModel = modelSelect.value;
  syncBadgeToModel(modelSelect.value);
});

inputText.addEventListener('input', () => {
  const len = inputText.value.length;
  charCount.textContent = `${len.toLocaleString()} char${len !== 1 ? 's' : ''}`;
});

processBtn.addEventListener('click', processText);

copyBtn.addEventListener('click', copyResult);

clearInputBtn.addEventListener('click', () => {
  inputText.value = '';
  charCount.textContent = '0 chars';
  outputSection.hidden = true;
  hideError();
  processMeta.textContent = '';
  inputText.focus();
});

// Ctrl/Cmd+Enter to process
inputText.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    processText();
  }
});

/* ================================================================
   Init
   ================================================================ */
document.addEventListener('DOMContentLoaded', () => {
  // Ensure banner is hidden on load (CSS display:flex overrides [hidden])
  hideError();
  loadStatus();
});

// Expose scrollToApp globally (called from HTML)
window.scrollToApp = scrollToApp;
