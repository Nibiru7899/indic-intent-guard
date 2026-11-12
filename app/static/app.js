const $ = (id) => document.getElementById(id);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const pace = (ms) => (reduced ? 0 : ms);
const inr = (n) => (n == null ? "—" : Number(n).toLocaleString("en-IN"));
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let session = null;
let samples = [];
let ledgerSeen = 0;

/* ---------------- microtext rules ---------------- */
document.querySelectorAll(".microtext").forEach((el) => {
  el.textContent = "INDICINTENTGUARD · SPEECH TO ACTION VERIFIED · PRISMA · TIMBRE · ".repeat(40);
});

/* ---------------- route diagram ---------------- */
const SEGS = ["prisma", "evidence", "decision", "bank", "timbre", "back", "human"];
const STATIONS = ["caller", "prisma", "evidence", "decision", "timbre", "human", "bank"];
const seg = (n) => $("seg-" + n);
// A station's state shows on the map and on the compact phone steps at once.
const st = (n) => {
  const g = $("st-" + n), li = document.querySelector(`.route__steps [data-st="${n}"]`);
  return { classList: {
    add: (...c) => { g.classList.add(...c); li.classList.add(...c); },
    remove: (...c) => { g.classList.remove(...c); li.classList.remove(...c); },
    replace: (a, b) => { g.classList.replace(a, b); li.classList.replace(a, b); },
  } };
};

function routeReset() {
  SEGS.forEach((n) => seg(n).classList.remove("on", "wait"));
  STATIONS.forEach((n) => st(n).classList.remove("on", "live"));
}
function routeSending() {
  routeReset();
  st("caller").classList.add("on");
  seg("prisma").classList.add("wait");
  st("prisma").classList.add("live");
}
async function routeDecided(decision) {
  seg("prisma").classList.remove("wait");
  seg("prisma").classList.add("on");
  st("prisma").classList.replace("live", "on");
  await wait(pace(260));
  seg("evidence").classList.add("on"); st("evidence").classList.add("on");
  await wait(pace(260));
  seg("decision").classList.add("on"); st("decision").classList.add("on");
  await wait(pace(300));
  if (decision === "accept") { seg("bank").classList.add("on"); await wait(pace(400)); st("bank").classList.add("on"); }
  if (decision === "clarify") { seg("timbre").classList.add("on"); await wait(pace(300)); st("timbre").classList.add("live"); }
  if (decision === "escalate") { seg("human").classList.add("on"); await wait(pace(300)); st("human").classList.add("on"); }
}
async function routeConfirmed() {
  st("timbre").classList.replace("live", "on");
  seg("back").classList.add("on");
  await wait(pace(500));
  seg("bank").classList.add("on");
  await wait(pace(400));
  st("bank").classList.add("on");
}

/* ---------------- the guilloché seal ---------------- */
// Hypotrochoid / epitrochoid curves: the same family security printers engrave.
function trochoid(R, r, d, { epi = false, rot = 0 } = {}) {
  const gcd = (a, b) => (b ? gcd(b, a % b) : a);
  const turns = r / gcd(R, r);
  const n = Math.round(turns * 160);
  let p = "";
  for (let i = 0; i <= n; i++) {
    const t = (i / n) * turns * 2 * Math.PI;
    const k = epi ? (R + r) / r : (R - r) / r;
    let x = epi ? (R + r) * Math.cos(t) - d * Math.cos(k * t) : (R - r) * Math.cos(t) + d * Math.cos(k * t);
    let y = epi ? (R + r) * Math.sin(t) - d * Math.sin(k * t) : (R - r) * Math.sin(t) - d * Math.sin(k * t);
    const c = Math.cos(rot), s = Math.sin(rot);
    [x, y] = [x * c - y * s, x * s + y * c];
    p += (i ? "L" : "M") + x.toFixed(2) + " " + y.toFixed(2);
  }
  return p;
}
const SEAL_PATHS = [
  trochoid(72, 20, 30),
  trochoid(63, 14, 26, { rot: 0.2 }),
  trochoid(48, 9, 22, { rot: 0.5 }),
  trochoid(80, 3, 5, { epi: true }),
];
// Two copies: a faint unengraved plate, and the inked engraving revealed by an angular sweep.
function sealSVG() {
  const art = `<path class="seal__ring" d="M0 -94 A94 94 0 1 1 -0.01 -94"/>${SEAL_PATHS.map((d) => `<path d="${d}"/>`).join("")}`;
  return `<div class="seal-wrap" aria-hidden="true"><div class="seal-stack">
      <svg class="seal__ghost" viewBox="-100 -100 200 200">${art}</svg>
      <svg class="seal__ink" viewBox="-100 -100 200 200">${art}</svg>
    </div><span class="seal__label"></span></div>`;
}
function setSeal(state, label) {
  const s = $("note-b3").querySelector(".seal-wrap");
  if (!s) return;
  s.dataset.state = state;
  s.querySelector(".seal__label").textContent = label;
}

