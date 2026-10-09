// Bird Quiz — photo ID. Question generators live in QUIZ_TYPES so a "song"
// type can be added later without touching the rest of the flow.
const ROUND_LENGTH = 10, CHOICES = 4;
const LEVELS = {
  easy:   { label: "Easy",   blurb: "Familiar birds, very different choices" },
  medium: { label: "Medium", blurb: "All species, random choices" },
  hard:   { label: "Hard",   blurb: "Look-alike choices from the same family" },
};
const app = document.getElementById("app");
let birds = [], state = null, level = "medium";

const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) {
  const j = Math.random() * (i + 1) | 0; [a[i], a[j]] = [a[j], a[i]]; } return a; };
const pick = a => a[Math.random() * a.length | 0];
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

// ---- flagged photos (stored on this device; hidden from future rounds) ----
const FLAG_KEY = "birdquiz-flags";
function getFlags() { try { return JSON.parse(localStorage.getItem(FLAG_KEY)) || {}; } catch { return {}; } }
function setFlag(file, reason) {
  const f = getFlags(); f[file] = { reason, at: new Date().toISOString() };
  try { localStorage.setItem(FLAG_KEY, JSON.stringify(f)); } catch {}
}
const goodPhotos = b => { const f = getFlags(); return b.photos.filter(p => !f[p.file]); };

// ---- question generation ----
function distractors(answer, pool) {
  const others = shuffle(pool.filter(b => b !== answer));
  const sameFam = others.filter(b => b.family === answer.family);
  const diffFam = others.filter(b => b.family !== answer.family);
  const order = level === "hard" ? [...sameFam, ...shuffle(diffFam)] : [...diffFam, ...sameFam];
  let picked = order.slice(0, CHOICES - 1);
  if (picked.length < CHOICES - 1)   // small pool: top up from everything
    picked = picked.concat(shuffle(birds.filter(b => b !== answer && !picked.includes(b))))
                   .slice(0, CHOICES - 1);
  return picked;
}
const QUIZ_TYPES = {
  photo(answer, pool) {
    const photo = pick(goodPhotos(answer));
    return { type: "photo", answer, photo, options: shuffle([answer, ...distractors(answer, pool)]) };
  },
  // song(answer, pool) { ... }  // future: audio from xeno-canto
};

function newRound() {
  const pool = level === "easy" ? birds.filter(b => b.easy) : birds;
  const playable = shuffle(pool.filter(b => goodPhotos(b).length));
  state = { i: 0, score: 0, missed: [],
            questions: playable.slice(0, ROUND_LENGTH).map(b => QUIZ_TYPES.photo(b, pool)) };
  renderQuestion();
}

// ---- views ----
function renderHome() {
  app.innerHTML = `<div class="center"><div class="hero">🐦</div><h1>Bird Quiz</h1>
    <p>Name the bird from its photo.</p><p class="sci">${birds.length} North American species</p>
    ${Object.entries(LEVELS).map(([k, v]) => `<button class="btn level" data-level="${k}">
      ${v.label}<small>${v.blurb}</small></button>`).join("")}</div>`;
  app.querySelectorAll(".level").forEach(b => b.onclick = () => { level = b.dataset.level; newRound(); });
}

const photoHTML = (p, extra = "") => `<div class="photowrap">
  <img class="backdrop" alt="" src="${esc(p.file)}"><img class="photo" alt="Bird" src="${esc(p.file)}">${extra}</div>`;

function renderQuestion() {
  const q = state.questions[state.i];
  app.innerHTML = `
    <div class="top"><span>${LEVELS[level].label} · ${state.i + 1} of ${ROUND_LENGTH}</span><span>Score ${state.score}</span></div>
    <div class="bar"><i style="width:${state.i / ROUND_LENGTH * 100}%"></i></div>
    <div id="pic">${photoHTML(q.photo)}</div>
    <div class="choices">${q.options.map((o, k) =>
      `<button class="choice" data-k="${k}">${esc(o.name)}</button>`).join("")}</div>
    <div id="after"></div>`;
  app.querySelectorAll(".choice").forEach(b => b.onclick = () => answer(q, +b.dataset.k));
}

function flagButton(q) {
  return `<button class="flagbtn" id="flag" title="Flag this photo">🚩 Flag photo</button>`;
}
function wireFlag(q) {
  const btn = document.getElementById("flag"); if (!btn) return;
  btn.onclick = () => {
    const reason = prompt("What's wrong with this photo? (bad crop, wrong bird, blurry, …)", "");
    if (reason === null) return;
    setFlag(q.photo.file, reason.trim());
    btn.textContent = "🚩 Flagged — won't show again"; btn.disabled = true;
  };
}

