/* ══════════════════════════════════════════════════════════
   AgriData CM — Application JavaScript
   Navigation, GPS, Formulaires, API, Analyses, Charts
══════════════════════════════════════════════════════════ */

const API = '';  // même origine

// ── i18n ─────────────────────────────────────────────────────────────────────
const LANG = {
  fr: {
    s_collect:'COLLECTE', s_analyse:'ANALYSE',
    nav_dashboard:'Tableau de bord', nav_producteur:'Producteur',
    nav_parcelle:'Parcelle & GPS', nav_phyto:'Phytosanitaire',
    nav_marche:'Prix Marché', nav_climat:'Climatologie',
    nav_analyse:'Analyses Stat.', nav_donnees:'Données', nav_export:'Exporter',
    t_dashboard:'Tableau de bord', sub_dashboard:'Vue d\'ensemble — Région Centre, Cameroun',
    t_producteur:'Fiche Producteur', sub_producteur:'Recensement des producteurs agricoles',
    sync_ok:'Tout synchronisé ✓', sync_pending:'enreg. en attente',
  },
  en: {
    s_collect:'DATA COLLECTION', s_analyse:'ANALYSIS',
    nav_dashboard:'Dashboard', nav_producteur:'Farmer',
    nav_parcelle:'Plot & GPS', nav_phyto:'Phytosanitary',
    nav_marche:'Market Price', nav_climat:'Climatology',
    nav_analyse:'Stat. Analysis', nav_donnees:'Data', nav_export:'Export',
    t_dashboard:'Dashboard', sub_dashboard:'Overview — Centre Region, Cameroon',
    t_producteur:'Farmer Profile', sub_producteur:'Agricultural producer census',
    sync_ok:'All synced ✓', sync_pending:'records pending',
  }
};
let currentLang = 'fr';

function setLang(l) {
  currentLang = l;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.lang-btn').forEach(b => { if(b.textContent===l.toUpperCase()) b.classList.add('active'); });
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const k = el.getAttribute('data-i18n');
    if (LANG[l][k]) el.textContent = LANG[l][k];
  });
}

// ── Theme ─────────────────────────────────────────────────────────────────────
let isDark = true;
function toggleTheme() {
  isDark = !isDark;
  document.body.className = isDark ? 'dark' : 'light';
  document.querySelector('.theme-btn').textContent = isDark ? '☀️' : '🌙';
}

// ── Toast ─────────────────────────────────────────────────────────────────────
let _toastTimer;
function toast(msg, type = 'ok') {
  const t = document.getElementById('toast');
  t.textContent = (type==='ok'?'✓ ':type==='error'?'✗ ':'ℹ ') + msg;
  t.className = 'toast show' + (type==='error'?' error':type==='info'?' info':'');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove('show'), 3000);
}

// ── Navigation ────────────────────────────────────────────────────────────────
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const page = document.getElementById('page-' + id);
  const nav  = document.getElementById('nav-' + id);
  if (page) page.classList.add('active');
  if (nav)  nav.classList.add('active');
  // Chargements spéciaux par page
  if (id === 'dashboard') loadDashboard();
  if (id === 'donnees') loadTable('producteurs', document.querySelector('.tabs .tab'));
  if (id === 'export') loadSyncStatus();
  if (id === 'parcelle') loadProducteursSelect();
  if (id === 'liste-producteurs') loadListeProducteurs();
}

function resetForm(id) {
  const f = document.getElementById(id);
  if (f) f.reset();
}

