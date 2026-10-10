// Topic definitions for the quiz engine in app.js. A topic provides:
//   id, title, emoji, blurb, dataUrl, setup(items)?, levels{easy,medium,hard}, praise[3], countLabel(items),
//   near(a, b)? (how alike two items are, for Easy/Hard distractors), infoHTML(item),
//   modes[]: { id, label, intro, usable(item), make(item) -> {promptHTML, revealHTML?, creditHTML, flagFile?},
//              optionText?(item), note?(item), missLabel?(item) }
const mkMode = o => ({ ...o, usableCount: items => items.filter(o.usable).length >= 8 });
const credit = (label, c) => `${label}: ${esc(c.author)}, ${esc(c.license)} — ${link(c.source, "source")}`;
const fmtNum = n => n.toLocaleString("en-US");

// =============================== BIRDS ===============================
registerTopic({
  id: "birds", title: "Birds", emoji: "🐦", blurb: "Photos & songs of North American birds",
  dataUrl: "birds.json",
  setup(items) { items.forEach(b => { b.group = b.family; }); },
  countLabel: items => `${items.length} North American species`,
  levels: { easy: "Familiar birds, very different choices", medium: "All species, random choices",
            hard: "Look-alike choices from the same family" },
  praise: ["Expert birder! 🦅", "Nice eye!", "Keep practicing 🌱"],
  modes: [
    mkMode({ id: "photo", label: "📷 Photos", intro: "Name the bird from its photo.",
      usable: b => goodPhotos(b).length > 0,
      note: b => `<span class="sci">(${esc(b.scientific)})</span>`,
      make(b) { const p = pick(goodPhotos(b));
        return { promptHTML: photoHTML(p, "Bird to identify"), creditHTML: credit("Photo", p), flagFile: p.file }; } }),
    mkMode({ id: "song", label: "🔊 Sounds", intro: "Name the bird from its call or song.",
      usable: b => (b.sounds || []).length > 0 && goodPhotos(b).length > 0,
      note: b => `<span class="sci">(${esc(b.scientific)})</span>`,
      make(b) { const s = pick(b.sounds), p = pick(goodPhotos(b));
        return { promptHTML: playerHTML(s.file, "Listen, then pick the bird"), revealHTML: photoHTML(p, "The bird"),
                 creditHTML: credit("Sound", s) + "<br>" + credit("Photo", p), flagFile: p.file }; } }),
  ],
  infoHTML(b) {
    const i = b.info || {}, m = i.map;
    const sec = (t, x) => x ? `<h3>${t}</h3><p>${esc(x)}</p>` : "";
    const sexTag = p => p.sex ? (p.sex === "male" ? "♂ Male · " : "♀ Female · ") : "";
    return `<h2>${esc(b.name)}</h2><p class="sci">${esc(b.scientific)} · ${esc(b.family)}
        ${i.status ? `<span class="chip">${esc(i.status)}</span>` : ""}</p>
      ${sec("About", i.about)}${sec("Diet", i.diet)}${sec("Habitat & range", i.habitat)}
      ${goodPhotos(b).length ? `<h3>Photos</h3><div class="gallery">${goodPhotos(b).map(p => `<figure><img loading="lazy" alt="${esc(b.name)}" src="${esc(p.file)}">
        <figcaption>${sexTag(p)}${esc(p.author)}, ${esc(p.license)} — ${link(p.source, "source")}</figcaption></figure>`).join("")}</div>` : ""}
      ${m ? `<h3>Range map</h3><img class="map" alt="Range map of ${esc(b.name)}" src="${esc(m.file)}">
        <p class="credit">Map: ${esc(m.author)}, ${esc(m.license)} — ${link(m.source, "source")}</p>
        <p class="credit mapkey">${/cephas|jebbles/i.test(m.author)
          ? `Key: <i style="background:#ff7f2a"></i>breeding <i style="background:#ffdd55"></i>migration <i style="background:#7137c8"></i>year-round <i style="background:#5f8dd3"></i>winter (non-breeding)`
          : "This map uses its own colors — see the source link for its legend."}</p>` : ""}
      ${(b.sounds || []).length ? `<h3>Sounds</h3>${b.sounds.map(x => `<div class="snd"><b>${x.kind === "song" ? "Song" : "Call"}</b>
        <audio controls preload="none" src="${esc(x.file)}"></audio>
        <p class="credit">${esc(x.author)}, ${esc(x.license)} — ${link(x.source, "xeno-canto")}</p></div>`).join("")}` : ""}
      ${i.wiki ? `<p class="credit">Text from ${link(i.wiki, "Wikipedia")} (CC BY-SA 4.0).</p>` : ""}`;
  },
});

