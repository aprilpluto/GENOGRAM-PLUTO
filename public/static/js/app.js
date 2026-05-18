/**
 * Pluto Genogram Pintar — Main Application Controller
 */
(() => {
  const STORAGE_KEY = 'pluto-genogram-projects';
  const MAX_HISTORY = 30;

  let history = [];
  let historyIndex = -1;
  let currentProject = null;

  const $ = (sel) => document.querySelector(sel);
  const familyInput = $('#family-input');
  const btnGenerate = $('#btn-generate');
  const validationPanel = $('#validation-panel');
  const validationList = $('#validation-list');
  const suggestionsPanel = $('#suggestions-panel');
  const suggestionsList = $('#suggestions-list');
  const statsBadge = $('#stats-badge');
  const templateSelect = $('#template-select');

  function init() {
    GenogramEngine.init('#genogram-svg');
    loadTemplates();
    bindEvents();
    loadLastProject();
    updateThemeIcon();
  }

  function bindEvents() {
    btnGenerate?.addEventListener('click', generateGenogram);
    $('#btn-undo')?.addEventListener('click', undo);
    $('#btn-redo')?.addEventListener('click', redo);
    $('#btn-zoom-in')?.addEventListener('click', () => GenogramEngine.zoomIn());
    $('#btn-zoom-out')?.addEventListener('click', () => GenogramEngine.zoomOut());
    $('#btn-zoom-fit')?.addEventListener('click', () => {
      const s = GenogramEngine.getState();
      if (s.layout?.bounds) GenogramEngine.fitView(s.layout.bounds);
    });
    $('#btn-autolayout')?.addEventListener('click', () => autoLayout());
    $('#theme-toggle')?.addEventListener('click', toggleTheme);
    templateSelect?.addEventListener('change', loadTemplate);
    $('#btn-import')?.addEventListener('click', () => $('#import-file')?.click());
    $('#import-file')?.addEventListener('change', importFile);

    document.querySelectorAll('[data-export]').forEach((btn) => {
      btn.addEventListener('click', () => handleExport(btn.dataset.export));
    });

    familyInput?.addEventListener('input', debounce(previewParse, 800));
    window.addEventListener('resize', debounce(() => {
      const s = GenogramEngine.getState();
      if (s.graph) GenogramEngine.render(s.graph, s.layout);
    }, 300));
  }

  async function generateGenogram() {
    const text = familyInput?.value?.trim();
    if (!text) {
      showToast('Masukkan data keluarga terlebih dahulu.');
      return;
    }

    const spinner = btnGenerate?.querySelector('.generate-spinner');
    spinner?.classList.remove('hidden');
    btnGenerate.disabled = true;
    document.getElementById('canvas-wrapper')?.classList.add('generating');

    try {
      const res = await fetch('/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Parse gagal');

      currentProject = {
        text,
        graph: data.graph,
        layout: data.layout,
        validation: data.validation,
        exportedAt: new Date().toISOString(),
      };

      GenogramEngine.render(data.graph, data.layout);
      showValidation(data);
      updateStats(data.stats);
      pushHistory(currentProject);
      saveProjectLocal(currentProject);
    } catch (err) {
      showToast(`Error: ${err.message}`);
    } finally {
      spinner?.classList.add('hidden');
      btnGenerate.disabled = false;
      document.getElementById('canvas-wrapper')?.classList.remove('generating');
    }
  }

  async function previewParse() {
    const text = familyInput?.value?.trim();
    if (!text || text.length < 20) return;
    try {
      const res = await fetch('/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (data.success && data.graph?.persons?.length) {
        GenogramEngine.render(data.graph, data.layout);
        document.getElementById('empty-state')?.classList.add('hidden');
        updateStats(data.stats);
      }
    } catch (_) { /* silent preview */ }
  }

  async function autoLayout() {
    if (!currentProject?.graph) return;
    const res = await fetch('/api/layout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph: currentProject.graph }),
    });
    const data = await res.json();
    if (data.layout) {
      currentProject.layout = data.layout;
      GenogramEngine.render(currentProject.graph, data.layout);
      pushHistory(currentProject);
    }
  }

  function showValidation(data) {
    const v = data.validation || {};
    const all = [...(v.errors || []), ...(v.warnings || []), ...(data.parse_warnings || [])];
    validationPanel?.classList.toggle('hidden', all.length === 0);
    validationList.innerHTML = all.map((m) =>
      `<li class="${(v.errors || []).includes(m) ? 'text-red-500' : 'text-amber-500'}">• ${m}</li>`
    ).join('');

    const suggestions = [...(data.suggestions || []), ...(v.fixes || [])];
    suggestionsPanel?.classList.toggle('hidden', suggestions.length === 0);
    suggestionsList.innerHTML = suggestions.map((s) =>
      `<li class="p-2 rounded-lg bg-pluto-50 dark:bg-pluto-900/50">${s.message || s.suggestion || JSON.stringify(s)}</li>`
    ).join('');
  }

  function updateStats(stats) {
    if (!stats) return;
    statsBadge.textContent = `${stats.persons} orang · ${stats.marriages} pernikahan`;
  }

  function pushHistory(project) {
    history = history.slice(0, historyIndex + 1);
    history.push(JSON.parse(JSON.stringify(project)));
    if (history.length > MAX_HISTORY) history.shift();
    historyIndex = history.length - 1;
    updateHistoryButtons();
  }

  function undo() {
    if (historyIndex <= 0) return;
    historyIndex--;
    restoreFromHistory();
  }

  function redo() {
    if (historyIndex >= history.length - 1) return;
    historyIndex++;
    restoreFromHistory();
  }

  function restoreFromHistory() {
    const project = history[historyIndex];
    if (!project) return;
    currentProject = project;
    familyInput.value = project.text || '';
    if (project.graph && project.layout) {
      GenogramEngine.render(project.graph, project.layout);
    }
    updateHistoryButtons();
  }

  function updateHistoryButtons() {
    $('#btn-undo').disabled = historyIndex <= 0;
    $('#btn-redo').disabled = historyIndex >= history.length - 1;
  }

  function saveProjectLocal(project) {
    try {
      const projects = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      const idx = projects.findIndex((p) => p.text === project.text);
      if (idx >= 0) projects[idx] = project;
      else projects.unshift(project);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(projects.slice(0, 10)));
      localStorage.setItem('pluto-last-project', JSON.stringify(project));
    } catch (_) { /* quota */ }
  }

  function loadLastProject() {
    try {
      const saved = localStorage.getItem('pluto-last-project');
      if (saved) {
        const project = JSON.parse(saved);
        if (project.text) familyInput.value = project.text;
      }
    } catch (_) { /* ignore */ }
  }

  async function loadTemplates() {
    try {
      const res = await fetch('/api/templates');
      const data = await res.json();
      data.templates?.forEach((t) => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.name;
        templateSelect?.appendChild(opt);
      });
    } catch (_) { /* offline */ }
  }

  async function loadTemplate() {
    const id = templateSelect?.value;
    if (!id) return;
    const res = await fetch(`/api/templates/${id}`);
    const data = await res.json();
    if (data.text) familyInput.value = data.text;
  }

  function handleExport(format) {
    const svgEl = GenogramEngine.getSvgElement();
    if (!svgEl || !currentProject) {
      showToast('Generate genogram terlebih dahulu.');
      return;
    }
    const name = `pluto-genogram-${Date.now()}`;
    switch (format) {
      case 'png': GenogramExport.exportPNG(svgEl, `${name}.png`); break;
      case 'jpg': GenogramExport.exportJPG(svgEl, `${name}.jpg`); break;
      case 'svg': GenogramExport.exportSVG(svgEl, `${name}.svg`); break;
      case 'pdf': GenogramExport.exportPDF(svgEl, `${name}.pdf`); break;
      case 'json':
        GenogramExport.exportJSON({
          text: familyInput?.value,
          graph: currentProject.graph,
          layout: currentProject.layout,
        }, `${name}.json`);
        break;
    }
    showToast(`Export ${format.toUpperCase()} dimulai...`);
  }

  function importFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target.result);
        if (data.text) familyInput.value = data.text;
        if (data.graph && data.layout) {
          currentProject = data;
          GenogramEngine.render(data.graph, data.layout);
          pushHistory(currentProject);
        } else if (data.text) {
          generateGenogram();
        }
        showToast('Project berhasil diimport.');
      } catch {
        familyInput.value = ev.target.result;
        showToast('File teks dimuat. Klik Generate.');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  }

  function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('pluto-theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    updateThemeIcon();
  }

  function updateThemeIcon() {
    const btn = $('#theme-toggle');
    if (btn) btn.textContent = document.documentElement.classList.contains('dark') ? '☀️' : '🌙';
  }

  function showToast(msg) {
    let toast = document.getElementById('pluto-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'pluto-toast';
      toast.className = 'fixed bottom-6 left-1/2 -translate-x-1/2 px-6 py-3 rounded-xl glass shadow-xl text-sm z-[200] animate-slide-up';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
  }

  function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }

  document.addEventListener('DOMContentLoaded', init);
})();