// ── API Helper ────────────────────────────────────────────────────────────────
async function apiGet(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
async function apiPost(path, body, isFormData=false) {
  const opts = { method:'POST' };
  if (isFormData) { opts.body = body; }
  else { opts.headers = {'Content-Type':'application/json'}; opts.body = JSON.stringify(body); }
  const r = await fetch(API + path, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ── DASHBOARD ─────────────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const d = await apiGet('/api/analyse/dashboard/stats');
    document.getElementById('s-prod').textContent   = d.producteurs;
    document.getElementById('s-ha').textContent     = d.surface_ha + ' ha';
    document.getElementById('s-phyto').textContent  = d.phyto;
    document.getElementById('s-analyse').textContent = d.analyses;
    document.getElementById('badge-donnees').textContent = d.producteurs + d.parcelles;
    renderPrixBars(d.prix_marche);
    renderPluieBars(d.pluviometrie);
  } catch(e) { console.error(e); }
}

function renderPrixBars(prix) {
  const colors = ['g','a','b','t','g','a'];
  const max = Math.max(...prix.map(p=>p.prix_moyen||0), 1);
  const el = document.getElementById('prix-bars');
  if (!el) return;
  el.innerHTML = prix.map((p,i) => `
    <div class="bar-row">
      <span class="bar-label">${p.produit}</span>
      <div class="bar-track">
        <div class="bar-fill ${colors[i%colors.length]}" style="width:${Math.round(p.prix_moyen/max*100)}%">
          <span class="bar-val">${Math.round(p.prix_moyen).toLocaleString('fr')} F</span>
        </div>
      </div>
    </div>`).join('');
}

function renderPluieBars(pluie) {
  const el = document.getElementById('pluie-bars');
  if (!el || !pluie.length) return;
  const max = Math.max(...pluie.map(p=>p.pluviometrie_mm||0), 1);
  el.innerHTML = pluie.map(p => `
    <div class="bar-row">
      <span class="bar-label">${p.mois_annee}</span>
      <div class="bar-track">
        <div class="bar-fill b" style="width:${Math.round((p.pluviometrie_mm||0)/max*100)}%">
          <span class="bar-val">${p.pluviometrie_mm||0} mm</span>
        </div>
      </div>
    </div>`).join('');
}

// ── SYNC STATUS ───────────────────────────────────────────────────────────────
async function loadSyncStatus() {
  try {
    const d = await apiGet('/api/export/sync-status');
    const chip = document.getElementById('sync-label');
    const dot  = document.querySelector('.pulse-dot');
    if (d.total_pending === 0) {
      chip.textContent = LANG[currentLang].sync_ok;
      dot.classList.add('ok');
    } else {
      chip.textContent = `${d.total_pending} ${LANG[currentLang].sync_pending}`;
      dot.classList.remove('ok');
    }
    const el = document.getElementById('sync-status-detail');
    if (!el) return;
    el.innerHTML = `<div class="sync-detail">` +
      Object.entries(d.details).map(([k,v]) => `
        <div class="sync-item">
          <span class="sync-name">${k}</span>
          <span class="sync-count ${v===0?'ok':'warn'}">${v===0?'✓':v}</span>
        </div>`).join('') + `</div>`;
  } catch(e) {}
}

async function syncAll() {
  const tables = ['producteurs','parcelles','prix_marche','phyto','climatologie'];
  for (const t of tables) {
    try { await apiPost(`/api/export/marquer-synced/${t}`, {}); } catch(e){}
  }
  toast('Synchronisation terminée ✓');
  loadSyncStatus();
}

// ── PRODUCTEUR ────────────────────────────────────────────────────────────────
function toggleGIC(sel) {
  document.getElementById('field-gic').style.display = sel.value==='1' ? 'flex' : 'none';
}

async function submitProducteur(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd.entries());
  body.consentement_rgpd = body.consentement_rgpd ? 1 : 0;
  body.appartient_gic = parseInt(body.appartient_gic) || 0;
  body.age = parseInt(body.age) || null;
  body.taille_menage = parseInt(body.taille_menage) || null;
  body.actifs_agricoles = parseInt(body.actifs_agricoles) || null;
  try {
    const r = await apiPost('/api/producteurs/', body);
    toast(`Producteur #${r.id} enregistré ✓`);
    e.target.reset();
    loadSyncStatus();
  } catch(err) { toast('Erreur: ' + err.message, 'error'); }
}

