/**
 * Pluto Genogram Pintar — D3.js Genogram Renderer
 * Professional genogram symbols per international standards
 */
const GenogramEngine = (() => {
  const SYMBOLS = {
    male: { shape: 'rect', tooltip: 'Laki-laki — persegi' },
    female: { shape: 'circle', tooltip: 'Perempuan — lingkaran' },
    unknown: { shape: 'rect', tooltip: 'Jenis kelamin tidak diketahui' },
  };

  const LEGEND = [
    { id: 'male', label: 'Laki-laki', draw: (g) => g.append('rect').attr('width', 14).attr('height', 14).attr('x', 3).attr('y', 1) },
    { id: 'female', label: 'Perempuan', draw: (g) => g.append('circle').attr('r', 7).attr('cx', 10).attr('cy', 8) },
    { id: 'deceased', label: 'Meninggal', draw: (g) => { g.append('rect').attr('width', 14).attr('height', 14).attr('x', 3).attr('y', 1); g.append('line').attr('x1', 3).attr('y1', 15).attr('x2', 17).attr('y2', 1).attr('stroke', 'currentColor').attr('stroke-width', 2); } },
    { id: 'marriage', label: 'Pernikahan', draw: (g) => g.append('line').attr('x1', 0).attr('y1', 8).attr('x2', 20).attr('y2', 8).attr('stroke', 'currentColor').attr('stroke-width', 2) },
    { id: 'divorced', label: 'Perceraian', draw: (g) => { g.append('line').attr('x1', 0).attr('y1', 8).attr('x2', 20).attr('y2', 8).attr('stroke', 'currentColor').attr('stroke-width', 2); g.append('line').attr('x1', 8).attr('y1', 2).attr('x2', 12).attr('y2', 14).attr('stroke', 'currentColor').attr('stroke-width', 2); g.append('line').attr('x1', 12).attr('y1', 2).attr('x2', 8).attr('y2', 14).attr('stroke', 'currentColor').attr('stroke-width', 2); } },
    { id: 'adopted', label: 'Adopsi', draw: (g) => g.append('line').attr('x1', 10).attr('y1', 0).attr('x2', 10).attr('y2', 16).attr('stroke', 'currentColor').attr('stroke-width', 2).attr('stroke-dasharray', '3,2') },
    { id: 'twin', label: 'Kembar', draw: (g) => { g.append('line').attr('x1', 4).attr('y1', 4).attr('x2', 16).attr('y2', 4).attr('stroke', 'currentColor'); g.append('line').attr('x1', 6).attr('y1', 4).attr('x2', 6).attr('y2', 14).attr('stroke', 'currentColor'); g.append('line').attr('x1', 14).attr('y1', 4).attr('x2', 14).attr('y2', 14).attr('stroke', 'currentColor'); } },
    { id: 'conflict', label: 'Konflik', draw: (g) => { const p = 'M0,8 L5,4 L10,12 L15,4 L20,8'; g.append('path').attr('d', p).attr('fill', 'none').attr('stroke', '#ef4444').attr('stroke-width', 2); } },
  ];

  let svg, gRoot, gLinks, gNodes, zoomBehavior;
  let state = { graph: null, layout: null, positions: {}, zoom: 1, transform: { x: 0, y: 0 } };
  let nodeSize = { w: 56, h: 56 };
  let onNodeDrag = null;

  function init(svgSelector) {
    const el = d3.select(svgSelector);
    el.selectAll('*').remove();
    svg = el;
    const wrapper = document.getElementById('canvas-wrapper');
    const w = wrapper?.clientWidth || 800;
    const h = wrapper?.clientHeight || 500;
    svg.attr('viewBox', `0 0 ${w} ${h}`).attr('width', '100%').attr('height', '100%');

    gRoot = svg.append('g').attr('class', 'genogram-root');
    gLinks = gRoot.append('g').attr('class', 'genogram-links');
    gNodes = gRoot.append('g').attr('class', 'genogram-nodes');

    zoomBehavior = d3.zoom()
      .scaleExtent([0.2, 3])
      .on('zoom', (event) => {
        gRoot.attr('transform', event.transform);
        state.transform = { x: event.transform.x, y: event.transform.y };
        state.zoom = event.transform.k;
      });
    svg.call(zoomBehavior);
    renderLegend();
    return { svg, gRoot };
  }

  function render(graph, layout) {
    if (!svg) init('#genogram-svg');
    state.graph = graph;
    state.layout = layout;
    state.positions = { ...layout.positions };

    document.getElementById('empty-state')?.classList.add('hidden');

    drawLinks(layout.links || []);
    drawNodes(graph, layout);
    fitView(layout.bounds);
  }

  function drawLinks(links) {
    gLinks.selectAll('*').remove();
    links.forEach((link) => {
      const g = gLinks.append('g');
      const cls = ['genogram-link', link.type, link.status].filter(Boolean).join(' ');
      if (link.type === 'marriage') {
        const line = g.append('line').attr('class', cls)
          .attr('x1', link.x1).attr('y1', link.y1)
          .attr('x2', link.x2).attr('y2', link.y2);
        if (link.status === 'divorced') {
          const mx = (link.x1 + link.x2) / 2;
          g.append('line').attr('x1', mx - 6).attr('y1', link.y1 - 8)
            .attr('x2', mx + 6).attr('y2', link.y1 + 8)
            .attr('stroke', '#ef4444').attr('stroke-width', 2);
          g.append('line').attr('x1', mx + 6).attr('y1', link.y1 - 8)
            .attr('x2', mx - 6).attr('y2', link.y1 + 8)
            .attr('stroke', '#ef4444').attr('stroke-width', 2);
        }
        if (link.year) {
          g.append('text').attr('x', (link.x1 + link.x2) / 2).attr('y', link.y1 - 12)
            .attr('text-anchor', 'middle').attr('class', 'person-age').text(link.year);
        }
      } else if (link.type === 'conflict') {
        const midX = (link.x1 + link.x2) / 2;
        const path = d3.line()([
          [link.x1, link.y1], [midX - 8, link.y1 - 6], [midX, link.y1 + 6],
          [midX + 8, link.y1 - 6], [link.x2, link.y2],
        ]);
        g.append('path').attr('d', path).attr('class', 'genogram-link conflict').attr('fill', 'none');
      } else {
        g.append('line').attr('class', cls)
          .attr('x1', link.x1).attr('y1', link.y1)
          .attr('x2', link.x2).attr('y2', link.y2);
      }
    });
  }

  function drawNodes(graph, layout) {
    gNodes.selectAll('*').remove();
    const persons = graph.persons || [];
    const personMap = {};
    persons.forEach((p) => { personMap[p.id] = p; });

    Object.entries(state.positions).forEach(([id, pos]) => {
      const person = personMap[id];
      if (!person) return;

      const ng = gNodes.append('g')
        .attr('class', 'genogram-node')
        .attr('data-id', id)
        .attr('transform', `translate(${pos.x},${pos.y})`);

      const gender = person.gender || 'unknown';
      const sym = SYMBOLS[gender] || SYMBOLS.unknown;
      const hw = nodeSize.w / 2;
      const hh = nodeSize.h / 2;

      if (sym.shape === 'circle') {
        ng.append('circle')
          .attr('cx', hw).attr('cy', hh).attr('r', hw - 2)
          .attr('fill', 'white').attr('stroke', '#4f46e5').attr('stroke-width', 2.5);
      } else {
        ng.append('rect')
          .attr('width', nodeSize.w - 4).attr('height', nodeSize.h - 4)
          .attr('x', 2).attr('y', 2)
          .attr('fill', 'white').attr('stroke', '#4f46e5').attr('stroke-width', 2.5)
          .attr('rx', 2);
      }

      if (person.life_status === 'deceased') {
        ng.append('line').attr('class', 'deceased-mark')
          .attr('x1', 2).attr('y1', nodeSize.h - 2)
          .attr('x2', nodeSize.w - 2).attr('y2', 2);
        ng.append('line').attr('class', 'deceased-mark')
          .attr('x1', 2).attr('y1', 2)
          .attr('x2', nodeSize.w - 2).attr('y2', nodeSize.h - 2);
      }

      person.conditions?.forEach((cond) => {
        if (cond === 'adopted') {
          ng.append('rect').attr('width', nodeSize.w).attr('height', nodeSize.h)
            .attr('fill', 'none').attr('stroke', '#06b6d4').attr('stroke-width', 1.5)
            .attr('stroke-dasharray', '4,2');
        }
      });

      ng.append('text').attr('class', 'person-label')
        .attr('x', hw).attr('y', nodeSize.h + 14)
        .text(person.name?.split(' ')[0] || '?');

      const ageText = person.age ? `${person.age}` : (person.birth_year ? `'${String(person.birth_year).slice(-2)}` : '');
      if (ageText) {
        ng.append('text').attr('class', 'person-age')
          .attr('x', hw).attr('y', hh + 4)
          .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
          .text(ageText);
      }

      ng.on('mouseenter', (e) => showTooltip(e, person, sym))
        .on('mouseleave', hideTooltip);

      const drag = d3.drag()
        .on('start', function () { d3.select(this).classed('dragging', true); })
        .on('drag', function (event) {
          const newX = pos.x + event.dx;
          const newY = pos.y + event.dy;
          pos.x = newX;
          pos.y = newY;
          state.positions[id] = pos;
          d3.select(this).attr('transform', `translate(${newX},${newY})`);
          if (onNodeDrag) onNodeDrag(id, newX, newY);
        })
        .on('end', function () {
          d3.select(this).classed('dragging', false);
          redrawLinks();
        });
      ng.call(drag);
    });
  }

  function redrawLinks() {
    if (!state.layout || !state.graph) return;
    const layout = { ...state.layout, positions: state.positions };
    fetch('/api/layout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph: state.graph }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.layout) {
          Object.assign(state.positions, data.layout.positions);
          drawLinks(data.layout.links);
        }
      })
      .catch(() => {
        drawLinks(state.layout.links || []);
      });
  }

  function showTooltip(event, person, sym) {
    const tip = document.getElementById('symbol-tooltip');
    if (!tip) return;
    const genderLabel = person.gender === 'female' ? 'Perempuan' : person.gender === 'male' ? 'Laki-laki' : 'Tidak diketahui';
    tip.innerHTML = `<strong>${person.name}</strong><br>${genderLabel}${person.age ? ` · ${person.age} tahun` : ''}${person.life_status === 'deceased' ? '<br>† Meninggal' : ''}<br><em>${sym.tooltip}</em>`;
    tip.classList.remove('hidden');
    tip.style.left = `${event.pageX + 12}px`;
    tip.style.top = `${event.pageY + 12}px`;
  }

  function hideTooltip() {
    document.getElementById('symbol-tooltip')?.classList.add('hidden');
  }

  function renderLegend() {
    const el = document.getElementById('legend');
    if (!el) return;
    el.innerHTML = '';
    LEGEND.forEach((item) => {
      const div = document.createElement('div');
      div.className = 'legend-item';
      div.title = item.label;
      const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svgEl.setAttribute('class', 'legend-symbol');
      svgEl.setAttribute('viewBox', '0 0 20 16');
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      item.draw(d3.select(g));
      svgEl.appendChild(g);
      div.appendChild(svgEl);
      const span = document.createElement('span');
      span.textContent = item.label;
      div.appendChild(span);
      div.addEventListener('mouseenter', (e) => {
        const tip = document.getElementById('symbol-tooltip');
        if (tip) {
          tip.innerHTML = item.label;
          tip.classList.remove('hidden');
          tip.style.left = `${e.pageX + 12}px`;
          tip.style.top = `${e.pageY + 12}px`;
        }
      });
      div.addEventListener('mouseleave', hideTooltip);
      el.appendChild(div);
    });
  }

  function fitView(bounds) {
    if (!bounds || !svg) return;
    const wrapper = document.getElementById('canvas-wrapper');
    const w = wrapper?.clientWidth || 800;
    const h = wrapper?.clientHeight || 500;
    const scale = Math.min(w / bounds.width, h / bounds.height, 1.2) * 0.85;
    const tx = (w - bounds.width * scale) / 2 - bounds.minX * scale;
    const ty = (h - bounds.height * scale) / 2 - bounds.minY * scale;
    svg.transition().duration(500).call(
      zoomBehavior.transform,
      d3.zoomIdentity.translate(tx, ty).scale(scale)
    );
  }

  function zoomIn() {
    svg?.transition().duration(300).call(zoomBehavior.scaleBy, 1.3);
  }

  function zoomOut() {
    svg?.transition().duration(300).call(zoomBehavior.scaleBy, 0.7);
  }

  function autoLayout() {
    if (state.graph && state.layout) render(state.graph, state.layout);
  }

  function getSvgElement() {
    return document.getElementById('genogram-svg');
  }

  function setNodeDragCallback(cb) {
    onNodeDrag = cb;
  }

  function updatePositions(positions) {
    state.positions = { ...positions };
    gNodes.selectAll('.genogram-node').each(function () {
      const id = d3.select(this).attr('data-id');
      const pos = state.positions[id];
      if (pos) d3.select(this).attr('transform', `translate(${pos.x},${pos.y})`);
    });
  }

  return {
    init,
    render,
    fitView,
    zoomIn,
    zoomOut,
    autoLayout,
    getSvgElement,
    setNodeDragCallback,
    updatePositions,
    getState: () => ({ ...state }),
  };
})();
