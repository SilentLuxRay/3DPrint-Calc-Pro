// DATABASE & LINGUE
let db = JSON.parse(localStorage.getItem('3DPrintCalc_Pro_DB')) || {
    printers: [], filaments: [], elec_cost: 0.25, lang: "ITA"
};

const translations = {
    ITA: {
        nav_calc: "Preventivatore", nav_printers: "Stampanti", nav_filaments: "Filamenti",
        h_calc: "Nuovo Preventivo", h_setup: "SETUP STAMPA", h_bus: "BUSINESS",
        lbl_g: "Grammi (g)", lbl_h: "Ore Stampa (h)", lbl_markup: "Rincaro (%)",
        lbl_iva: "IVA (%)", lbl_elec: "Energia (€/kWh)", lbl_rate: "Tariffa (€/h)",
        h_mod: "Modellazione", h_post: "Post-Produzione", h_cons: "Consumabili",
        btn_calc: "CALCOLA PREVENTIVO", btn_reg: "REGISTRA", btn_rep: "REPORT",
        btn_add_p: "+ Nuova Stampante", btn_add_f: "+ Nuovo Filamento",
        h_wear: "Componenti Usura", config: "Edit", back: "Torna",
        reg_ok: "✅ REGISTRATO", tech: "Totale Tecnico", labor: "Lavoro",
        mat: "Materiale", en: "Energia", wear: "Usura", cons: "Consumabili"
    },
    ENG: {
        nav_calc: "Estimator", nav_printers: "Printers", nav_filaments: "Filaments",
        h_calc: "New Estimate", h_setup: "PRINT SETUP", h_bus: "BUSINESS",
        lbl_g: "Grams (g)", lbl_h: "Print Time (h)", lbl_markup: "Markup (%)",
        lbl_iva: "Tax (%)", lbl_elec: "Energy ($/kWh)", lbl_rate: "Rate ($/h)",
        h_mod: "Modeling", h_post: "Post-Processing", h_cons: "Consumables",
        btn_calc: "CALCULATE QUOTE", btn_reg: "REGISTER", btn_rep: "REPORT",
        btn_add_p: "+ New Printer", btn_add_f: "+ New Filament",
        h_wear: "Wear Parts", config: "Edit", back: "Back",
        reg_ok: "✅ REGISTERED", tech: "Tech Total", labor: "Labor",
        mat: "Material", en: "Power", wear: "Wear", cons: "Consumables"
    }
};

let editingId = null;
let modPhases = [], postPhases = [], consumables = [];
let lastCalc = null;

function save() { localStorage.setItem('3DPrintCalc_Pro_DB', JSON.stringify(db)); }

function toggleLang() {
    db.lang = db.lang === 'ITA' ? 'ENG' : 'ITA';
    save(); applyLang();
}

function applyLang() {
    const l = translations[db.lang];
    Object.keys(l).forEach(key => {
        const el = document.getElementById(key.replace('_','-')) || document.getElementById(key);
        if(el) el.innerText = l[key];
    });
    document.getElementById('lang-btn').innerText = "🌐 " + db.lang;
    refreshOptions();
}

// NAVIGAZIONE
function showTab(id) {
    document.querySelectorAll('.tab').forEach(x => x.style.display = 'none');
    document.getElementById('tab-' + id).style.display = 'block';
    document.querySelectorAll('.nav-btn').forEach(x => x.classList.remove('active'));
    document.getElementById('nav-' + id).classList.add('active');
    if(id === 'calc') refreshOptions();
    if(id === 'printers') renderPrinters();
    if(id === 'filaments') renderFilaments();
}

// PREVENTIVATORE
function refreshOptions() {
    document.getElementById('sel-printer').innerHTML = db.printers.map(p => `<option value="${p.id}">${p.name}</option>`).join('') || '<option>---</option>';
    document.getElementById('sel-filament').innerHTML = db.filaments.map(f => {
        let name = `${f.brand} ${f.material}`;
        if(f.color) name += ` (${f.color})`;
        return `<option value="${f.id}">${name}</option>`;
    }).join('') || '<option>---</option>';
    updateColorPreview();
}

