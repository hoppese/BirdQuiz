// Bird Quiz — multi-topic quiz engine. Each topic (birds, countries, states, ...) is registered in
// topics.js and supplies: items, modes (what a question looks like), an info card and credits.
// This file owns everything shared: home/topic screens, rounds, review, flags, bug reports, sheets.
const ROUND_LENGTH = 10, CHOICES = 4;
const LEVELS = ["easy", "medium", "hard"];
const LEVEL_LABEL = { easy: "Easy", medium: "Medium", hard: "Hard" };
const app = document.getElementById("app");
const TOPICS = {};                      // id -> topic definition (see topics.js)
let topic = null, mode = null, level = "medium", state = null, view = "home";

const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) {
  const j = Math.random() * (i + 1) | 0; [a[i], a[j]] = [a[j], a[i]]; } return a; };
const pick = a => a[Math.random() * a.length | 0];
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const link = (href, text) => `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(text)}</a>`;
function registerTopic(t) { TOPICS[t.id] = t; }

// ---- flagged photos (stored on this device; hidden from future rounds; reported to the repo) ----
const FLAG_KEY = "birdquiz-flags";
const REPORT_URL = "https://birds-api.sethhopper.com/report";
function getFlags() { try { return JSON.parse(localStorage.getItem(FLAG_KEY)) || {}; } catch { return {}; } }
function saveFlags(f) { try { localStorage.setItem(FLAG_KEY, JSON.stringify(f)); } catch {} }
function sendFlag(file) {            // best-effort; unsent flags are retried on next launch
  const f = getFlags(), e = f[file]; if (!e || e.sent) return;
  fetch(REPORT_URL, { method: "POST", headers: { "Content-Type": "application/json" }, keepalive: true,
    body: JSON.stringify({ photo: file, reason: e.reason, pageUrl: location.href, userAgent: navigator.userAgent }) })
    .then(r => { if (r.ok) { const g = getFlags(); if (g[file]) { g[file].sent = true; saveFlags(g); } } })
    .catch(() => {});
}
function setFlag(file, reason) {
  const f = getFlags(); f[file] = { reason, at: new Date().toISOString(), sent: false };
  saveFlags(f); sendFlag(file);
}
const retryFlags = () => Object.keys(getFlags()).forEach(sendFlag);
const goodPhotos = b => { const f = getFlags(); return (b.photos || []).filter(p => !f[p.file]); };

// ---- data loading ----
const loaded = {};
async function loadTopic(t) {
  if (loaded[t.id]) return t;
  const r = await fetch(t.dataUrl); if (!r.ok) throw new Error(t.dataUrl);
  t.items = await r.json();
  if (t.setup) await t.setup(t.items);
  loaded[t.id] = true; return t;
}

// ---- question generation ----
const optText = (m, it) => (m.optionText ? m.optionText(it) : it.name);
const nearScore = (t, a, o) => t.near ? t.near(a, o) : (a.group && a.group === o.group ? 1 : 0);
function distractors(t, m, answer, pool) {
  const want = optText(m, answer), seen = new Set([want]);
  let others = shuffle(pool.filter(o => o !== answer && m.usable(o)));
  const score = new Map(others.map(o => [o, nearScore(t, answer, o)]));
  if (level === "hard") others.sort((a, b) => score.get(b) - score.get(a));          // look-alikes first
  else if (level === "easy") others.sort((a, b) => score.get(a) - score.get(b));     // very different first
  const out = [];
  for (const o of others) { const x = optText(m, o); if (!seen.has(x)) { seen.add(x); out.push(o); if (out.length === CHOICES - 1) break; } }
  return out;
}
function newRound() {
  const t = topic, m = t.modes.find(x => x.id === mode);
  let pool = t.items.filter(m.usable);
  if (level === "easy") { const easy = pool.filter(x => x.easy); if (easy.length >= CHOICES * 3) pool = easy; }
  const picked = shuffle(pool).slice(0, ROUND_LENGTH);
  state = { i: 0, score: 0, answered: 0, missed: [],
            questions: picked.map(it => ({ ...m.make(it), answer: it, mode: m,
              options: shuffle([it, ...distractors(t, m, it, pool)]) })) };
  renderQuestion();
}

