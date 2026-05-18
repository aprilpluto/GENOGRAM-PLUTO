/**
 * Pluto Genogram Pintar — Export utilities
 */
const GenogramExport = (() => {
  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function exportPNG(svgEl, filename = 'genogram.png') {
    const canvas = await svgToCanvas(svgEl);
    canvas.toBlob((blob) => downloadBlob(blob, filename), 'image/png');
  }

  async function exportJPG(svgEl, filename = 'genogram.jpg') {
    const canvas = await svgToCanvas(svgEl);
    canvas.toBlob((blob) => downloadBlob(blob, filename), 'image/jpeg', 0.92);
  }

  function exportSVG(svgEl, filename = 'genogram.svg') {
    const clone = svgEl.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('width', '100%');
    bg.setAttribute('height', '100%');
    bg.setAttribute('fill', document.documentElement.classList.contains('dark') ? '#1e1b4b' : '#f8fafc');
    clone.insertBefore(bg, clone.firstChild);
    const svgData = new XMLSerializer().serializeToString(clone);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    downloadBlob(blob, filename);
  }

  async function exportPDF(svgEl, filename = 'genogram.pdf') {
    const canvas = await svgToCanvas(svgEl);
    const imgData = canvas.toDataURL('image/png');
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({
      orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
      unit: 'px',
      format: [canvas.width, canvas.height],
    });
    pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
    pdf.save(filename);
  }

  function exportJSON(project, filename = 'pluto-genogram-project.json') {
    const data = {
      app: 'Pluto Genogram Pintar',
      version: '1.0',
      branding: 'by Pluto for April',
      exportedAt: new Date().toISOString(),
      ...project,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadBlob(blob, filename);
  }

  async function svgToCanvas(svgEl) {
    const wrapper = document.getElementById('canvas-wrapper');
    const rect = wrapper?.getBoundingClientRect() || { width: 800, height: 600 };

    const clone = svgEl.cloneNode(true);
    clone.setAttribute('width', rect.width);
    clone.setAttribute('height', rect.height);

    const svgData = new XMLSerializer().serializeToString(clone);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    const img = new Image();
    const isDark = document.documentElement.classList.contains('dark');
    const bgColor = isDark ? '#1e1b4b' : '#f8fafc';

    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
      img.src = url;
    });

    const canvas = document.createElement('canvas');
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    const ctx = canvas.getContext('2d');
    ctx.scale(2, 2);
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, rect.width, rect.height);
    ctx.drawImage(img, 0, 0, rect.width, rect.height);
    URL.revokeObjectURL(url);
    return canvas;
  }

  return { exportPNG, exportJPG, exportSVG, exportPDF, exportJSON };
})();