/* ---------------- note panels ---------------- */
function noteHTML(action, { guard = false, superseded } = {}) {
  const line = action
    ? `<b>${esc(cap(action.intent.replace("_", " ")))}</b> · ${action.account_id ? "account …" + esc(action.account_id) : "account not stated"}` +
      (guard && superseded?.amount != null ? ` · <s>₹${inr(superseded.amount)}</s> retracted` : "")
    : "&nbsp;";
  return `
    <div class="note__band"><span class="band__t">${action ? "" : "Waiting for a request"}</span><small class="band__s"></small></div>
    <div class="note__body">
      <div>
        <span class="note__k">Amount</span>
        <div class="figure"><span class="cur">₹</span><span class="reg"><span class="digits"></span><span class="reg__ghost" aria-hidden="true"></span></span></div>
        <p class="note__words">${action?.words ? esc(action.words) + " rupees" : action ? "amount not heard" : "&nbsp;"}</p>
      </div>
      ${guard ? sealSVG() : ""}
      <p class="note__line">${line}</p>
      <ul class="note__signs"></ul>
    </div>`;
}

function setDigits(el, text) {
  el.innerHTML = [...text].map((c) => `<span${c === "," ? ' class="sep"' : ""}>${c === " " ? "&nbsp;" : esc(c)}</span>`).join("");
}
async function flipDigits(el, from, to) {
  const n = Math.max(from.length, to.length);
  const a = from.padStart(n, " "), b = to.padStart(n, " ");
  setDigits(el, a);
  const spans = [...el.children];
  for (let i = 0; i < n; i++) {
    if (a[i] === b[i]) continue;
    const s = spans[i];
    s.classList.add("flip");
    setTimeout(() => { s.innerHTML = b[i] === " " ? "&nbsp;" : esc(b[i]); }, pace(170));
    await wait(pace(90));
  }
  await wait(pace(300));
  setDigits(el, to);
}

function band(note, kind, title, small) {
  const b = note.querySelector(".note__band");
  b.className = `note__band band--${kind}`;
  b.querySelector(".band__t").textContent = title;
  b.querySelector(".band__s").textContent = small || "";
  void b.offsetWidth;
  b.classList.add("land");
}

function blankNotes() {
  for (const id of ["note-b0", "note-b3"]) {
    const n = $(id);
    n.dataset.state = "blank";
    n.innerHTML = noteHTML(null, { guard: id === "note-b3" });
    setDigits(n.querySelector(".digits"), "—");
  }
}