function updateColorPreview() {
    const f = db.filaments.find(x => x.id == document.getElementById('sel-filament').value);
    document.getElementById('color-preview').style.backgroundColor = f ? f.hex : '#fff';
}

function addPhase(type) {
    const n = document.getElementById(`add-${type}-n`), c = document.getElementById(`add-${type}-c`);
    if(!n.value || !c.value) return;
    const item = { name: n.value, cost: parseFloat(c.value) };
    if(type === 'mod') modPhases.push(item); else if(type === 'post') postPhases.push(item); else consumables.push(item);
    n.value = ''; c.value = ''; renderPhaseLists();
}

function renderPhaseLists() {
    const render = (list, elId, type) => {
        document.getElementById(elId).innerHTML = list.map((x, i) => `
            <div class="phase-row"><span>${x.name} (€${x.cost.toFixed(2)})</span><b onclick="removePhase('${type}',${i})" style="color:red;cursor:pointer">x</b></div>
        `).join('');
    };
    render(modPhases, 'list-mod', 'mod'); render(postPhases, 'list-post', 'post'); render(consumables, 'list-cons', 'cons');
}

function removePhase(type, i) {
    if(type === 'mod') modPhases.splice(i, 1); else if(type === 'post') postPhases.splice(i, 1); else consumables.splice(i, 1);
    renderPhaseLists();
}

function calculate() {
    const p = db.printers.find(x => x.id == document.getElementById('sel-printer').value);
    const f = db.filaments.find(x => x.id == document.getElementById('sel-filament').value);
    const l = translations[db.lang];
    if(!p || !f) return alert("Seleziona setup!");

    const g = parseFloat(document.getElementById('in-g').value) || 0;
    const h = parseFloat(document.getElementById('in-h').value) || 0;
    const mk = parseFloat(document.getElementById('in-markup').value) || 0;
    const iva = parseFloat(document.getElementById('in-iva').value) || 0;
    const elec = parseFloat(document.getElementById('in-elec').value) || 0;

    const cMat = (f.price / f.weight) * g;
    const cEn = (p.watt / 1000) * h * elec;
    const cWearB = (p.base_cost / p.life) * h;
    const cWearP = p.components.reduce((s, c) => s + (c.cost / c.life) * h, 0);
    const cCons = consumables.reduce((s, c) => s + c.cost, 0);

    const tech = cMat + cEn + cWearB + cWearP + cCons;
    const labor = modPhases.reduce((s, c) => s + c.cost, 0) + postPhases.reduce((s, c) => s + c.cost, 0);
    const final = (tech + labor) * (1 + mk/100) * (1 + iva/100);

    document.getElementById('total-price').innerText = `€ ${final.toFixed(2)}`;
    document.getElementById('detailed-breakdown').innerText = 
        `${l.mat}: €${cMat.toFixed(2)} | ${l.en}: €${cEn.toFixed(2)} | ${l.wear}: €${(cWearB+cWearP).toFixed(2)} | ${l.cons}: €${cCons.toFixed(2)}\n` +
        `${l.labor}: €${labor.toFixed(2)} | ${l.tech}: €${tech.toFixed(2)}`;
    
    lastCalc = { p, f, g, h, final, cMat, cEn, cWear: cWearB+cWearP, cCons, labor, tech, mk, iva };
    document.getElementById('btn-reg').disabled = false;
    document.getElementById('btn-rep').disabled = false;
    document.getElementById('btn-reg').innerText = l.btn_reg;
    db.elec_cost = elec; save();
}

function register() {
    lastCalc.p.used_hours += lastCalc.h;
    lastCalc.p.components.forEach(c => c.used_hours += lastCalc.h);
    lastCalc.f.rem_weight -= lastCalc.g;
    save(); document.getElementById('btn-reg').innerText = translations[db.lang].reg_ok; document.getElementById('btn-reg').disabled = true;
}