// ============================= COUNTRIES =============================
let WORLD = {}, WORLD_PATHS = "";
const K = 1000 / (2 * Math.PI);
const mx = lon => lon * Math.PI / 180 * K;
const my = lat => -1.25 * Math.log(Math.tan(Math.PI / 4 + 0.4 * Math.max(-58, Math.min(84, lat)) * Math.PI / 180)) * K;
const win = (lo0, la0, lo1, la1) => [mx(lo0), my(la1), mx(lo1), my(la0)];        // lon/lat box -> map box
const WINDOWS = { "Europe": win(-25, 34, 45, 72), "Asia": win(25, -12, 150, 60), "Africa": win(-20, -37, 55, 38),
  "North America": win(-170, 5, -50, 72), "South America": win(-85, -57, -32, 14), "Oceania": win(105, -50, 180, 10) };
const WORLD_WIN = win(-180, -58, 180, 84);

function viewBoxFor(it, wide) {
  const b = WORLD[it.id].bbox, cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2, bw = b[2] - b[0], bh = b[3] - b[1];
  let w = wide ? WORLD_WIN : (WINDOWS[it.region] || WORLD_WIN);
  const inside = cx > w[0] && cx < w[2] && cy > w[1] && cy < w[3];
  if (!wide && bw > (w[2] - w[0]) * 0.6) { const p = Math.max(bw, bh) * 0.4; w = [b[0] - p, b[1] - p, b[2] + p, b[3] + p]; }
  else if (!wide && !inside) w = WORLD_WIN;
  let [x0, y0, x1, y1] = w, vw = x1 - x0, vh = y1 - y0;
  if (vw / vh < 4 / 3) { const nw = vh * 4 / 3; x0 -= (nw - vw) / 2; vw = nw; } else { const nh = vw * 3 / 4; y0 -= (nh - vh) / 2; vh = nh; }
  return { x: x0, y: y0, w: vw, h: vh, tiny: Math.max(bw, bh) < vw * 0.05, cx, cy };
}
function mapHTML(it, wide) {
  const v = viewBoxFor(it, wide);
  return `<div class="mapbox"><svg viewBox="${v.x.toFixed(1)} ${v.y.toFixed(1)} ${v.w.toFixed(1)} ${v.h.toFixed(1)}" role="img" aria-label="World map with one country highlighted">
    <g class="land">${WORLD_PATHS}</g><path class="hl" d="${WORLD[it.id].d}"/>
    ${v.tiny ? `<circle class="ring" cx="${v.cx.toFixed(1)}" cy="${v.cy.toFixed(1)}" r="${(v.w * 0.028).toFixed(1)}"/>` : ""}</svg></div>`;
}
const flagBox = src => `<div class="flagbox"><img alt="Flag" src="${esc(src)}"></div>`;
const qText = (html, flag) => `<div class="qtext">${flag ? `<img class="miniflag" alt="" src="${esc(flag)}">` : ""}<p>${html}</p></div>`;