const DECISION_INK = { accept: "var(--green)", clarify: "var(--ochre-ink)", escalate: "var(--violet)" };
function signsHTML(items, color, title) {
  if (!items.length) return "";
  return `<li class="note__signs-title" style="opacity:1;animation:none">${title}</li>` + items.map((it, i) => {
    // Dot size means evidence weight; hypotheticals get one small uniform mark.
    const size = it.hyp ? 8 : Math.round(Math.min(24, Math.max(10, 6 + 6 * it.w)));
    return `<li style="animation-delay:${pace(900 + 110 * i)}ms"><span class="dot" style="width:${size}px;height:${size}px;--sign:${color}"></span>
      <span class="${it.hyp ? "hyp" : ""}">${esc(it.text)}</span></li>`;
  }).join("");
}

const sameAction = (a, b) => (a?.amount ?? null) === (b?.amount ?? null) && (a?.account_id ?? null) === (b?.account_id ?? null);

async function renderNotes(r) {
  const b0 = r.policies.B0_direct.action, g = r.guard;
  const N0 = $("note-b0"), N3 = $("note-b3");
  $("confirmHome").appendChild($("confirm"));  // lift the slip out before the note is rebuilt
  N0.dataset.state = N3.dataset.state = "filled";
  N0.innerHTML = noteHTML(b0);
  N3.innerHTML = noteHTML(g.action, { guard: true, superseded: r.superseded });
  const d0 = N0.querySelector(".digits"), d3 = N3.querySelector(".digits");
  const s0 = b0?.amount != null ? inr(b0.amount) : "—";
  const s3 = g.action?.amount != null ? inr(g.action.amount) : "—";
  setDigits(d0, s0);
  N0.querySelector(".reg").classList.add("in-register");

  // B0 commits immediately.
  const retracted = r.superseded?.amount != null && b0?.amount === r.superseded.amount;
  const b0Wrong = b0 && !(sameAction(b0, g.action) && g.decision === "accept");
  N0.dataset.verdict = b0Wrong ? "wrong" : "ok";
  if (!b0) band(N0, "void", "Nothing to execute");
  else if (!b0Wrong) band(N0, "ok", "Executes");
  else band(N0, "wrong", "Executes", retracted ? "the amount the caller retracted" : "without any check");

  // What the naive agent's choice would do, stated as a hypothetical next to the guard's proof.
  if (b0Wrong && b0.amount != null) {
    const conseq = [
      { hyp: true, text: `Debits ₹${inr(b0.amount)} at once; balance would fall to ₹${inr(lastBalance - b0.amount)}` },
      { hyp: true, text: "No question is put to the caller" },
    ];
    if (retracted && g.action?.amount != null) conseq.splice(1, 0, { hyp: true, text: `The caller took back ₹${inr(b0.amount)} and said ₹${inr(g.action.amount)}` });
    N0.querySelector(".note__signs").innerHTML = signsHTML(conseq, "var(--oxide)", "If this executes");
  }
  const flags = checks(r).filter((c) => c.on).slice(0, 3).map((c) => ({ w: c.w, text: c.flag }));
  N3.querySelector(".note__signs").innerHTML = signsHTML(flags, DECISION_INK[g.decision], "Why the guard stopped");

  // The guard's panel starts from what the naive agent read, then flips to what it keeps.
  N3.querySelector(".reg__ghost").textContent = s3;
  await wait(pace(650));
  if (s0 !== s3 && s0 !== "—" && s3 !== "—") await flipDigits(d3, s0, s3);
  else setDigits(d3, s3);

  // See-through register: words and figures agree -> the halves align.
  await wait(pace(120));
  N3.querySelector(".reg").classList.add(r.features.itn_literal_mismatch ? "off-register" : "in-register");
  await wait(pace(250));
  guardState(g.decision, g.fields);
}

function guardState(decision, fields = []) {
  const N3 = $("note-b3");
  if (decision === "accept") { band(N3, "ok", "Cleared", "every check passed"); setSeal("ok", "VERIFIED"); }
  if (decision === "clarify") { band(N3, "ask", "Asks the caller first", "checking " + (fields.join(" + ") || "amount")); setSeal("ask", "ASK FIRST"); }
  if (decision === "escalate") { band(N3, "refer", "Referred to a person", "outside the account rules"); setSeal("refer", "REFER"); }
}