// ---- views ----
function renderHome() {
  view = "home"; topic = null; stopClips();
  app.innerHTML = `<div class="center"><div class="hero">🐦</div><h1>Bird Quiz</h1>
    <p>Pick a quiz.</p>
    <div class="topicgrid">${Object.values(TOPICS).map(t => `<button class="topiccard" data-t="${t.id}">
      <span class="emo">${t.emoji}</span><b>${esc(t.title)}</b><small>${esc(t.blurb)}</small></button>`).join("")}</div></div>`;
  app.querySelectorAll(".topiccard").forEach(b => b.onclick = () => openTopic(TOPICS[b.dataset.t]));
}

async function openTopic(t) {
  app.innerHTML = `<div class="center"><p class="sci">Loading…</p></div>`;
  try { await loadTopic(t); } catch { app.innerHTML = `<div class="center"><p>Couldn't load ${esc(t.title)}. Are you online?</p>
    <button class="btn ghost" id="home">Home</button></div>`; document.getElementById("home").onclick = renderHome; return; }
  topic = t;
  if (!t.modes.some(m => m.id === mode && m.usableCount(t.items))) mode = t.modes.find(m => m.usableCount(t.items)).id;
  renderTopic();
}

function renderTopic() {
  view = "topic"; const t = topic, avail = t.modes.filter(m => m.usableCount(t.items));
  const m = t.modes.find(x => x.id === mode);
  app.innerHTML = `<button class="btn ghost back" id="back">‹ All quizzes</button>
    <div class="center"><div class="hero">${t.emoji}</div><h1>${esc(t.title)}</h1>
    <p>${esc(m.intro)}</p>
    ${avail.length > 1 ? `<div class="seg">${avail.map(x => `<button data-mode="${x.id}" class="${x.id === mode ? "on" : ""}">${x.label}</button>`).join("")}</div>` : ""}
    <p class="sci">${esc(t.countLabel ? t.countLabel(t.items) : t.items.length + " items")}</p>
    ${LEVELS.map(k => `<button class="btn level" data-level="${k}">${LEVEL_LABEL[k]}<small>${esc(t.levels[k])}</small></button>`).join("")}</div>`;
  document.getElementById("back").onclick = renderHome;
  app.querySelectorAll(".seg button").forEach(b => b.onclick = () => { mode = b.dataset.mode; renderTopic(); });
  app.querySelectorAll(".level").forEach(b => b.onclick = () => { level = b.dataset.level; newRound(); });
}

const photoHTML = (p, alt = "Photo") => `<div class="photowrap">
  <img class="backdrop" alt="" src="${esc(p.file)}"><img class="photo" alt="${esc(alt)}" src="${esc(p.file)}"></div>`;

function renderQuestion() {
  view = "question";
  const q = state.questions[state.i];
  app.innerHTML = `
    <div class="top"><button class="quit" id="quit">✕ End quiz</button><span>${LEVEL_LABEL[level]} · ${state.i + 1} of ${state.questions.length}</span><span>Score ${state.score}</span></div>
    <div class="bar"><i style="width:${state.i / state.questions.length * 100}%"></i></div>
    <div id="pic">${q.promptHTML}</div>
    <div class="choices">${q.options.map((o, k) =>
      `<button class="choice" data-k="${k}">${esc(optText(q.mode, o))}</button>`).join("")}</div>
    <div id="after"></div>`;
  app.querySelectorAll(".choice").forEach(b => b.onclick = () => answer(q, +b.dataset.k));
  document.getElementById("quit").onclick = () => {
    if (!confirm(state.answered ? "End this quiz and see your results so far?" : "End this quiz?")) return;
    stopClips(); state.answered ? renderResults() : renderHome();
  };
  wirePlayer();
}

// ---- sound player (used by sound questions) ----
const playerHTML = (file, hint) => `<div class="player"><audio id="clip" src="${esc(file)}" preload="auto"></audio>
  <button id="play" aria-label="Play">▶</button><p>${esc(hint)}</p></div>`;
function wirePlayer() {
  const clip = document.getElementById("clip"), btn = document.getElementById("play");
  if (!clip) return;
  btn.onclick = () => clip.paused ? clip.play() : clip.pause();
  clip.onplay = () => btn.textContent = "⏸"; clip.onpause = clip.onended = () => btn.textContent = "▶";
}
const stopClips = () => document.querySelectorAll("audio").forEach(a => a.pause());