registerTopic({
  id: "countries", title: "Countries", emoji: "🌍", blurb: "Flags, maps & capitals of 195 countries",
  dataUrl: "topics/countries/data.json",
  async setup(items) {
    WORLD = await (await fetch("topics/countries/world.json")).json();
    WORLD_PATHS = items.filter(c => WORLD[c.id]).map(c => `<path d="${WORLD[c.id].d}"/>`).join("");
  },
  countLabel: items => `${items.length} countries`,
  levels: { easy: "Well-known countries, very different choices", medium: "All 195 countries, random choices",
            hard: "Look-alikes and neighbours; maps show the whole world" },
  praise: ["Globetrotter! 🌍", "Well traveled!", "Keep exploring 🧭"],
  near(a, o) { return (mode === "flag" && a.look != null && a.look === o.look ? 2 : 0) + (a.group === o.group ? 1 : 0); },
  modes: [
    mkMode({ id: "flag", label: "🏳️ Flags", intro: "Which country's flag is this?", usable: () => true,
      note: c => c.capital ? `· capital: ${esc(c.capital)}` : "",
      make: c => ({ promptHTML: flagBox(c.flag), creditHTML: `Flags: ${link("https://github.com/lipis/flag-icons", "flag-icons")} (MIT)` }) }),
    mkMode({ id: "map", label: "🗺️ Maps", intro: "Name the highlighted country.", usable: c => !!WORLD[c.id],
      note: c => c.capital ? `· capital: ${esc(c.capital)}` : "",
      make: c => ({ promptHTML: mapHTML(c, level === "hard"), creditHTML: `Map: ${link("https://www.naturalearthdata.com/", "Natural Earth")} (public domain)` }) }),
    mkMode({ id: "capital", label: "🏛️ Capitals", intro: "Name the capital city.", usable: c => !!c.capital,
      optionText: c => c.capital, missLabel: c => `${c.name} → ${c.capital}`, note: c => `is the capital of ${esc(c.name)}`,
      make: c => ({ promptHTML: qText(`What is the capital of <b>${esc(c.name)}</b>?`, c.flag),
                    creditHTML: `Capitals: ${link("https://www.naturalearthdata.com/", "Natural Earth")}` }) }),
    mkMode({ id: "capital2", label: "📍 Capital → country", intro: "Which country has this capital?", usable: c => !!c.capital,
      missLabel: c => `${c.capital} → ${c.name}`, note: c => `· capital: ${esc(c.capital)}`,
      make: c => ({ promptHTML: qText(`<b>${esc(c.capital)}</b> is the capital of which country?`),
                    creditHTML: `Capitals: ${link("https://www.naturalearthdata.com/", "Natural Earth")}` }) }),
  ],
  infoHTML(c) {
    return `<h2>${esc(c.name)}</h2><p class="sci">${esc(c.official)}</p>
      ${flagBox(c.flag)}
      <h3>Facts</h3><p>${c.capital ? `Capital: <b>${esc(c.capital)}</b><br>` : ""}Region: ${esc(c.subregion || c.region)}<br>
      Population: ${fmtNum(c.pop)}</p>
      ${WORLD[c.id] ? `<h3>Where is it?</h3>${mapHTML(c, false)}` : ""}
      <p class="credit">Flags: ${link("https://github.com/lipis/flag-icons", "flag-icons")} (MIT). Map &amp; capitals:
      ${link("https://www.naturalearthdata.com/", "Natural Earth")} (public domain).</p>`;
  },
});

// ============================== US STATES ==============================
registerTopic({
  id: "states", title: "US States", emoji: "🇺🇸", blurb: "State flags & capitals",
  dataUrl: "topics/states/data.json",
  countLabel: items => `${items.length} states`,
  levels: { easy: "Well-known states, very different choices", medium: "All 50 states, random choices",
            hard: "Similar-looking flags and neighbouring states" },
  praise: ["Road-trip pro! 🇺🇸", "Not bad!", "Keep studying 📚"],
  near(a, o) { return (mode === "flag" && a.look != null && a.look === o.look ? 2 : 0) + (a.group === o.group ? 1 : 0); },
  modes: [
    mkMode({ id: "flag", label: "🚩 Flags", intro: "Which state's flag is this?", usable: () => true,
      note: s => `· capital: ${esc(s.capital)}`,
      make: s => ({ promptHTML: flagBox(s.flag), creditHTML: credit("Flag", s.flagCredit) }) }),
    mkMode({ id: "capital", label: "🏛️ Capitals", intro: "Name the state capital.", usable: () => true,
      optionText: s => s.capital, missLabel: s => `${s.name} → ${s.capital}`, note: s => `is the capital of ${esc(s.name)}`,
      make: s => ({ promptHTML: qText(`What is the capital of <b>${esc(s.name)}</b>?`, s.flag), creditHTML: "" }) }),
    mkMode({ id: "capital2", label: "📍 Capital → state", intro: "Which state has this capital?", usable: () => true,
      missLabel: s => `${s.capital} → ${s.name}`, note: s => `· capital: ${esc(s.capital)}`,
      make: s => ({ promptHTML: qText(`<b>${esc(s.capital)}</b> is the capital of which state?`), creditHTML: "" }) }),
  ],
  infoHTML(s) {
    return `<h2>${esc(s.name)}</h2><p class="sci">${esc(s.abbr)} · ${esc(s.region)}</p>
      ${flagBox(s.flag)}<p class="credit">${credit("Flag", s.flagCredit)}</p>
      <h3>Capital</h3><p>${esc(s.capital)}</p>`;
  },
});