/* ---------------- security features checked ---------------- */
function checks(r) {
  const f = r.features, w = r.weights, a = r.guard.action || {}, sup = r.superseded || {}, st = r.audio_stats || {};
  const flagged = (...ks) => ks.filter((k) => f[k]);
  const weight = (ks) => Math.max(0, ...ks.map((k) => w[k] ?? 1));
  const rows = [
    { t: "Self-correction", ks: flagged("correction_resolved", "multiple_unresolved", "negated_only"),
      flag: f.multiple_unresolved ? "Two amounts and no clear correction." : f.negated_only ? "The only amount was negated."
        : sup.amount != null ? `₹${inr(sup.amount)} was retracted; ₹${inr(a.amount)} is the final amount.` : "An earlier value was retracted.",
      ok: "No retracted or competing values." },
    { t: "Words vs figures", ks: flagged("itn_literal_mismatch"),
      flag: "Prisma's literal words and its digits disagree.",
      ok: r.literal ? "Prisma's literal words and digits agree." : "Only one form returned." },
    { t: "Teen / ty", ks: flagged("confusable_amount", "confusable_x_degraded"),
      flag: f.confusable_x_degraded ? "A thirteen-or-thirty amount on degraded audio." : "Thirteen and thirty sound alike on a phone line.",
      ok: "No easily confused number words." },
    { t: "Complete sentence", ks: flagged("truncated", "low_word_rate"),
      flag: f.truncated ? "The transcript ends mid-word." : "Fewer words than the audio holds.",
      ok: "The request reads as complete." },
    { t: "Line quality", ks: flagged("narrowband", "low_snr"),
      flag: [f.narrowband && "telephone-band audio", f.low_snr && `noisy, SNR ≈ ${st.snr_db} dB`].filter(Boolean).join(", "),
      ok: `Clear audio, SNR ≈ ${st.snr_db ?? "?"} dB.` },
    { t: "Amount stated", ks: flagged("missing_field"), flag: "No amount was heard.", ok: "The amount is present." },
    { t: "Account rules", ks: flagged("context_violation"),
      flag: cap(r.guard.reasons.find((x) => /limit|not one of/.test(x)) || "Outside the account rules."),
      ok: "Within the limit and the caller's accounts." },
  ];
  return rows.map((x) => ({ ...x, on: x.ks.length > 0, w: weight(x.ks) }))
    .sort((p, q) => (q.on - p.on) || (q.w - p.w));
}

function renderChecks(r) {
  $("checks").hidden = false;
  $("checkList").innerHTML = checks(r).map((c, i) => {
    const size = c.w >= 3 ? 18 : c.w >= 1.2 ? 13 : 9;
    const mark = c.on ? `<span class="dot" style="width:${size}px;height:${size}px"></span>`
      : `<span class="pass"><svg class="ic"><use href="#i-check"/></svg></span>`;
    return `<li class="${c.on ? "flag" : "ok"}" style="animation-delay:${pace(70 * i)}ms"><span class="mark">${mark}</span>
      <strong>${c.t}</strong><span class="why">${esc(c.on ? c.flag : c.ok)}</span></li>`;
  }).join("");
  const pos = (x) => Math.min(100, Math.sqrt(Math.max(0, x)) * 100) + "%";
  $("mark").style.left = "0%";
  $("thresh").style.left = pos(r.threshold);
  requestAnimationFrame(() => requestAnimationFrame(() => { $("mark").style.left = pos(r.probability); }));
  const pct = (x) => (x * 100 < 1 ? (x * 100).toFixed(1) : Math.round(x * 100)) + "%";
  $("scaleRead").innerHTML = `Chance the parsed action is wrong: <b>${pct(r.probability)}</b>. ` +
    `For a ${r.tier}-risk ${esc(r.guard.action?.intent?.replace("_", " ") || "request")}, the guard asks above <b>${pct(r.threshold)}</b>.`;
}