async function loadListeProducteurs() {
  try {
    const prods = await apiGet('/api/producteurs/');
    const el = document.getElementById('table-producteurs');
    if (!prods.length) { el.innerHTML = '<div class="loading">Aucun producteur enregistré.</div>'; return; }
    el.innerHTML = `<table class="data-table">
      <thead><tr><th>#</th><th>Nom</th><th>Localité</th><th>Dép.</th><th>Culture</th><th>GIC</th><th>Statut</th></tr></thead>
      <tbody>${prods.map(p=>`
        <tr>
          <td>${p.id}</td><td>${p.nom}</td><td>${p.localite||'—'}</td>
          <td>${p.departement||'—'}</td><td>${p.culture_principale||'—'}</td>
          <td>${p.appartient_gic?'✓ '+p.nom_gic:'—'}</td>
          <td><span class="status-pill ${p.synced?'ok':'wait'}">${p.synced?'✓ Sync':'⏳ Local'}</span></td>
        </tr>`).join('')}
      </tbody></table>`;
  } catch(e) { toast('Erreur chargement', 'error'); }
}

async function loadProducteursSelect() {
  try {
    const prods = await apiGet('/api/producteurs/');
    const sel = document.getElementById('select-producteur-parcelle');
    sel.innerHTML = '<option value="">-- Choisir --</option>' +
      prods.map(p=>`<option value="${p.id}">${p.nom} (${p.localite||'?'})</option>`).join('');
  } catch(e) {}
}

// ── GPS & PARCELLE ────────────────────────────────────────────────────────────
let gpsWatcher = null;
let gpsPosition = null;
let polygonPoints = [];

function initGPS() {
  if (!navigator.geolocation) {
    setGPSStatus(false, 'GPS non disponible sur ce navigateur');
    return;
  }
  setGPSStatus(true, 'Activation GPS...');
  gpsWatcher = navigator.geolocation.watchPosition(
    pos => {
      gpsPosition = pos;
      document.getElementById('gps-lat').textContent = pos.coords.latitude.toFixed(6) + '° N';
      document.getElementById('gps-lng').textContent = pos.coords.longitude.toFixed(6) + '° E';
      document.getElementById('gps-alt').textContent = pos.coords.altitude ? Math.round(pos.coords.altitude) + ' m' : '— m';
      document.getElementById('gps-accuracy').textContent = `Précision: ±${Math.round(pos.coords.accuracy)} m`;
      setGPSStatus(true, 'Signal GPS actif');
    },
    err => setGPSStatus(false, 'Signal GPS indisponible — ' + err.message),
    { enableHighAccuracy: true, maximumAge: 2000, timeout: 10000 }
  );
}

function setGPSStatus(active, msg) {
  const s = document.getElementById('gps-status');
  const l = document.getElementById('gps-label-text');
  if (!s) return;
  s.className = 'gps-status ' + (active ? 'active' : 'inactive');
  l.textContent = msg;
}

function addGPSPoint() {
  if (!gpsPosition) {
    toast('GPS non disponible. Utilisation de coordonnées simulées.', 'info');
    // Coordonnées simulées pour démo
    gpsPosition = {
      coords: {
        latitude: 3.8613 + (Math.random() * 0.02 - 0.01),
        longitude: 11.5214 + (Math.random() * 0.02 - 0.01),
        altitude: 740 + Math.random() * 20,
        accuracy: 3 + Math.random() * 5
      }
    };
  }
  const lat = gpsPosition.coords.latitude;
  const lng = gpsPosition.coords.longitude;
  polygonPoints.push({ lat, lng });
  renderPolygon();
  calculateSuperficie();
  toast(`Point P${polygonPoints.length} ajouté (${lat.toFixed(4)}, ${lng.toFixed(4)})`);
}

function undoLastPoint() {
  if (polygonPoints.length) { polygonPoints.pop(); renderPolygon(); calculateSuperficie(); }
}

