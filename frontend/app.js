const PERSONAS = [
  {id: "vedic", n: "Acharya Rishi", d: "Vedic · nakshatra & rashi"},
  {id: "western", n: "Luna", d: "Western · sun, moon, rising"},
  {id: "love", n: "Venus Rao", d: "Love & compatibility"},
];
const CHIPS = ["My personality traits", "Career outlook this year", "Love and relationships",
  "Today's horoscope", "Lucky colours and numbers", "Compatibility with a Libra"];
let persona = "western", history = [], busy = false;
const $ = (id) => document.getElementById(id);

function drawPersonas() {
  $("personas").replaceChildren(...PERSONAS.map((p) => {
    const b = document.createElement("button");
    b.className = p.id === persona ? "on" : "";
    const t = document.createElement("b"); t.textContent = p.n;
    const s = document.createElement("small"); s.textContent = p.d;
    b.append(t, s);
    b.onclick = () => { persona = p.id; history = []; drawPersonas(); };
    return b;
  }));
}
drawPersonas();
CHIPS.forEach((c) => {
  const b = document.createElement("button"); b.textContent = c;
  b.onclick = () => { $("q").value = c; send(); };
  $("chips").append(b);
});

function add(cls, text) {
  const d = document.createElement("div"); d.className = "m " + cls; d.textContent = text;
  $("log").append(d); $("log").scrollTop = 1e9; return d;
}

function showEvidence(r) {
  const box = $("evbody"); box.replaceChildren();
  const line = (label, value) => {
    const p = document.createElement("p"); const b = document.createElement("b");
    b.textContent = label + ": "; p.append(b, document.createTextNode(value)); box.append(p);
  };
  const c = r.chart;
  if (c) {
    const parts = [`tropical sun ${c.tropical_sun.sign}`];
    if (c.system === "sidereal") parts.push(`Vedic sun ${c.sun.sign}`);
    if (c.moon) parts.push(`moon ${c.moon.sign}${c.moon_approximate ? " (approx.)" : ""}`);
    if (c.nakshatra) parts.push(`nakshatra ${c.nakshatra.name}`);
    parts.push(c.rising ? `rising ${c.rising.sign}` : "rising unknown");
    line("Computed chart", parts.join(" · "));
  }
  line("Sources", r.sources.length ? r.sources.map((s) => `[${s.label}] ${s.title}`).join(", ") : "none");
  line("Guardrails", r.flags.length ? r.flags.join(", ") : "no flags");
  line("Model", `${r.model} · prompt ${r.prompt_version}`);
  $("evidence").hidden = false;
}

async function send() {
  const q = $("q").value.trim();
  if (!q || busy) return;
  if (!$("name").value.trim() || !$("dob").value) { add("b", "Please enter your name and date of birth first."); return; }
  busy = true; $("go").disabled = true; $("q").value = ""; add("u", q);
  const out = add("b", "✦ reading the stars…");
  const body = {
    profile: {name: $("name").value.trim(), dob: $("dob").value, tob: $("tob").value || null, pob: $("pob").value.trim() || null},
    question: q, persona, history,
  };
  try {
    const res = await fetch("/api/chat", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
    const data = await res.json();
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Please check your details.");
    out.textContent = data.answer; $("disclaimer").textContent = data.disclaimer;
    history.push({role: "user", content: q}, {role: "assistant", content: data.answer});
    history = history.slice(-10); showEvidence(data);
  } catch (e) { out.textContent = e.message || "The stars are cloudy. Please try again."; }
  busy = false; $("go").disabled = false;
}
$("go").onclick = send;
$("q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
