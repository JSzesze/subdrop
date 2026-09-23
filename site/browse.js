/* Live published catalog only — never git raw or preview hosts. */
const CATALOG_URL = "https://subdrop.repruv.com/v1/catalog.json";

const MONEY = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

const BILLING_SHORT = { month: "mo", year: "yr", week: "wk" };
const BILLING_LONG = { month: "monthly", year: "yearly", week: "weekly" };

const state = {
  catalog: null,
  query: "",
  category: "",
  billing: "",
  view: "cards",
  sortKey: "name",
  sortDir: "asc",
};

const els = {
  q: document.getElementById("q"),
  category: document.getElementById("category"),
  billing: document.getElementById("billing"),
  sort: document.getElementById("sort"),
  viewCards: document.getElementById("view-cards"),
  viewTable: document.getElementById("view-table"),
  status: document.getElementById("status"),
  cards: document.getElementById("cards"),
  tableWrap: document.getElementById("table-wrap"),
  tableBody: document.getElementById("table-body"),
};

function text(value) {
  return value == null ? "" : String(value);
}

function categoryLabel(id) {
  const hit = (state.catalog?.categories || []).find((c) => c.id === id);
  return hit ? hit.label : id;
}

function money(n) {
  return MONEY.format(Number(n) || 0);
}

function listedPrice(svc) {
  const unit = BILLING_SHORT[svc.billing] || svc.billing;
  return `${money(svc.priceUsd)}/${unit}`;
}

function readParams() {
  const p = new URLSearchParams(location.search);
  state.query = p.get("q") || "";
  state.category = p.get("category") || "";
  state.billing = p.get("billing") || "";
  state.view = p.get("view") === "table" ? "table" : "cards";
  const sort = p.get("sort") || "name:asc";
  const [key, dir] = sort.split(":");
  state.sortKey = key || "name";
  state.sortDir = dir === "desc" ? "desc" : "asc";
}

function writeParams() {
  const p = new URLSearchParams();
  if (state.query) p.set("q", state.query);
  if (state.category) p.set("category", state.category);
  if (state.billing) p.set("billing", state.billing);
  if (state.view !== "cards") p.set("view", state.view);
  const sort = `${state.sortKey}:${state.sortDir}`;
  if (sort !== "name:asc") p.set("sort", sort);
  const qs = p.toString();
  const next = qs ? `?${qs}` : location.pathname;
  history.replaceState(null, "", next);
}

function applyControls() {
  els.q.value = state.query;
  els.category.value = state.category;
  els.billing.value = state.billing;
  els.sort.value = `${state.sortKey}:${state.sortDir}`;
  els.viewCards.setAttribute("aria-pressed", String(state.view === "cards"));
  els.viewTable.setAttribute("aria-pressed", String(state.view === "table"));
}

function haystack(svc) {
  return [
    svc.name,
    svc.plan,
    svc.blurb,
    svc.domain,
    svc.id,
    categoryLabel(svc.category),
    ...(svc.aliases || []),
  ]
    .map(text)
    .join(" ")
    .toLowerCase();
}

function filtered() {
  const q = state.query.trim().toLowerCase();
  let rows = state.catalog.services.slice();
  if (state.category) rows = rows.filter((s) => s.category === state.category);
  if (state.billing) rows = rows.filter((s) => s.billing === state.billing);
  if (q) rows = rows.filter((s) => haystack(s).includes(q));
  const dir = state.sortDir === "desc" ? -1 : 1;
  const key = state.sortKey;
  rows.sort((a, b) => {
    const av = a[key];
    const bv = b[key];
    if (typeof av === "number" || typeof bv === "number") {
      return ((Number(av) || 0) - (Number(bv) || 0)) * dir;
    }
    return text(av).localeCompare(text(bv), "en") * dir;
  });
  return rows;
}

function logoNode(svc, compact) {
  const wrap = document.createElement("span");
  const fallback = document.createElement("span");
  fallback.className = "logo-fallback";
  fallback.textContent = text(svc.name).slice(0, 1).toUpperCase() || "?";
  fallback.setAttribute("aria-hidden", "true");
  wrap.append(fallback);
  if (svc.logoUrl) {
    const img = document.createElement("img");
    img.className = "logo";
    img.alt = "";
    img.loading = compact ? "lazy" : "lazy";
    img.decoding = "async";
    img.src = svc.logoUrl;
    img.addEventListener("error", () => img.remove());
    img.addEventListener("load", () => fallback.remove());
    wrap.prepend(img);
  }
  return wrap;
}

function serviceTitle(svc) {
  const h = document.createElement("h2");
  if (svc.url) {
    const a = document.createElement("a");
    a.href = svc.url;
    a.rel = "noopener noreferrer";
    a.textContent = svc.name;
    h.append(a);
  } else {
    h.textContent = svc.name;
  }
  return h;
}