function clearPolygon() {
  polygonPoints = [];
  renderPolygon();
  document.getElementById('superficie').textContent = '0.00 ha';
}

function renderPolygon() {
  const container = document.getElementById('polygon-pts');
  const hint = document.getElementById('map-hint');
  container.innerHTML = polygonPoints.map((p,i) =>
    `<span class="pt-badge">P${i+1}: ${p.lat.toFixed(4)}, ${p.lng.toFixed(4)}</span>`
  ).join('');
  if (hint) hint.style.display = polygonPoints.length ? 'none' : 'block';
  // Dessin SVG simple
  drawMapPolygon();
}

function drawMapPolygon() {
  const canvas = document.getElementById('map-canvas');
  if (!canvas || !polygonPoints.length) { if(canvas) canvas.innerHTML=''; return; }
  const W = canvas.offsetWidth || 400;
  const H = canvas.offsetHeight || 200;
  const lats = polygonPoints.map(p=>p.lat);
  const lngs = polygonPoints.map(p=>p.lng);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const pad = 20;
  const scaleX = (maxLng===minLng) ? 1 : (W-2*pad)/(maxLng-minLng);
  const scaleY = (maxLat===minLat) ? 1 : (H-2*pad)/(maxLat-minLat);
  const pts = polygonPoints.map(p => ({
    x: pad + (p.lng-minLng)*scaleX,
    y: H - pad - (p.lat-minLat)*scaleY
  }));
  const ptStr = pts.map(p=>`${p.x},${p.y}`).join(' ');
  canvas.innerHTML = `<svg width="${W}" height="${H}" style="position:absolute;inset:0">
    <polygon points="${ptStr}" fill="rgba(74,222,128,.15)" stroke="#4ade80" stroke-width="2" stroke-linejoin="round"/>
    ${pts.map((p,i)=>`<circle cx="${p.x}" cy="${p.y}" r="4" fill="#4ade80"/>
      <text x="${p.x+6}" y="${p.y-5}" font-size="10" fill="#86efac">P${i+1}</text>`).join('')}
  </svg>`;
}

function calculateSuperficie() {
  if (polygonPoints.length < 3) { document.getElementById('superficie').textContent = '0.00 ha'; return; }
  const coords = polygonPoints.map(p=>[p.lng, p.lat]);
  coords.push(coords[0]);
  let area = 0;
  const R = 6378137;
  for (let i=0; i<coords.length-1; i++) {
    const lat1 = coords[i][1] * Math.PI/180;
    const lat2 = coords[i+1][1] * Math.PI/180;
    const dLng = (coords[i+1][0] - coords[i][0]) * Math.PI/180;
    area += dLng * (2 + Math.sin(lat1) + Math.sin(lat2));
  }
  const ha = Math.abs(area * R * R / 2) / 10000;
  document.getElementById('superficie').textContent = ha.toFixed(4) + ' ha';
}

async function saveParcelle() {
  const idProd = document.getElementById('select-producteur-parcelle').value;
  if (!idProd) { toast('Sélectionnez un producteur', 'error'); return; }
  if (polygonPoints.length < 3) { toast('Minimum 3 points GPS requis', 'error'); return; }
  const coords = polygonPoints.map(p=>[p.lng, p.lat]);
  coords.push(coords[0]);
  const geojson = JSON.stringify({ type:'Polygon', coordinates:[coords] });
  const ha = parseFloat(document.getElementById('superficie').textContent);
  const body = {
    id_producteur: parseInt(idProd),
    geojson,
    superficie_ha: ha,
    type_sol: document.getElementById('parc-type-sol').value,
    culture_principale: document.getElementById('parc-culture').value,
    methode_mesure: document.getElementById('parc-methode').value,
    type_terrain: document.getElementById('parc-terrain').value,
    observations: document.getElementById('parc-obs').value,
  };
  try {
    const r = await apiPost('/api/parcelles/', body);
    toast(`Parcelle #${r.id} enregistrée — ${r.superficie_ha} ha ✓`);
    clearPolygon();
    loadSyncStatus();
  } catch(e) { toast('Erreur: ' + e.message, 'error'); }
}

