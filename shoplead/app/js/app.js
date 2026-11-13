(function () {
  const STORAGE_KEY = "shoplead-leads-v1";
  let current = null;
  let leads = [];

  const $ = (id) => document.getElementById(id);

  async function loadSeed() {
    const res = await fetch("data/seed.json");
    const seed = await res.json();
    return seed.map((s, i) => ({
      id: s.id || ("seed-" + (i + 1)),
      date: s.date,
      customer: s.customer,
      phone: s.phone || "",
      vehicle: s.vehicle,
      service: s.service,
      status: s.status || "New",
      urgency: s.urgency,
      missing: s.missing,
      nextAction: s.nextAction,
      draft: s.draft,
      original: s.original,
      summary: s.summary,
      automation: s.automation || "Draft prepared — review required; not sent",
      source: s.source || "Seed"
    }));
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(leads));
  }

  async function initLeads() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try { leads = JSON.parse(saved); }
      catch { leads = await loadSeed(); persist(); }
    } else {
      leads = await loadSeed();
      persist();
    }
    renderLeads();
  }

  function showView(name) {
    document.querySelectorAll(".view").forEach((el) => { el.hidden = el.id !== "view-" + name; });
    document.querySelectorAll(".nav").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === name);
    });
  }

  function urgencyClass(u) {
    if (u.startsWith("CRITICAL")) return "crit";
    if (u.startsWith("HIGH")) return "high";
    return "norm";
  }

  function renderResult(lead) {
    current = lead;
    $("result-panel").hidden = false;
    const chip = $("urgency-chip");
    chip.textContent = lead.urgency;
    chip.className = "urgency-chip " + urgencyClass(lead.urgency);
    $("fields").innerHTML = [
      ["Customer", lead.customer],
      ["Phone", lead.phone || "—"],
      ["Vehicle", lead.vehicle],
      ["Service", lead.service],
      ["Missing info", lead.missing],
      ["Next action", lead.nextAction],
      ["Summary", lead.summary]
    ].map(([k, v]) => "<dt>" + k + "</dt><dd>" + escapeHtml(v) + "</dd>").join("");
    $("draft").value = lead.draft;
    $("auto-status").textContent = lead.automation;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function renderLeads() {
    const filter = $("filter-urgency").value;
    const list = $("leads-list");
    const rows = leads.filter((l) => !filter || l.urgency === filter);
    if (!rows.length) {
      list.innerHTML = "<p class='meta'>No leads yet.</p>";
      return;
    }
    list.innerHTML = rows.map((l) => (
      '<article class="lead-card" data-id="' + l.id + '">' +
      "<h3>" + escapeHtml(l.vehicle) + " · " + escapeHtml(l.service) + "</h3>" +
      '<div class="meta">' + escapeHtml(l.urgency) + " · " + escapeHtml(l.customer) + " · " + escapeHtml(l.automation) + "</div>" +
      "</article>"
    )).join("");
    list.querySelectorAll(".lead-card").forEach((card) => {
      card.addEventListener("click", () => {
        const lead = leads.find((x) => x.id === card.dataset.id);
        if (!lead) return;
        showView("inbox");
        $("raw").value = lead.original;
        renderResult(lead);
      });
    });
  }

  function toCsv(rows) {
    const headers = ["Date","Customer","Phone","Vehicle","Requested Service","Status","Urgency","Missing Information","Next Action","Follow-up Draft","Original Message","AI Summary","Automation Status"];
    const esc = (v) => '"' + String(v ?? "").replace(/"/g, '""') + '"';
    return [headers.join(",")].concat(rows.map((l) => [
      l.date, l.customer, l.phone, l.vehicle, l.service, l.status, l.urgency, l.missing, l.nextAction, l.draft, l.original, l.summary, l.automation
    ].map(esc).join(","))).join("\n");
  }

  function download(name, text) {
    const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  $("analyze").addEventListener("click", () => {
    const raw = $("raw").value.trim();
    if (!raw) return alert("Paste a customer message first.");
    const lead = Object.assign({ id: "local-" + Date.now(), source: $("source").value }, ShopLeadExtract.analyze(raw));
    renderResult(lead);
  });

  $("clear").addEventListener("click", () => {
    $("raw").value = "";
    $("result-panel").hidden = true;
    current = null;
  });

  $("approve").addEventListener("click", () => {
    if (!current) return;
    current.draft = $("draft").value;
    current.automation = "Approved locally — not sent";
    $("auto-status").textContent = current.automation;
    const idx = leads.findIndex((l) => l.id === current.id);
    if (idx >= 0) { leads[idx] = current; persist(); renderLeads(); }
  });

  $("copy").addEventListener("click", async () => {
    await navigator.clipboard.writeText($("draft").value);
    $("auto-status").textContent = "Draft copied — still not sent";
  });

  $("save-lead").addEventListener("click", () => {
    if (!current) return;
    current.draft = $("draft").value;
    const idx = leads.findIndex((l) => l.id === current.id);
    if (idx >= 0) leads[idx] = current;
    else leads.unshift(current);
    persist();
    renderLeads();
    $("auto-status").textContent = "Saved locally — " + current.automation;
  });

  $("export-one").addEventListener("click", () => {
    if (!current) return;
    current.draft = $("draft").value;
    download("shoplead-one.csv", toCsv([current]));
  });

  $("export-all").addEventListener("click", () => download("shoplead-leads.csv", toCsv(leads)));
  $("filter-urgency").addEventListener("change", renderLeads);
  $("reset-seed").addEventListener("click", async () => {
    leads = await loadSeed();
    persist();
    renderLeads();
  });

  document.querySelectorAll(".nav").forEach((btn) => {
    btn.addEventListener("click", () => showView(btn.dataset.view));
  });

  // quick self-tests in console
  const t1 = ShopLeadExtract.analyze("I have a 1987 RX7 that I need to do my brake pads on. If you could call me back, that would be greatly appreciated");
  console.assert(!t1.urgency.startsWith("CRITICAL"), "pads should not be CRITICAL", t1);
  console.assert(/Mazda RX-7/.test(t1.vehicle), "RX7 vehicle", t1.vehicle);
  const t2 = ShopLeadExtract.analyze("Hi, this is Maria. My 2018 Honda Civic brakes are grinding and the pedal feels soft. Can you look at it today?");
  console.assert(t2.urgency === "CRITICAL — SAFETY", "maria critical", t2);
  console.assert(!/column\s+[BCD]/i.test(t2.draft), "no column leak", t2.draft);
  const t3 = ShopLeadExtract.analyze("Hey man, I have a 2014 hyuandai Tucson and the catalytic converter pipe separated from the flange today.");
  console.assert(/Hyundai Tucson/.test(t3.vehicle), "hyundai", t3.vehicle);
  console.assert(t3.urgency === "HIGH — INSPECT", "exhaust inspect", t3.urgency);

  initLeads();
})();