function generateReport() {
    const d = lastCalc;
    const modTxt = modPhases.length ? modPhases.map(x => ` - ${x.name}: €${x.cost.toFixed(2)}`).join('\n') : " - Nessuna";
    const postTxt = postPhases.length ? postPhases.map(x => ` - ${x.name}: €${x.cost.toFixed(2)}`).join('\n') : " - Nessuna";
    const consTxt = consumables.length ? consumables.map(x => ` - ${x.name}: €${x.cost.toFixed(2)}`).join('\n') : " - Nessuno";

    const report = `=========================================
      REPORT PREVENTIVO 3DPRINTCALC
=========================================
STAMPANTE:  ${d.p.name}
MATERIALE:  ${d.f.brand} ${d.f.material} (${d.f.color})
-----------------------------------------
1. COSTI TECNICI (VIVI)
- Materiale:     € ${d.cMat.toFixed(2)}
- Energia:       € ${d.cEn.toFixed(2)}
- Usura:         € ${d.cWear.toFixed(2)}
- Consumabili:   € ${d.cCons.toFixed(2)}
${consTxt}
TOTALE TECNICO:  € ${d.tech.toFixed(2)}
-----------------------------------------
2. LAVORAZIONI
MODELLAZIONE:
${modTxt}
POST-PRODUZIONE:
${postTxt}
TOTALE LAVORO:   € ${d.labor.toFixed(2)}
-----------------------------------------
RIEPILOGO FINALE
Rincaro (${d.mk}%): € ${( (d.tech+d.labor) * d.mk/100 ).toFixed(2)}
IVA (${d.iva}%):     € ${( d.final - (d.final/(1+d.iva/100)) ).toFixed(2)}

TOTALE CLIENTE:  € ${d.final.toFixed(2)}
=========================================`;

    const blob = new Blob([report], { type: 'text/plain' });
    const a = document.createElement('a'); a.download = `Preventivo_${Date.now()}.txt`; a.href = URL.createObjectURL(blob); a.click();
}

// GESTIONE STAMPANTI & FILAMENTI (Formato compresso come richiesto per Web)
function renderPrinters() {
    document.getElementById('p-list-view').style.display = 'block'; document.getElementById('p-edit-view').style.display = 'none';
    document.getElementById('printer-list').innerHTML = db.printers.map(p => `<div class="item-card"><span><b>${p.name}</b> (${p.used_hours.toFixed(1)}h)</span><button onclick="editPrinter(${p.id})">Edit</button></div>`).join('');
}
function newPrinter() { const id = Date.now(); db.printers.push({ id, name: "New", base_cost: 300, life: 5000, used_hours: 0, watt: 150, components: [] }); save(); editPrinter(id); }
function editPrinter(id) {
    editingId = id; const p = db.printers.find(x => x.id == id);
    document.getElementById('p-list-view').style.display = 'none'; document.getElementById('p-edit-view').style.display = 'block';
    document.getElementById('p-form').innerHTML = `<div class="input-group"><label>Nome</label><input type="text" id="ep-n" value="${p.name}"></div><div class="input-group"><label>Costo €</label><input type="number" id="ep-c" value="${p.base_cost}"></div><div class="input-group"><label>Life h</label><input type="number" id="ep-l" value="${p.life}"></div><div class="input-group"><label>W</label><input type="number" id="ep-w" value="${p.watt}"></div><button class="primary-btn" onclick="saveP()">Salva Base</button><button onclick="delP(${id})" style="color:red;background:none;border:none;margin-top:10px;cursor:pointer;width:100%">ELIMINA</button>`;
    renderComps();
}
function saveP() { const p = db.printers.find(x => x.id == editingId); p.name = document.getElementById('ep-n').value; p.base_cost = parseFloat(document.getElementById('ep-c').value); p.life = parseFloat(document.getElementById('ep-l').value); p.watt = parseFloat(document.getElementById('ep-w').value); save(); renderPrinters(); }
function addComp() { const p = db.printers.find(x => x.id == editingId); const n = document.getElementById('new-cp-n').value, c = parseFloat(document.getElementById('new-cp-c').value), l = parseFloat(document.getElementById('new-cp-l').value); if(n && c && l) { p.components.push({ name: n, cost: c, life: l, used_hours: 0 }); save(); renderComps(); } }
function renderComps() { const p = db.printers.find(x => x.id == editingId); document.getElementById('p-comp-list').innerHTML = p.components.map((c, i) => `<div class="phase-row"><span>${c.name} (${c.used_hours.toFixed(1)}/${c.life}h)</span><b onclick="delComp(${i})" style="color:red;cursor:pointer">x</b></div>`).join(''); }
function delComp(i) { db.printers.find(x => x.id == editingId).components.splice(i, 1); save(); renderComps(); }
function delP(id) { if(confirm("Eliminare?")) { db.printers = db.printers.filter(x => x.id !== id); save(); renderPrinters(); } }