// ── PHOTO / PHYTO ─────────────────────────────────────────────────────────────
let capturedPhoto = null;

function triggerCamera() {
  document.getElementById('camera-input').click();
}

function handlePhotoCapture(input) {
  const file = input.files[0];
  if (!file) return;
  capturedPhoto = file;
  const reader = new FileReader();
  reader.onload = e => {
    const thumbs = document.getElementById('photo-thumbs');
    thumbs.innerHTML = `<div class="photo-thumb">
      <img src="${e.target.result}" alt="photo">
      <div class="photo-del" onclick="removePhoto()">✕</div>
    </div>`;
    const exif = document.getElementById('exif-display');
    exif.style.display = 'block';
    const now = new Date().toLocaleString('fr-FR');
    const lat = gpsPosition ? gpsPosition.coords.latitude.toFixed(6) : '—';
    const lng = gpsPosition ? gpsPosition.coords.longitude.toFixed(6) : '—';
    exif.innerHTML = `📍 GPS : ${lat}°N, ${lng}°E &nbsp;·&nbsp; ⏱️ ${now} &nbsp;·&nbsp; 🗜️ Compression 65%`;
  };
  reader.readAsDataURL(file);
}

function removePhoto() {
  capturedPhoto = null;
  document.getElementById('photo-thumbs').innerHTML = '';
  document.getElementById('exif-display').style.display = 'none';
  document.getElementById('camera-input').value = '';
}

async function submitPhyto(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  if (capturedPhoto) fd.append('photo', capturedPhoto, capturedPhoto.name);
  if (gpsPosition) {
    fd.append('latitude', gpsPosition.coords.latitude);
    fd.append('longitude', gpsPosition.coords.longitude);
    if (gpsPosition.coords.altitude) fd.append('altitude', gpsPosition.coords.altitude);
  }
  try {
    const r = await apiPost('/api/phyto/', fd, true);
    toast(`Relevé phytosanitaire #${r.id} enregistré ✓`);
    e.target.reset();
    removePhoto();
    loadSyncStatus();
  } catch(err) { toast('Erreur: ' + err.message, 'error'); }
}

// ── MARCHÉ ────────────────────────────────────────────────────────────────────
async function submitMarche(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const marche = fd.get('marche');
  const date_releve = fd.get('date_releve');
  const produits = ['Maïs','Cacao','Oignon','Manioc','Plantain','Tomate','Café','Riz','Haricot'];
  const batch = [];
  for (const p of produits) {
    const val = parseFloat(fd.get('prix_'+p));
    if (val > 0) batch.push({ marche, date_releve, produit:p, prix_fcfa:val });
  }
  if (!batch.length) { toast('Saisissez au moins un prix', 'error'); return; }
  try {
    const r = await apiPost('/api/marche/batch', batch);
    toast(`${r.count} prix enregistrés pour ${marche} ✓`);
    e.target.reset();
    loadSyncStatus();
  } catch(err) { toast('Erreur: ' + err.message, 'error'); }
}

// ── CLIMATOLOGIE ──────────────────────────────────────────────────────────────
async function submitClimat(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd.entries());
  for (const k of ['pluviometrie_mm','intensite_max','temp_moyenne','humidite_moy'])
    if (body[k]) body[k] = parseFloat(body[k]);
  if (body.jours_pluie) body.jours_pluie = parseInt(body.jours_pluie);
  try {
    const r = await apiPost('/api/climat/', body);
    toast(`Relevé climatologique enregistré ✓ (#${r.id})`);
    e.target.reset();
    loadSyncStatus();
  } catch(err) { toast('Erreur: ' + err.message, 'error'); }
}