/* ---------------- tables ---------------- */
const NAMES = { B0_direct: "B0 · direct", "B0+parse": "B0 + correction parser", B1_always_confirm: "B1 · always confirm",
  B2_rules: "B2 · keyword rules", B3_guard: "B3 · IndicIntentGuard" };
function renderReport(r) {
  const g = r.guard.action;
  $("report").innerHTML = `<thead><tr><th>System</th><th>Decision</th><th class="num">Amount</th><th>Account</th></tr></thead><tbody>` +
    Object.entries(r.policies).map(([n, o]) => {
      const wrongExec = o.decision === "accept" && !sameAction(o.action, g);
      const label = { accept: "executes", clarify: "asks", escalate: "refers" }[o.decision];
      return `<tr class="${n === "B3_guard" ? "is-guard" : ""}"><td>${NAMES[n] || n}</td>
        <td><span class="chip chip--${wrongExec ? "wrong" : o.decision}">${label}</span></td>
        <td class="num">${o.action?.amount != null ? "₹" + inr(o.action.amount) : "—"}</td>
        <td>${o.action?.account_id ? "…" + esc(o.action.account_id) : "—"}</td></tr>`;
    }).join("") + "</tbody>";
}

let lastBalance = 0;
async function refresh() {
  const s = await (await fetch("/api/state")).json();
  lastBalance = s.balance;
  $("calls").textContent = s.ledger.calls;
  const rows = [...s.executed].reverse();
  const fresh = rows.length - ledgerSeen;
  ledgerSeen = rows.length;
  $("ledger").innerHTML = `<thead><tr><th>Time</th><th>Particulars</th><th class="num">Debit</th><th class="num">Balance</th></tr></thead><tbody>
    <tr><td>—</td><td>Opening balance</td><td class="num"></td><td class="num">₹${inr(s.opening_balance)}</td></tr>` +
    rows.map((e, i) => `<tr class="${i >= rows.length - fresh ? "new" : ""}"><td>${esc(e.time)}</td>
      <td>${esc(cap(e.intent.replace("_", " ")))}${e.account_id ? " to …" + esc(e.account_id) : ""} · ${esc(e.via)}</td>
      <td class="num">${e.amount != null ? "₹" + inr(e.amount) : ""}</td><td class="num">₹${inr(e.balance)}</td></tr>`).join("") + "</tbody>";
}

/* ---------------- what Prisma heard ---------------- */
function renderHeard(r, source) {
  $("heard").dataset.empty = "false";
  const words = (r.transcript || "(silence)").split(/(\s+)/);
  $("transcript").className = "heard__text reveal-words";
  $("transcript").innerHTML = words.map((w, i) => /\s/.test(w) ? w : `<span style="animation-delay:${pace(i * 28)}ms">${esc(w)}</span>`).join("");
  $("literal").textContent = r.literal && r.literal !== r.transcript ? r.literal : "";
  const st = r.audio_stats || {};
  $("meta").innerHTML = [
    source === "synthetic" ? '<span class="synthetic">Synthetic voice (Timbre), not a real caller</span>' : source === "live" ? "Live recording" : "Uploaded audio",
    r.cached ? "Cached result, no credits used" : `Prisma answered in ${Math.round(r.latency_ms)} ms`,
    `${st.duration ?? "?"} s · ${st.sr ?? "?"} Hz · SNR ≈ ${st.snr_db ?? "?"} dB`,
  ].map((x) => `<span>${x}</span>`).join("");
}

