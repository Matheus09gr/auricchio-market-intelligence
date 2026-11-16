fetch('./metals.json')
  .then(r => r.json())
  .then(data => {
    const grid = document.querySelector('#metals-grid');
    if (!grid) return;
    grid.innerHTML = data.metals.map(m => {
      const available = m.status === 'available';
      const biasClass = m.bias === 'Bearish' ? 'bias-bear' : m.bias === 'Bullish' ? 'bias-bull' : 'bias-neutral';
      return `
      <article class="card">
        <div class="symbol">${m.symbol}</div>
        <h3>${m.name}</h3>
        <div class="en">${m.english}</div>
        <div class="meta">
          <div class="row"><span>Último relatório</span><b>${m.last_report || '—'}</b></div>
          <div class="row"><span>Viés curto prazo</span><b class="${biasClass}">${m.bias || '—'}</b></div>
          <div class="row"><span>Status</span><b>${available ? 'Disponível' : 'Em preparação'}</b></div>
        </div>
        ${available ? `<a class="action" href="${m.path}">Abrir observatório</a>` : `<div class="action disabled">Em preparação</div>`}
      </article>`;
    }).join('');

    const rows = data.metals.map(m => `
      <tr>
        <td><b>${m.name}</b></td>
        <td>${m.last_report || '—'}</td>
        <td>${m.bias || '—'}</td>
        <td>${m.physical || '—'}</td>
        <td>${m.note || '—'}</td>
      </tr>`).join('');
    const tbody = document.querySelector('#compare-body');
    if (tbody) tbody.innerHTML = rows;
  })
  .catch(() => {
    const grid = document.querySelector('#metals-grid');
    if (grid) grid.innerHTML = '<p>Não foi possível carregar o catálogo de metais.</p>';
  });