function renderFilaments() {
    document.getElementById('f-list-view').style.display = 'block'; document.getElementById('f-edit-view').style.display = 'none';
    document.getElementById('filament-list').innerHTML = db.filaments.map(f => `<div class="item-card"><div style="display:flex;align-items:center"><div style="width:15px;height:15px;border-radius:50%;background:${f.hex};margin-right:10px;border:1px solid white"></div><span>${f.brand} ${f.material} (${f.color})</span></div><button onclick="editFil(${f.id})">Edit</button></div>`).join('');
}
function newFilament() { const id = Date.now(); db.filaments.push({ id, brand: "Brand", material: "PLA", color: "White", hex: "#ffffff", price: 25, weight: 1000, rem_weight: 1000 }); save(); editFil(id); }
function editFil(id) {
    editingId = id; const f = db.filaments.find(x => x.id == id);
    document.getElementById('f-list-view').style.display = 'none'; document.getElementById('f-edit-view').style.display = 'block';
    document.getElementById('f-form').innerHTML = `<div class="input-group"><label>Marca</label><input type="text" id="ef-b" value="${f.brand}"></div><div class="input-group"><label>Mat</label><input type="text" id="ef-m" value="${f.material}"></div><div class="input-group"><label>Colore</label><input type="text" id="ef-c" value="${f.color}"></div><div class="input-group"><label>Hex</label><input type="text" id="ef-h" value="${f.hex}"></div><div class="input-group"><label>€</label><input type="number" id="ef-p" value="${f.price}"></div><div class="input-group"><label>Peso g</label><input type="number" id="ef-w" value="${f.weight}"></div><div class="input-group"><label>Stock g</label><input type="number" id="ef-r" value="${f.rem_weight}"></div><button class="primary-btn" onclick="saveF()">Salva</button><button onclick="delF(${id})" style="color:red;background:none;border:none;margin-top:10px;cursor:pointer;width:100%">ELIMINA</button>`;
}
function saveF() { const f = db.filaments.find(x => x.id == editingId); f.brand = document.getElementById('ef-b').value; f.material = document.getElementById('ef-m').value; f.color = document.getElementById('ef-c').value; f.hex = document.getElementById('ef-h').value; f.price = parseFloat(document.getElementById('ef-p').value); f.weight = parseFloat(document.getElementById('ef-w').value); f.rem_weight = parseFloat(document.getElementById('ef-r').value); save(); renderFilaments(); }
function delF(id) { if(confirm("Eliminare?")) { db.filaments = db.filaments.filter(x => x.id !== id); save(); renderFilaments(); } }

// PROTEZIONE ANTI DEV-TOOLS
document.addEventListener('contextmenu', e => e.preventDefault());
document.onkeydown = e => { if(e.keyCode == 123 || (e.ctrlKey && e.shiftKey && (e.keyCode == 73 || e.keyCode == 74 || e.keyCode == 67)) || (e.ctrlKey && e.keyCode == 85)) return false; };

applyLang();
showTab('calc');