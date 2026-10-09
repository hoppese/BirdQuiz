// Bird Quiz — photo ID. Question generators live in QUIZ_TYPES so a "song"
// type can be added later without touching the rest of the flow.
const ROUND_LENGTH = 10, CHOICES = 4;
const app = document.getElementById("app");
let birds = [], state = null;

const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) {
  const j = Math.random() * (i + 1) | 0; [a[i], a[j]] = [a[j], a[i]]; } return a; };
const pick = a => a[Math.random() * a.length | 0];
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

const QUIZ_TYPES = {
  photo(answer) {
    const photo = pick(answer.photos);
    const options = shuffle([answer, ...shuffle(birds.filter(b => b !== answer)).slice(0, CHOICES - 1)]);
    return { type: "photo", answer, photo, options };
  },
  // song(answer) { ... }  // future: audio from xeno-canto
};

function newRound() {
  const answers = shuffle(birds).slice(0, ROUND_LENGTH);
  state = { i: 0, score: 0, missed: [], questions: answers.map(QUIZ_TYPES.photo) };
  renderQuestion();
}

function renderHome() {
  app.innerHTML = `<div class="center"><div class="hero">🐦</div><h1>Bird Quiz</h1>
    <p>Name the bird from its photo.</p><p class="sci">${birds.length} species</p>
    <button class="btn" id="start">Start a round</button></div>`;
  document.getElementById("start").onclick = newRound;
}

function renderQuestion() {
  const q = state.questions[state.i];
  app.innerHTML = `
    <div class="top"><span>Question ${state.i + 1} of ${ROUND_LENGTH}</span><span>Score ${state.score}</span></div>
    <div class="bar"><i style="width:${state.i / ROUND_LENGTH * 100}%"></i></div>
    <img class="photo" alt="Bird to identify" src="${esc(q.photo.file)}">
    <div class="choices">${q.options.map((o, k) =>
      `<button class="choice" data-k="${k}">${esc(o.name)}</button>`).join("")}</div>
    <div id="after"></div>`;
  app.querySelectorAll(".choice").forEach(b => b.onclick = () => answer(q, +b.dataset.k));
}

function answer(q, k) {
  const right = q.options[k] === q.answer;
  if (right) state.score++; else state.missed.push(q.answer);
  app.querySelectorAll(".choice").forEach((b, j) => {
    b.disabled = true;
    if (q.options[j] === q.answer) b.classList.add("good");
    else if (j === k) b.classList.add("bad");
  });
  const last = state.i === ROUND_LENGTH - 1;
  document.getElementById("after").innerHTML = `
    <p class="credit">${right ? "✅ Correct!" : "❌ It was the"} <b>${esc(q.answer.name)}</b>
      <span class="sci">(${esc(q.answer.scientific)})</span><br>
      Photo: ${esc(q.photo.author)}, ${esc(q.photo.license)} —
      <a href="${esc(q.photo.source)}" target="_blank" rel="noopener">source</a></p>
    <button class="btn" id="next">${last ? "See results" : "Next"}</button>`;
  document.getElementById("next").onclick = () => { state.i++; last ? renderResults() : renderQuestion(); };
}

function renderResults() {
  const miss = state.missed.length ? `<div class="miss"><b>Review:</b><br>${
    state.missed.map(b => `${esc(b.name)}`).join("<br>")}</div>` : "";
  app.innerHTML = `<div class="center"><div class="score">${state.score}/${ROUND_LENGTH}</div>
    <p>${state.score >= 9 ? "Expert birder! 🦅" : state.score >= 6 ? "Nice eye!" : "Keep practicing 🌱"}</p>
    ${miss}<button class="btn" id="again">Play again</button>
    <button class="btn ghost" id="home">Home</button></div>`;
  document.getElementById("again").onclick = newRound;
  document.getElementById("home").onclick = renderHome;
}

fetch("birds.json").then(r => r.json()).then(d => { birds = d; renderHome(); })
  .catch(() => app.innerHTML = "<p>Couldn't load bird data.</p>");

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