// ── ANALYSES ──────────────────────────────────────────────────────────────────
async function lancerAnalyse(type) {
  const container = document.getElementById('analyse-result-container');
  const spinner   = document.getElementById('analyse-spinner');
  const result    = document.getElementById('analyse-result');
  container.style.display = 'block';
  spinner.style.display = 'block';
  result.innerHTML = '';
  container.scrollIntoView({ behavior:'smooth' });
  try {
    const data = await apiPost('/api/analyse/lancer', { type_analyse: type, n_clusters:3, n_components:2 });
    spinner.style.display = 'none';
    renderAnalyseResult(data, type);
  } catch(e) {
    spinner.style.display = 'none';
    result.innerHTML = `<div style="color:var(--red)">❌ Erreur : ${e.message}</div>`;
  }
}

function renderAnalyseResult(d, type) {
  const el = document.getElementById('analyse-result');

  if (type === 'stats_descriptives') {
    const vars = d.variables;
    el.innerHTML = `<h4 style="margin-bottom:12px;color:var(--green)">${d.type}</h4>` +
      Object.entries(vars).map(([v, s]) => `
        <div style="margin-bottom:14px">
          <div style="font-size:12px;color:var(--text3);margin-bottom:8px;text-transform:uppercase">${v}</div>
          <div class="result-grid">
            ${[['N obs.', s.n], ['Moyenne', s.mean], ['Médiane', s.median], ['Écart-type', s.std],
               ['Min', s.min], ['Max', s.max], ['Q25', s.q25], ['Q75', s.q75]]
              .map(([l,v2]) => `<div class="result-item"><div class="result-label">${l}</div><div class="result-value" style="font-size:16px">${v2}</div></div>`).join('')}
          </div>
        </div>`).join('');
    return;
  }

  if (type === 'regression_simple') {
    el.innerHTML = `
      <h4 style="margin-bottom:12px;color:var(--green)">${d.type}</h4>
      <div class="result-grid">
        <div class="result-item"><div class="result-label">Équation</div><div style="font-size:13px;font-weight:600;color:var(--text);margin-top:4px">${d.equation}</div></div>
        <div class="result-item"><div class="result-label">R² (coefficient de détermination)</div><div class="result-value">${d.r2}</div></div>
        <div class="result-item"><div class="result-label">r de Pearson</div><div class="result-value">${d.r_pearson}</div></div>
        <div class="result-item"><div class="result-label">RMSE</div><div class="result-value">${d.rmse}</div></div>
        <div class="result-item"><div class="result-label">N observations</div><div class="result-value">${d.n}</div></div>
        <div class="result-item"><div class="result-label">Pente (a)</div><div class="result-value">${d.pente}</div></div>
      </div>
      ${renderMiniChart(d.x_data, d.y_data, d.y_pred, d.labels_x)}
      <div class="interp-box">💡 ${d.interpretation}</div>`;
    return;
  }

  if (type === 'regression_multiple') {
    const coeffs = Object.entries(d.coefficients).map(([k,v2])=>
      `<div class="result-item"><div class="result-label">Coeff. ${k}</div><div class="result-value" style="font-size:16px">${v2}</div></div>`).join('');
    el.innerHTML = `
      <h4 style="margin-bottom:12px;color:var(--green)">${d.type}</h4>
      <div style="background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:12px;font-size:13px;color:var(--greenDim);margin-bottom:12px;font-family:var(--font-head)">${d.equation}</div>
      <div class="result-grid">
        <div class="result-item"><div class="result-label">R²</div><div class="result-value">${d.r2}</div></div>
        <div class="result-item"><div class="result-label">R² ajusté</div><div class="result-value">${d.r2_ajuste}</div></div>
        <div class="result-item"><div class="result-label">RMSE</div><div class="result-value">${d.rmse}</div></div>
        <div class="result-item"><div class="result-label">N variables</div><div class="result-value">${d.p_variables}</div></div>
        ${coeffs}
      </div>
      <div class="interp-box">💡 ${d.interpretation}</div>`;
    return;
  }

  if (type === 'pca') {
    const bars = d.variance_expliquee_pct.map((v2,i) => `
      <div class="prog-wrap">
        <div class="prog-label"><span>Composante ${i+1}</span><span>${v2}%</span></div>
        <div class="prog-bar"><div class="prog-fill ${i===0?'':'amber'}" style="width:${v2}%"></div></div>
      </div>`).join('');
    el.innerHTML = `
      <h4 style="margin-bottom:12px;color:var(--green)">${d.type}</h4>
      <div class="result-grid">
        <div class="result-item"><div class="result-label">Observations</div><div class="result-value">${d.n_observations}</div></div>
        <div class="result-item"><div class="result-label">Variables</div><div class="result-value">${d.n_variables}</div></div>
        <div class="result-item"><div class="result-label">Variance totale expliquée</div><div class="result-value">${d.variance_cumulee_pct.at(-1)}%</div></div>
        <div class="result-item"><div class="result-label">Composantes retenues</div><div class="result-value">${d.n_composantes}</div></div>
      </div>
      <div style="margin:12px 0">${bars}</div>
      <div class="interp-box">💡 ${d.interpretation}</div>`;
    return;
  }

  if (type === 'clustering') {
    const sizes = d.tailles_clusters.map((s,i)=>
      `<div class="result-item"><div class="result-label">Cluster ${i+1}</div><div class="result-value">${s} obs.</div></div>`).join('');
    el.innerHTML = `
      <h4 style="margin-bottom:12px;color:var(--green)">${d.type}</h4>
      <div class="result-grid">
        <div class="result-item"><div class="result-label">Nombre de clusters (k)</div><div class="result-value">${d.k}</div></div>
        <div class="result-item"><div class="result-label">Observations totales</div><div class="result-value">${d.n_observations}</div></div>
        <div class="result-item"><div class="result-label">Inertie intra-cluster</div><div class="result-value">${d.inertia}</div></div>
        ${sizes}
      </div>
      <div class="interp-box">💡 ${d.interpretation}</div>`;
    return;
  }

  if (type === 'classification_supervisee') {
    const classes = d.classes;
    const confRows = classes.map(c =>
      `<tr><th>${c}</th>${classes.map(c2=>`<td style="text-align:center;background:${d.confusion_matrix[c][c2]>0?'rgba(74,222,128,.1)':'transparent'}">${d.confusion_matrix[c][c2]}</td>`).join('')}</tr>`
    ).join('');
    el.innerHTML = `
      <h4 style="margin-bottom:12px;color:var(--green)">${d.type}</h4>
      <div class="result-grid">
        <div class="result-item"><div class="result-label">Précision (Accuracy)</div><div class="result-value">${d.accuracy_pct}%</div></div>
        <div class="result-item"><div class="result-label">Échantillon d'entraînement</div><div class="result-value">${d.n_train}</div></div>
        <div class="result-item"><div class="result-label">Échantillon de test</div><div class="result-value">${d.n_test}</div></div>
        <div class="result-item"><div class="result-label">Classes</div><div class="result-value" style="font-size:13px">${d.classes.join(' · ')}</div></div>
      </div>
      <div style="margin-top:12px">
        <div style="font-size:12px;color:var(--text3);margin-bottom:8px">Matrice de confusion</div>
        <div style="overflow-x:auto"><table class="data-table" style="min-width:300px">
          <thead><tr><th>Réel\Prédit</th>${classes.map(c=>`<th>${c}</th>`).join('')}</tr></thead>
          <tbody>${confRows}</tbody>
        </table></div>
      </div>
      <div class="interp-box">💡 ${d.interpretation}</div>`;
    return;
  }

  el.innerHTML = `<pre style="font-size:11px;color:var(--text2);overflow-x:auto">${JSON.stringify(d, null, 2)}</pre>`;
}