/* ---------------- confirmation ---------------- */
const audio = $("promptAudio");
function showConfirm(c) {
  session = c.session;
  const p = $("confirm");
  p.hidden = false;
  p.style.animation = "none"; void p.offsetWidth; p.style.animation = "";
  $("prompt").textContent = c.prompt;
  $("player").hidden = !c.audio;
  setStatus("replyStatus", "");
  if (c.audio) { audio.src = c.audio; audio.play().catch(() => {}); }
}
audio.addEventListener("play", () => $("playBtn").innerHTML = '<svg class="ic"><use href="#i-pause"/></svg>');
audio.addEventListener("pause", () => $("playBtn").innerHTML = '<svg class="ic"><use href="#i-play"/></svg>');
audio.addEventListener("timeupdate", () => { $("playFill").style.width = (audio.currentTime / (audio.duration || 1)) * 100 + "%"; });
$("playBtn").onclick = () => (audio.paused ? audio.play() : audio.pause());

async function reply({ blob, text }) {
  if (!session) return;
  const f = new FormData();
  f.append("session", session);
  if (blob) f.append("audio", blob, "reply.wav");
  if (text) f.append("text", text);
  setStatus("replyStatus", "Listening to the answer…");
  try {
    const r = await post("/api/reply", f);
    const heard = r.heard ? `Heard “${r.heard}”. ` : "";
    const N3 = $("note-b3");
    if (r.clarify) {
      if (r.action) {
        const d3 = N3.querySelector(".digits");
        await flipDigits(d3, d3.textContent.replace(/ /g, " "), inr(r.action.amount));
        N3.querySelector(".note__words").textContent = r.action.words + " rupees";
      }
      showConfirm(r.clarify);
      setStatus("replyStatus", heard + "The amount changed, so the guard asks once more.");
    } else {
      session = null;
      if (r.executed) {
        await routeConfirmed();
        band(N3, "ok", "Cleared", "confirmed by the caller");
        setSeal("ok", "VERIFIED");
        setStatus("replyStatus", heard + `Confirmed. ₹${inr(r.executed.amount)} debited in the ledger.`);
      } else if (r.status === "rejected") {
        band(N3, "void", "Cancelled", "the caller said no");
        setSeal("void", "CANCELLED");
        setStatus("replyStatus", heard + "Cancelled. Nothing was debited.");
      } else {
        await routeDecided("escalate");
        band(N3, "refer", "Referred to a person", "could not confirm");
        setSeal("refer", "REFER");
        setStatus("replyStatus", heard + (r.message || ""));
      }
      $("yes").disabled = $("no").disabled = $("replyRec").disabled = true;
    }
  } catch (e) { setStatus("replyStatus", e.message, true); }
  refresh();
}

/* ---------------- analyse ---------------- */
function setStatus(id, msg, err = false) { $(id).textContent = msg; $(id).classList.toggle("err", err); }
async function post(url, form) {
  const r = await fetch(url, { method: "POST", body: form });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || `Request failed (${r.status}).`);
  return j;
}

async function analyze({ blob, sample, source }) {
  const f = new FormData();
  if (blob) f.append("audio", blob, "input.wav");
  if (sample) f.append("sample", sample);
  f.append("language_code", $("lang").value);
  f.append("reply_lang", $("replyLang").value);
  if ($("maxAmount").value) f.append("max_amount", $("maxAmount").value);
  f.append("known_accounts", $("accounts").value);
  session = null;
  document.body.classList.add("has-result");
  $("confirm").hidden = true;
  $("yes").disabled = $("no").disabled = $("replyRec").disabled = false;
  setStatus("status", "Sending to Gnani Prisma…");
  routeSending();
  try {
    const r = await post("/api/analyze", f);
    setStatus("status", "");
    renderHeard(r, source);
    const routing = routeDecided(r.guard.decision);
    renderReport(r);
    renderChecks(r);
    await renderNotes(r);
    await routing;
    if (r.clarify) { $("note-b3").appendChild($("confirm")); showConfirm(r.clarify); }
  } catch (e) {
    routeReset();
    setStatus("status", e.message.includes("MAX_API_CALLS") ? "API call cap reached. Raise MAX_API_CALLS in .env to continue." : e.message, true);
  }
  refresh();
}