function answer(q, k) {
  const right = q.options[k] === q.answer;
  if (right) state.score++; else state.missed.push({ q, chosen: q.options[k] });
  app.querySelectorAll(".choice").forEach((b, j) => {
    b.disabled = true;
    if (q.options[j] === q.answer) b.classList.add("good");
    else if (j === k) b.classList.add("bad");
  });
  document.getElementById("pic").insertAdjacentHTML("beforeend",
    `<button class="infobtn" id="info" aria-label="About this bird">i</button>`);
  document.getElementById("info").onclick = () => openInfo(q.answer);
  const last = state.i === ROUND_LENGTH - 1;
  document.getElementById("after").innerHTML = `
    <p class="credit">${right ? "✅ Correct!" : "❌ It was the"} <b>${esc(q.answer.name)}</b>
      <span class="sci">(${esc(q.answer.scientific)})</span><br>
      Photo: ${esc(q.photo.author)}, ${esc(q.photo.license)} —
      <a href="${esc(q.photo.source)}" target="_blank" rel="noopener">source</a>
      · ${flagButton(q)}</p>
    <button class="btn" id="next">${last ? "See results" : "Next"}</button>`;
  wireFlag(q);
  document.getElementById("next").onclick = () => { state.i++; last ? renderResults() : renderQuestion(); };
}

// ---- info sheet ----
function infoHTML(b) {
  const i = b.info || {}, m = i.map;
  const sec = (t, x) => x ? `<h3>${t}</h3><p>${esc(x)}</p>` : "";
  return `<h2>${esc(b.name)}</h2><p class="sci">${esc(b.scientific)} · ${esc(b.family)}
      ${i.status ? `<span class="chip">${esc(i.status)}</span>` : ""}</p>
    ${sec("About", i.about)}${sec("Diet", i.diet)}${sec("Habitat & range", i.habitat)}
    ${m ? `<h3>Range map</h3><img class="map" alt="Range map of ${esc(b.name)}" src="${esc(m.file)}">
      <p class="credit">Map: ${esc(m.author)}, ${esc(m.license)} — <a href="${esc(m.source)}" target="_blank" rel="noopener">source</a></p>` : ""}
    <div id="sounds"></div>
    ${i.wiki ? `<p class="credit">Text from <a href="${esc(i.wiki)}" target="_blank" rel="noopener">Wikipedia</a>
      (CC BY-SA 4.0).</p>` : ""}`;
}
function openInfo(b) {
  const sheet = document.createElement("div");
  sheet.className = "sheet";
  sheet.innerHTML = `<div class="sheetbody"><button class="close" aria-label="Close">✕</button>${infoHTML(b)}</div>`;
  sheet.onclick = e => { if (e.target === sheet || e.target.closest(".close")) sheet.remove(); };
  document.body.appendChild(sheet);
}

// ---- results & review ----
function renderResults() {
  const miss = state.missed.length ? `<div class="miss"><b>Review — tap a bird:</b>${
    state.missed.map((m, k) => `<button class="missrow" data-k="${k}">${esc(m.q.answer.name)} <span>›</span></button>`).join("")}</div>` : "";
  app.innerHTML = `<div class="center"><div class="score">${state.score}/${ROUND_LENGTH}</div>
    <p>${state.score >= 9 ? "Expert birder! 🦅" : state.score >= 6 ? "Nice eye!" : "Keep practicing 🌱"}</p>
    ${miss}<button class="btn" id="again">Play again</button>
    <button class="btn ghost" id="home">Home</button></div>`;
  app.querySelectorAll(".missrow").forEach(b => b.onclick = () => renderReview(+b.dataset.k));
  document.getElementById("again").onclick = newRound;
  document.getElementById("home").onclick = renderHome;
}

function renderReview(k) {
  const { q, chosen } = state.missed[k];
  app.innerHTML = `<button class="btn ghost back" id="back">‹ Back to results</button>
    ${photoHTML(q.photo)}
    <p class="credit">You picked <b>${esc(chosen.name)}</b> · it was the <b>${esc(q.answer.name)}</b><br>
      Photo: ${esc(q.photo.author)}, ${esc(q.photo.license)} —
      <a href="${esc(q.photo.source)}" target="_blank" rel="noopener">source</a> · ${flagButton(q)}</p>
    <div class="review">${infoHTML(q.answer)}</div>`;
  wireFlag(q);
  document.getElementById("back").onclick = () => { renderResults(); window.scrollTo(0, 0); };
  window.scrollTo(0, 0);
}

fetch("birds.json").then(r => r.json()).then(d => { birds = d; renderHome(); })
  .catch(() => app.innerHTML = "<p>Couldn't load bird data.</p>");

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