const flagButton = q => q.flagFile ? `<button class="flagbtn" id="flag" title="Flag this photo">🚩 Flag photo</button>` : "";
function wireFlag(q) {
  const btn = document.getElementById("flag"); if (!btn || !q.flagFile) return;
  btn.onclick = () => {
    const reason = prompt("What's wrong with this photo? (bad crop, wrong subject, blurry, …)", "");
    if (reason === null) return;
    setFlag(q.flagFile, reason.trim());
    btn.textContent = "🚩 Flagged — won't show again"; btn.disabled = true;
  };
}

function answer(q, k) {
  const right = q.options[k] === q.answer, m = q.mode, t = topic;
  state.answered++;
  if (right) state.score++; else state.missed.push({ q, chosen: q.options[k] });
  app.querySelectorAll(".choice").forEach((b, j) => {
    b.disabled = true;
    if (q.options[j] === q.answer) b.classList.add("good");
    else if (j === k) b.classList.add("bad");
  });
  const pic = document.getElementById("pic");
  if (q.revealHTML) { pic.querySelector(".player")?.classList.add("mini"); pic.insertAdjacentHTML("beforeend", q.revealHTML); }
  const host = pic.querySelector(".photowrap") || pic;
  host.insertAdjacentHTML("beforeend", `<button class="infobtn" id="info" aria-label="More info">i</button>`);
  document.getElementById("info").onclick = () => openInfo(t, q.answer);
  const last = state.i === state.questions.length - 1;
  document.getElementById("after").innerHTML = `
    <p class="credit">${right ? "✅ Correct!" : "❌ It was"} <b>${esc(optText(m, q.answer))}</b>
      ${m.note ? m.note(q.answer) : ""}<br>${q.creditHTML || ""}${flagButton(q) ? " · " + flagButton(q) : ""}</p>
    <button class="btn" id="next">${last ? "See results" : "Next"}</button>`;
  wireFlag(q);
  document.getElementById("next").onclick = () => { stopClips(); state.i++; last ? renderResults() : renderQuestion(); };
}

// ---- info sheet ----
function openInfo(t, item) {
  const sheet = document.createElement("div");
  sheet.className = "sheet";
  sheet.innerHTML = `<div class="sheetbody"><div class="grab"></div><button class="close" aria-label="Close">✕</button>${t.infoHTML(item)}</div>`;
  sheet.onclick = e => { if (e.target === sheet || e.target.closest(".close")) { stopClips(); sheet.remove(); } };
  document.body.appendChild(sheet);
  swipeToClose(sheet);
}

// Drag a sheet down to dismiss it (only when it's scrolled to the top).
function swipeToClose(sheet) {
  const body = sheet.querySelector(".sheetbody"); let y0 = null, dy = 0;
  body.addEventListener("touchstart", e => { y0 = body.scrollTop <= 0 ? e.touches[0].clientY : null; dy = 0; body.style.transition = "none"; }, { passive: true });
  body.addEventListener("touchmove", e => {
    if (y0 === null) return; dy = e.touches[0].clientY - y0;
    if (dy > 0) body.style.transform = `translateY(${dy}px)`; else { dy = 0; body.style.transform = ""; }
  }, { passive: true });
  body.addEventListener("touchend", () => {
    body.style.transition = "transform .2s";
    if (dy > 100) { body.style.transform = "translateY(100%)"; setTimeout(() => sheet.remove(), 180); }
    else body.style.transform = "";
    y0 = null;
  });
}