function renderCards(rows) {
  const root = els.cards;
  root.replaceChildren();
  if (!rows.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No services match those filters.";
    root.append(empty);
    return;
  }
  for (const svc of rows) {
    const card = document.createElement("article");
    card.className = "card";
    card.append(logoNode(svc, false), (() => {
      const mid = document.createElement("div");
      mid.append(serviceTitle(svc));
      const plan = document.createElement("p");
      plan.className = "plan";
      plan.textContent = svc.plan;
      mid.append(plan);
      return mid;
    })());
    const prices = document.createElement("div");
    prices.className = "price-block";
    const price = document.createElement("div");
    const listed = document.createElement("div");
    listed.className = "price";
    listed.textContent = listedPrice(svc);
    price.append(listed);
    if (svc.billing !== "month") {
      const equiv = document.createElement("div");
      equiv.className = "equiv";
      equiv.textContent = `${money(svc.monthlyUsd)}/mo equiv.`;
      price.append(equiv);
    }
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = categoryLabel(svc.category);
    prices.append(price, chip);
    card.append(prices);
    root.append(card);
  }
}

function renderTable(rows) {
  const body = els.tableBody;
  body.replaceChildren();
  document.querySelectorAll("th button[data-sort]").forEach((btn) => {
    const key = btn.getAttribute("data-sort");
    if (key === state.sortKey) btn.setAttribute("aria-sort", state.sortDir === "desc" ? "descending" : "ascending");
    else btn.removeAttribute("aria-sort");
  });
  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 6;
    td.className = "empty";
    td.textContent = "No services match those filters.";
    tr.append(td);
    body.append(tr);
    return;
  }
  for (const svc of rows) {
    const tr = document.createElement("tr");
    const nameTd = document.createElement("td");
    const row = document.createElement("div");
    row.className = "row-svc";
    const title = document.createElement("span");
    title.className = "svc-name";
    if (svc.url) {
      const a = document.createElement("a");
      a.href = svc.url;
      a.rel = "noopener noreferrer";
      a.textContent = svc.name;
      title.append(a);
    } else {
      title.textContent = svc.name;
    }
    row.append(logoNode(svc, true), title);
    nameTd.append(row);

    const cat = document.createElement("td");
    cat.textContent = categoryLabel(svc.category);
    const plan = document.createElement("td");
    plan.textContent = svc.plan;
    const listed = document.createElement("td");
    listed.className = "num";
    listed.textContent = money(svc.priceUsd);
    const billing = document.createElement("td");
    billing.textContent = BILLING_LONG[svc.billing] || svc.billing;
    const monthly = document.createElement("td");
    monthly.className = "num";
    monthly.textContent = money(svc.monthlyUsd);
    tr.append(nameTd, cat, plan, listed, billing, monthly);
    body.append(tr);
  }
}

function render() {
  if (!state.catalog) return;
  applyControls();
  writeParams();
  const rows = filtered();
  const generated = state.catalog.generatedAt
    ? state.catalog.generatedAt.slice(0, 10)
    : "unknown date";
  els.status.textContent = `Showing ${rows.length} of ${state.catalog.count} services · updated ${generated} · schema v${state.catalog.schemaVersion}`;
  const cards = state.view === "cards";
  els.cards.hidden = !cards;
  els.tableWrap.hidden = cards;
  if (cards) renderCards(rows);
  else renderTable(rows);
}

function fillCategories() {
  const seen = new Set();
  for (const c of state.catalog.categories || []) {
    if (seen.has(c.id)) continue;
    seen.add(c.id);
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.label;
    els.category.append(opt);
  }
}

function bind() {
  let timer = 0;
  els.q.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      state.query = els.q.value;
      render();
    }, 120);
  });
  els.category.addEventListener("change", () => {
    state.category = els.category.value;
    render();
  });
  els.billing.addEventListener("change", () => {
    state.billing = els.billing.value;
    render();
  });
  els.sort.addEventListener("change", () => {
    const [key, dir] = els.sort.value.split(":");
    state.sortKey = key;
    state.sortDir = dir === "desc" ? "desc" : "asc";
    render();
  });
  els.viewCards.addEventListener("click", () => {
    state.view = "cards";
    render();
  });
  els.viewTable.addEventListener("click", () => {
    state.view = "table";
    render();
  });
  document.querySelectorAll("th button[data-sort]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-sort");
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDir = "asc";
      }
      render();
    });
  });
}

async function main() {
  readParams();
  applyControls();
  bind();
  try {
    const res = await fetch(CATALOG_URL, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (!data || !Array.isArray(data.services)) {
      throw new Error("Unexpected catalog shape");
    }
    state.catalog = data;
    fillCategories();
    if (state.category && ![...els.category.options].some((o) => o.value === state.category)) {
      state.category = "";
    }
    render();
  } catch (err) {
    els.status.classList.add("error");
    els.status.textContent = `Could not load the live catalog (${err instanceof Error ? err.message : "error"}).`;
    const link = document.createElement("a");
    link.href = CATALOG_URL;
    link.textContent = " Open catalog.json";
    els.status.append(link);
  }
}

main();