function renderMiniChart(xData, yData, yPred, labels) {
  if (!xData || !xData.length) return '';
  const W = 460, H = 120, pad = 30;
  const maxY = Math.max(...yData, ...yPred);
  const minY = Math.min(...yData, ...yPred);
  const n = xData.length;
  const scaleX = (W-2*pad)/(n-1||1);
  const scaleY = (H-2*pad)/(maxY-minY||1);
  const pts = yData.map((y,i)=>({
    x: pad+i*scaleX,
    y: H-pad-(y-minY)*scaleY
  }));
  const predPts = yPred.map((y,i)=>({
    x: pad+i*scaleX,
    y: H-pad-(y-minY)*scaleY
  }));
  const predLine = predPts.map(p=>`${p.x},${p.y}`).join(' ');
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;margin:12px 0;background:var(--bg3);border-radius:8px;border:1px solid var(--border)">
    <polyline points="${predLine}" fill="none" stroke="#4ade80" stroke-width="2" stroke-dasharray="4,2"/>
    ${pts.map(p=>`<circle cx="${p.x}" cy="${p.y}" r="3" fill="#60a5fa"/>`).join('')}
    <text x="${pad}" y="${H-8}" font-size="9" fill="#5a7a5a">Observations (bleu) · Régression (vert)</text>
  </svg>`;
}

// ── DATA TABLE ────────────────────────────────────────────────────────────────
async function loadTable(table, tabEl) {
  if (tabEl) {
    document.querySelectorAll('.tabs .tab').forEach(t=>t.classList.remove('active'));
    tabEl.classList.add('active');
  }
  const el = document.getElementById('data-table-container');
  el.innerHTML = '<div class="loading">Chargement...</div>';
  try {
    let rows = [];
    if (table==='producteurs') rows = await apiGet('/api/producteurs/');
    else if (table==='parcelles') rows = await apiGet('/api/parcelles/');
    else if (table==='prix_marche') rows = await apiGet('/api/marche/');
    else if (table==='phyto') rows = await apiGet('/api/phyto/');
    else if (table==='climatologie') rows = await apiGet('/api/climat/');
    else if (table==='analyses') rows = await apiGet('/api/analyse/historique');
    if (!rows.length) { el.innerHTML = '<div class="loading">Aucune donnée.</div>'; return; }
    const keys = Object.keys(rows[0]).filter(k=>!['geojson','description','photo_path'].includes(k));
    el.innerHTML = `<table class="data-table"><thead><tr>${keys.map(k=>`<th>${k}</th>`).join('')}</tr></thead>
      <tbody>${rows.map(r=>`<tr>${keys.map(k=>`<td title="${r[k]??''}">${formatCell(k,r[k])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  } catch(e) { el.innerHTML = `<div class="loading" style="color:var(--red)">Erreur: ${e.message}</div>`; }
}

function formatCell(key, val) {
  if (val===null||val===undefined) return '—';
  if (key==='synced') return `<span class="status-pill ${val?'ok':'wait'}">${val?'✓':'⏳'}</span>`;
  if (key==='consentement_rgpd') return val ? '✓' : '✗';
  if (key==='appartient_gic') return val ? '✓' : '✗';
  if (typeof val==='number' && key.includes('fcfa')) return val.toLocaleString('fr') + ' F';
  return String(val).substring(0, 50);
}

// ── EXPORT ────────────────────────────────────────────────────────────────────
function exportData(fmt) {
  const table = document.getElementById('exp-table').value;
  window.open(`${API}/api/export/${fmt}/${table}`, '_blank');
}
function exportRapport() {
  window.open(`${API}/api/export/rapport-html`, '_blank');
}

// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Date par défaut pour marché
  const dateInput = document.querySelector('input[name="date_releve"]');
  if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];

  // GPS si page parcelle
  initGPS();
  window.addEventListener('resize', drawMapPolygon);

  // Chargement initial
  loadDashboard();
  loadSyncStatus();

  // Rafraîchissement sync toutes les 30s
  setInterval(loadSyncStatus, 30000);
});