// ---- results & review ----
function renderResults() {
  view = "results";
  const miss = state.missed.length ? `<div class="miss"><b>Review — tap one:</b>${
    state.missed.map((x, k) => `<button class="missrow" data-k="${k}">${esc(x.q.mode.missLabel ? x.q.mode.missLabel(x.q.answer) : optText(x.q.mode, x.q.answer))} <span>›</span></button>`).join("")}</div>` : "";
  const ratio = state.answered ? state.score / state.answered : 0;
  app.innerHTML = `<div class="center"><div class="score">${state.score}/${state.answered}</div>
    <p>${ratio >= .9 ? topic.praise[0] : ratio >= .6 ? topic.praise[1] : topic.praise[2]}</p>
    ${miss}<button class="btn" id="again">Play again</button>
    <button class="btn ghost" id="settings">Change difficulty</button>
    <button class="btn ghost" id="home">All quizzes</button></div>`;
  app.querySelectorAll(".missrow").forEach(b => b.onclick = () => renderReview(+b.dataset.k));
  document.getElementById("again").onclick = newRound;
  document.getElementById("settings").onclick = renderTopic;
  document.getElementById("home").onclick = renderHome;
}

function renderReview(k) {
  view = "review";
  const { q, chosen } = state.missed[k], m = q.mode;
  app.innerHTML = `<button class="btn ghost back" id="back">‹ Back to results</button>
    <div id="pic">${q.promptHTML}${q.revealHTML || ""}</div>
    <p class="credit">You picked <b>${esc(optText(m, chosen))}</b> · answer: <b>${esc(optText(m, q.answer))}</b><br>
      ${q.creditHTML || ""}${flagButton(q) ? " · " + flagButton(q) : ""}</p>
    <div class="review">${topic.infoHTML(q.answer)}</div>`;
  wireFlag(q); wirePlayer();
  document.getElementById("back").onclick = () => { stopClips(); renderResults(); window.scrollTo(0, 0); };
  window.scrollTo(0, 0);
}

// ---- general bug report (button at the bottom of every screen) ----
function bugContext() {
  const q = state && state.questions && state.questions[state.i], inQ = q && view === "question";
  return [`screen=${view}`, topic ? `topic=${topic.id}` : "", mode ? `mode=${mode}` : "", `level=${level}`,
          inQ ? `question=${state.i + 1}/${state.questions.length}` : "", inQ && q.answer ? `item=${q.answer.id}` : "",
          inQ && q.flagFile ? `photo=${q.flagFile}` : "", `size=${innerWidth}x${innerHeight}`].filter(Boolean).join(" ");
}
function openBugReport() {
  const sheet = document.createElement("div");
  sheet.className = "sheet";
  sheet.innerHTML = `<div class="sheetbody"><div class="grab"></div><button class="close" aria-label="Close">✕</button>
    <h2>Report a bug</h2><p class="credit">What went wrong? We'll note which screen you were on automatically.</p>
    <textarea id="bugtext" rows="5" placeholder="What happened, and what did you expect?"></textarea>
    <p id="bugmsg" class="credit"></p><button class="btn" id="bugsend">Send report</button></div>`;
  sheet.onclick = e => { if (e.target === sheet || e.target.closest(".close")) sheet.remove(); };
  document.body.appendChild(sheet); swipeToClose(sheet);
  const text = sheet.querySelector("#bugtext"), msg = sheet.querySelector("#bugmsg"), send = sheet.querySelector("#bugsend");
  text.focus();
  send.onclick = async () => {
    if (text.value.trim().length < 3) { msg.textContent = "Please describe the problem first."; return; }
    send.disabled = true; msg.textContent = "Sending…";
    try {
      const r = await fetch(REPORT_URL, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.value, context: bugContext(), pageUrl: location.href, userAgent: navigator.userAgent }) });
      if (!r.ok) throw new Error(r.status);
      sheet.querySelector(".sheetbody").innerHTML = `<button class="close" aria-label="Close">✕</button>
        <h2>Thanks! 🐞</h2><p>Your report was sent.</p>`;
      setTimeout(() => sheet.remove(), 1800);
    } catch { send.disabled = false; msg.textContent = "Couldn't send (are you online?). Your text is still here — try again."; }
  };
}
// keep a small "Report a bug" link at the end of whatever screen is showing
new MutationObserver(() => {
  if (app.lastElementChild && app.lastElementChild.id === "bugfoot") return;
  const f = document.createElement("p"); f.id = "bugfoot"; f.className = "bugfoot";
  f.innerHTML = `<button>🐞 Report a bug</button>`; f.firstChild.onclick = openBugReport; app.appendChild(f);
}).observe(app, { childList: true });

window.addEventListener("load", () => { renderHome(); retryFlags(); });   // topics.js has registered by now
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
