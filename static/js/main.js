(function () {
  "use strict";
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];

  // ---- mobile nav
  const toggle = $("#navToggle"), links = $("#navLinks");
  if (toggle) toggle.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open);
  });

  // ---- animated rings / bars (results + home)
  const CIRC = 2 * Math.PI * 52;
  window.addEventListener("load", () => {
    $$(".ring").forEach(r => {
      const fg = $(".ring-fg", r), score = +r.dataset.score;
      requestAnimationFrame(() => { fg.style.strokeDashoffset = CIRC * (1 - score / 100); });
    });
    $$(".bar i[data-w]").forEach(b => { b.style.width = b.dataset.w + "%"; });
  });

  // ---- copy buttons
  $$("[data-copy]").forEach(btn => btn.addEventListener("click", async () => {
    const text = $(btn.dataset.copy).innerText.trim();
    const original = btn.innerHTML;
    try { await navigator.clipboard.writeText(text); }
    catch (e) { const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); }
    btn.textContent = "Copied ✓";
    setTimeout(() => { btn.innerHTML = original; }, 1600);
  }));

  // ---- history delete
  $$("[data-delete]").forEach(btn => btn.addEventListener("click", async () => {
    if (!confirm("Delete this analysis?")) return;
    const id = btn.dataset.delete;
    const res = await fetch("/api/history/" + id, { method: "DELETE" });
    if (res.ok) { const row = $("#row-" + id); row.remove(); if (!$("tbody tr")) location.reload(); }
  }));

  // ---- analyzer page
  const form = $("#analyzeForm");
  if (!form) return;
  const drop = $("#dropzone"), input = $("#resumeInput"), info = $("#fileInfo"), err = $("#formError");
  const jd = $("#jobDesc"), btn = $("#analyzeBtn"), hint = $("#hint");
  let file = null;
  const MAX = 5 * 1024 * 1024;

  const fmt = b => b < 1024 ? b + " B" : b < MAX / 5 ? (b / 1024).toFixed(1) + " KB" : (b / 1048576).toFixed(2) + " MB";
  const showError = m => { err.textContent = m; err.hidden = !m; if (m) err.scrollIntoView({ behavior: "smooth", block: "center" }); };
  const wordCount = () => (jd.value.trim().match(/\S+/g) || []).length;

  function refresh() {
    const words = wordCount();
    $("#wordCount").textContent = words + " words";
    const ready = !!file && words >= 20;
    btn.disabled = !ready;
    hint.textContent = !file ? "Add a resume and a job description to enable analysis."
      : words < 20 ? "Paste a job description (at least 20 words)." : "Ready to analyze.";
  }

  function validate(f) {
    const ext = f.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx"].includes(ext)) return "Unsupported file type. Please upload a PDF or DOCX file.";
    if (f.size === 0) return "The file is empty.";
    if (f.size > MAX) return "File is larger than 5 MB.";
    return "";
  }
  function setFile(f) {
    const problem = validate(f);
    if (problem) { showError(problem); return; }
    showError(""); file = f;
    $("#fileName").textContent = f.name; $("#fileSize").textContent = fmt(f.size);
    info.hidden = false; drop.hidden = true; refresh();
  }
  function clearFile() { file = null; input.value = ""; info.hidden = true; drop.hidden = false; refresh(); }

  drop.addEventListener("click", () => input.click());
  drop.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
  input.addEventListener("change", () => input.files[0] && setFile(input.files[0]));
  ["dragenter", "dragover"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("drag"); }));
  ["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("drag"); }));
  drop.addEventListener("drop", e => { if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); });
  $("#removeFile").addEventListener("click", clearFile);
  jd.addEventListener("input", refresh);
  $("#sampleJd").addEventListener("click", async () => {
    const res = await fetch("/api/sample-jd"); const data = await res.json();
    jd.value = data.text; $("#jobTitle").value = "Junior Software Developer"; refresh();
  });

  form.addEventListener("submit", async e => {
    e.preventDefault();
    if (!file) return showError("Please upload your resume (PDF or DOCX).");
    if (wordCount() < 20) return showError("Please paste a job description (at least 20 words).");
    showError("");
    const overlay = $("#loading"), steps = $$("#progressSteps li");
    overlay.hidden = false;
    let i = 0;
    const tick = () => { steps.forEach((s, k) => { s.className = k < i ? "done" : k === i ? "active" : ""; }); i = Math.min(i + 1, steps.length - 1); };
    tick(); const timer = setInterval(tick, 450);
    const fd = new FormData();
    fd.append("resume", file); fd.append("job_description", jd.value); fd.append("job_title", $("#jobTitle").value);
    try {
      const res = await fetch("/api/analyze", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Analysis failed.");
      steps.forEach(s => s.className = "done");
      location.href = data.url;
    } catch (ex) {
      clearInterval(timer); overlay.hidden = true; showError(ex.message);
    }
  });
  refresh();
})();