/* ---------------- recording: MediaRecorder -> 16 kHz mono WAV ---------------- */
async function toWav16k(blob) {
  const ctx = new AudioContext();
  const decoded = await ctx.decodeAudioData(await blob.arrayBuffer());
  ctx.close();
  const off = new OfflineAudioContext(1, Math.ceil(decoded.duration * 16000), 16000);
  const src = off.createBufferSource();
  src.buffer = decoded; src.connect(off.destination); src.start();
  const pcm = (await off.startRendering()).getChannelData(0);
  const out = new DataView(new ArrayBuffer(44 + pcm.length * 2));
  const w = (o, s) => [...s].forEach((c, i) => out.setUint8(o + i, c.charCodeAt(0)));
  w(0, "RIFF"); out.setUint32(4, 36 + pcm.length * 2, true); w(8, "WAVEfmt ");
  out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 1, true);
  out.setUint32(24, 16000, true); out.setUint32(28, 32000, true); out.setUint16(32, 2, true);
  out.setUint16(34, 16, true); w(36, "data"); out.setUint32(40, pcm.length * 2, true);
  pcm.forEach((v, i) => out.setInt16(44 + i * 2, Math.max(-1, Math.min(1, v)) * 0x7fff, true));
  return new Blob([out], { type: "audio/wav" });
}

function recorder(button, onDone, statusId) {
  let rec = null, chunks = [], timer = null;
  const label = button.querySelector(".btn__label"), idle = label.textContent;
  const time = button.querySelector(".rec-time");
  button.onclick = async () => {
    if (rec) { rec.stop(); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      rec = new MediaRecorder(stream); chunks = [];
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        clearInterval(timer); if (time) time.textContent = "";
        button.classList.remove("is-recording"); label.textContent = idle;
        button.querySelector("use").setAttribute("href", "#i-mic"); rec = null;
        onDone(await toWav16k(new Blob(chunks)));
      };
      rec.start();
      const t0 = Date.now();
      if (time) timer = setInterval(() => { const s = Math.floor((Date.now() - t0) / 1000); time.textContent = `0:${String(s).padStart(2, "0")}`; }, 250);
      button.classList.add("is-recording"); label.textContent = "Stop and send";
      button.querySelector("use").setAttribute("href", "#i-stop");
      if (button.id === "rec") { routeReset(); st("caller").classList.add("live"); }
    } catch (e) { setStatus(statusId, "Microphone unavailable: " + e.message, true); }
  };
}

async function loadSamples() {
  samples = await (await fetch("/api/samples")).json();
  samples.forEach((s) => $("sample").insertAdjacentHTML("beforeend",
    `<option value="${esc(s.file)}">“${esc(s.text.length > 58 ? s.text.slice(0, 56) + "…" : s.text)}”${s.synthetic ? " · synthetic" : ""}</option>`));
}

recorder($("rec"), (blob) => analyze({ blob, source: "live" }), "status");
recorder($("replyRec"), (blob) => reply({ blob }), "replyStatus");
$("file").onchange = (e) => e.target.files[0] && analyze({ blob: e.target.files[0], source: "upload" });
$("sample").onchange = (e) => {
  const s = samples.find((x) => x.file === e.target.value);
  if (s) analyze({ sample: s.file, source: s.synthetic ? "synthetic" : "upload" });
};
$("yes").onclick = () => reply({ text: "yes" });
$("no").onclick = () => reply({ text: "no" });
document.addEventListener("click", (e) => { const d = document.querySelector(".settings[open]"); if (d && !d.contains(e.target)) d.open = false; });

blankNotes();
refresh();
// ?clip=<saved file> plays a saved clip on load (handy when recording the demo video).
loadSamples().then(() => {
  const q = new URLSearchParams(location.search);
  const clip = q.get("clip");
  if (q.get("lang")) $("lang").value = q.get("lang");
  const s = clip && samples.find((x) => x.file === clip);
  if (s) { $("sample").value = s.file; analyze({ sample: s.file, source: s.synthetic ? "synthetic" : "upload" }); }
});
