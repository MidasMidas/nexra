const state = {
  selectedView: "dashboard",
  selectedSkillId: "skill-risk",
  selectedRating: 0,
  skills: [
    {
      id: "skill-risk",
      name: "Risk Sentinel",
      category: "Compliance",
      description: "Flags risky outputs, policy violations, and unsafe execution plans before an agent takes action.",
      pricePerCall: 0.08,
      status: "active",
      successRate: 98,
      latencyP95: 420,
      costEfficiency: 84,
      userRatingAvg: 4.7,
      userRatingCount: 128,
      recentCalls: 18420
    },
    {
      id: "skill-search",
      name: "Context Search",
      category: "Retrieval",
      description: "Retrieves domain-specific documents and compresses them into agent-friendly evidence packets.",
      pricePerCall: 0.03,
      status: "active",
      successRate: 94,
      latencyP95: 610,
      costEfficiency: 93,
      userRatingAvg: 4.3,
      userRatingCount: 204,
      recentCalls: 31980
    },
    {
      id: "skill-voice",
      name: "Voice Forge",
      category: "Media",
      description: "Turns structured responses into speech-ready assets with speaker controls and export presets.",
      pricePerCall: 0.12,
      status: "beta",
      successRate: 89,
      latencyP95: 920,
      costEfficiency: 67,
      userRatingAvg: 4.8,
      userRatingCount: 64,
      recentCalls: 7640
    }
  ],
  transactions: [
    { id: "txn_1001", type: "Invocation charges", amount: -124.32, timestamp: "2026-04-09 18:10" },
    { id: "txn_1002", type: "Top-up", amount: 500.0, timestamp: "2026-04-08 09:30" },
    { id: "txn_1003", type: "Invocation charges", amount: -87.76, timestamp: "2026-04-07 20:12" }
  ],
  apiKeys: [
    { id: "nk_live_01", name: "Production Gateway", scope: "invoke:all", lastUsed: "3 min ago", status: "active" },
    { id: "nk_test_02", name: "Staging Agent", scope: "invoke:read", lastUsed: "2 hrs ago", status: "active" },
    { id: "nk_old_03", name: "Legacy QA", scope: "invoke:all", lastUsed: "12 days ago", status: "revoked" }
  ],
  reviews: [
    { id: "rev_1", skillId: "skill-risk", author: "Ops Team", rating: 5, comment: "Catches edge-case policy issues before they hit production.", timestamp: "2026-04-09" },
    { id: "rev_2", skillId: "skill-risk", author: "Agent Builder", rating: 4, comment: "Very dependable, but we want more debugging detail on rejections.", timestamp: "2026-04-08" },
    { id: "rev_3", skillId: "skill-search", author: "Research Ops", rating: 4, comment: "Strong retrieval quality and good cost profile.", timestamp: "2026-04-07" },
    { id: "rev_4", skillId: "skill-voice", author: "Media Team", rating: 5, comment: "High perceived quality, though latency is still visible in long jobs.", timestamp: "2026-04-06" }
  ]
};

const heroTitle = document.querySelector("#hero-title");
const platformTrust = document.querySelector("#platform-trust");
const metricTemplate = document.querySelector("#metric-template");

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function currency(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function agentScore(skill) {
  const latencyScore = clamp(100 - (skill.latencyP95 - 200) / 10, 35, 100);
  return Math.round(skill.successRate * 0.5 + latencyScore * 0.3 + skill.costEfficiency * 0.2);
}

function normalizedUserRating(skill) {
  return Math.round((skill.userRatingAvg / 5) * 100);
}

function overallTrust(skill) {
  return Math.round(normalizedUserRating(skill) * 0.45 + agentScore(skill) * 0.55);
}

function averageTrust() {
  return Math.round(state.skills.reduce((sum, skill) => sum + overallTrust(skill), 0) / state.skills.length);
}

function balanceValue() {
  return 2864.92;
}

function totalCalls() {
  return state.skills.reduce((sum, skill) => sum + skill.recentCalls, 0);
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 2200);
}

function setView(view) {
  state.selectedView = view;
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === `${view}-view`);
  });
  document.querySelectorAll(".nav-link").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  const titles = {
    dashboard: "Operational trust for AI skills",
    marketplace: "Compare skills by quality, trust, and cost",
    skill: "Inspect trust, telemetry, and human feedback",
    billing: "Track spend and audit every invocation",
    keys: "Manage credentials for agent access"
  };
  heroTitle.textContent = titles[view];
}

function createMetricCard(label, value, meta) {
  const node = metricTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector(".metric-label").textContent = label;
  node.querySelector(".metric-value").textContent = value;
  node.querySelector(".metric-meta").textContent = meta;
  return node;
}

function renderDashboard() {
  const view = document.querySelector("#dashboard-view");
  view.innerHTML = "";

  const metrics = document.createElement("div");
  metrics.className = "metrics-grid";
  metrics.append(
    createMetricCard("Current balance", currency(balanceValue()), "Ready for agent invocations"),
    createMetricCard("Active skills", state.skills.filter((skill) => skill.status !== "revoked").length, "Marketplace inventory in circulation"),
    createMetricCard("Average trust", `${averageTrust()}/100`, "Blended user and agent score"),
    createMetricCard("30-day invocations", totalCalls().toLocaleString(), "Observed through gateway logs")
  );

  const topSkills = [...state.skills].sort((a, b) => overallTrust(b) - overallTrust(a));
  const trustPanel = document.createElement("div");
  trustPanel.className = "three-grid";

  const ranking = document.createElement("article");
  ranking.className = "panel";
  ranking.innerHTML = `<div class="section-title"><h3>Top trusted skills</h3><span class="pill">Ranking</span></div>`;
  topSkills.forEach((skill) => {
    const stat = document.createElement("div");
    stat.className = "inline-stat";
    stat.innerHTML = `<span>${skill.name}</span><strong>${overallTrust(skill)}/100</strong>`;
    ranking.appendChild(stat);
  });

  const trustSplit = document.createElement("article");
  trustSplit.className = "panel";
  trustSplit.innerHTML = `
    <div class="section-title"><h3>Trust split</h3><span class="pill">New model</span></div>
    <div class="score-stack">
      <div class="score-ring" style="--score:${averageTrust()}"><strong>${averageTrust()}</strong></div>
      <div class="score-list">
        <div><span>User rating influence</span><span>45%</span></div>
        <div><span>Agent rating influence</span><span>55%</span></div>
        <div><span>Manual reviews</span><span>${state.reviews.length}</span></div>
      </div>
    </div>
  `;

  const health = document.createElement("article");
  health.className = "panel";
  const avgSuccess = Math.round(state.skills.reduce((sum, skill) => sum + skill.successRate, 0) / state.skills.length);
  const avgLatency = Math.round(state.skills.reduce((sum, skill) => sum + skill.latencyP95, 0) / state.skills.length);
  const avgEfficiency = Math.round(state.skills.reduce((sum, skill) => sum + skill.costEfficiency, 0) / state.skills.length);
  health.innerHTML = `
    <div class="section-title"><h3>Agent rating health</h3><span class="pill">Auto-evaluated</span></div>
    <div class="inline-stat"><span>Avg success rate</span><strong>${avgSuccess}%</strong></div>
    <div class="inline-stat"><span>Avg latency p95</span><strong>${avgLatency} ms</strong></div>
    <div class="inline-stat"><span>Avg cost efficiency</span><strong>${avgEfficiency}/100</strong></div>
  `;

  trustPanel.append(ranking, trustSplit, health);
  view.append(metrics, trustPanel);
}

function renderMarketplace() {
  const view = document.querySelector("#marketplace-view");
  view.innerHTML = "";

  const controls = document.createElement("div");
  controls.className = "filter-row";
  controls.innerHTML = `
    <input id="skill-search-input" type="search" placeholder="Search skills, categories, or outcomes" />
    <select id="skill-sort-select">
      <option value="trust">Sort by overall trust</option>
      <option value="user">Sort by user rating</option>
      <option value="agent">Sort by agent rating</option>
      <option value="price">Sort by lowest price</option>
    </select>
  `;

  const list = document.createElement("div");
  list.className = "skill-grid";
  view.append(controls, list);

  function paintCards() {
    const query = document.querySelector("#skill-search-input").value.toLowerCase().trim();
    const sortBy = document.querySelector("#skill-sort-select").value;
    const filtered = state.skills.filter((skill) => {
      const corpus = `${skill.name} ${skill.category} ${skill.description}`.toLowerCase();
      return corpus.includes(query);
    });

    filtered.sort((a, b) => {
      if (sortBy === "price") return a.pricePerCall - b.pricePerCall;
      if (sortBy === "user") return b.userRatingAvg - a.userRatingAvg;
      if (sortBy === "agent") return agentScore(b) - agentScore(a);
      return overallTrust(b) - overallTrust(a);
    });

    list.innerHTML = "";
    filtered.forEach((skill) => {
      const card = document.createElement("article");
      card.className = "skill-card";
      card.innerHTML = `
        <div class="skill-head">
          <div>
            <p class="eyebrow">${skill.category}</p>
            <h3>${skill.name}</h3>
          </div>
          <span class="pill">${skill.status}</span>
        </div>
        <p>${skill.description}</p>
        <div class="skill-stats"><span>Overall trust: <strong>${overallTrust(skill)}/100</strong></span><span>${currency(skill.pricePerCall)}/call</span></div>
        <div class="skill-stats"><span>User: ${skill.userRatingAvg.toFixed(1)}/5</span><span>Agent: ${agentScore(skill)}/100</span></div>
        <button data-skill-id="${skill.id}">Open detail</button>
      `;
      list.appendChild(card);
    });

    list.querySelectorAll("button[data-skill-id]").forEach((button) => {
      button.addEventListener("click", () => {
        state.selectedSkillId = button.dataset.skillId;
        renderSkillDetail();
        setView("skill");
      });
    });
  }

  controls.querySelector("#skill-search-input").addEventListener("input", paintCards);
  controls.querySelector("#skill-sort-select").addEventListener("change", paintCards);
  paintCards();
}

function renderSkillDetail() {
  const view = document.querySelector("#skill-view");
  const skill = state.skills.find((entry) => entry.id === state.selectedSkillId) ?? state.skills[0];
  const reviews = state.reviews.filter((entry) => entry.skillId === skill.id).sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  const overall = overallTrust(skill);
  const agent = agentScore(skill);
  const user = normalizedUserRating(skill);

  view.innerHTML = `
    <div class="detail-layout">
      <div class="panel">
        <div class="detail-hero">
          <div>
            <p class="eyebrow">${skill.category}</p>
            <h3>${skill.name}</h3>
          </div>
          <span class="pill">${skill.status}</span>
        </div>
        <p>${skill.description}</p>
        <div class="score-stack">
          <div class="score-ring" style="--score:${overall}"><strong>${overall}</strong></div>
          <div class="score-list">
            <div><span>Overall trust</span><span>${overall}/100</span></div>
            <div><span>User rating</span><span>${skill.userRatingAvg.toFixed(1)}/5 (${user}/100)</span></div>
            <div><span>Agent rating</span><span>${agent}/100</span></div>
            <div><span>Price per call</span><span>${currency(skill.pricePerCall)}</span></div>
          </div>
        </div>
        <div class="two-grid">
          <article class="panel">
            <div class="section-title"><h3>User rating</h3><span class="pill">${skill.userRatingCount} reviews</span></div>
            <div class="inline-stat"><span>Average score</span><strong>${skill.userRatingAvg.toFixed(1)}/5</strong></div>
            <div class="inline-stat"><span>Normalized score</span><strong>${user}/100</strong></div>
            <div class="inline-stat"><span>Intent</span><strong>Human usefulness</strong></div>
          </article>
          <article class="panel">
            <div class="section-title"><h3>Agent rating</h3><span class="pill">Auto</span></div>
            <div class="inline-stat"><span>Success rate</span><strong>${skill.successRate}%</strong></div>
            <div class="inline-stat"><span>Latency p95</span><strong>${skill.latencyP95} ms</strong></div>
            <div class="inline-stat"><span>Cost efficiency</span><strong>${skill.costEfficiency}/100</strong></div>
          </article>
        </div>
      </div>

      <div class="panel">
        <div class="section-title"><h3>Submit user feedback</h3><span class="pill">Manual review</span></div>
        <form id="review-form" class="review-form">
          <label>Star rating</label>
          <div class="stars" id="stars"></div>
          <label for="review-comment">Short review</label>
          <textarea id="review-comment" rows="5" placeholder="What did this skill do well, and what should improve?"></textarea>
          <button class="primary-btn" type="submit">Save rating</button>
        </form>
      </div>
    </div>
    <div class="panel" style="margin-top:18px;">
      <div class="section-title"><h3>Recent reviews</h3><span class="pill">Human voice</span></div>
      <div class="review-list" id="review-list"></div>
    </div>
  `;

  const stars = document.querySelector("#stars");
  const reviewList = document.querySelector("#review-list");
  state.selectedRating = 0;

  for (let i = 1; i <= 5; i += 1) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "star";
    button.textContent = "★";
    button.setAttribute("aria-label", `${i} star`);
    button.addEventListener("click", () => {
      state.selectedRating = i;
      [...stars.children].forEach((child, index) => {
        child.classList.toggle("active", index < i);
      });
    });
    stars.appendChild(button);
  }

  reviews.forEach((review) => {
    const card = document.createElement("article");
    card.className = "review-card";
    card.innerHTML = `
      <div class="row-between">
        <strong>${review.author}</strong>
        <small>${review.timestamp}</small>
      </div>
      <p>${"★".repeat(review.rating)}${"☆".repeat(5 - review.rating)}</p>
      <p>${review.comment}</p>
    `;
    reviewList.appendChild(card);
  });

  document.querySelector("#review-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!state.selectedRating) {
      showToast("Choose a star rating first.");
      return;
    }

    const comment = document.querySelector("#review-comment").value.trim();
    const skillEntry = state.skills.find((entry) => entry.id === skill.id);
    const review = {
      id: `rev_${Date.now()}`,
      skillId: skill.id,
      author: "Console User",
      rating: state.selectedRating,
      comment: comment || "No written feedback left.",
      timestamp: "2026-04-09"
    };

    state.reviews.unshift(review);
    const newCount = skillEntry.userRatingCount + 1;
    const totalScore = skillEntry.userRatingAvg * skillEntry.userRatingCount + state.selectedRating;
    skillEntry.userRatingAvg = totalScore / newCount;
    skillEntry.userRatingCount = newCount;

    renderDashboard();
    renderMarketplace();
    renderSkillDetail();
    refreshPlatformTrust();
    showToast("User rating saved. Trust score updated.");
  });
}

function renderBilling() {
  const view = document.querySelector("#billing-view");
  view.innerHTML = `
    <div class="billing-grid">
      <article class="panel">
        <div class="section-title"><h3>Billing snapshot</h3><span class="pill">Usage based</span></div>
        <div class="inline-stat"><span>Current balance</span><strong>${currency(balanceValue())}</strong></div>
        <div class="inline-stat"><span>30-day spend</span><strong>${currency(212.08)}</strong></div>
        <div class="inline-stat"><span>Avg call price</span><strong>${currency(0.06)}</strong></div>
      </article>
      <article class="panel">
        <div class="section-title"><h3>Recent transactions</h3><span class="pill">Audit trail</span></div>
        <div id="transaction-list"></div>
      </article>
    </div>
  `;

  const list = document.querySelector("#transaction-list");
  state.transactions.forEach((transaction) => {
    const card = document.createElement("article");
    card.className = "transaction-card";
    card.innerHTML = `
      <div class="row-between">
        <strong>${transaction.type}</strong>
        <strong>${transaction.amount < 0 ? "-" : "+"}${currency(Math.abs(transaction.amount))}</strong>
      </div>
      <small>${transaction.id} • ${transaction.timestamp}</small>
    `;
    list.appendChild(card);
  });
}

function renderKeys() {
  const view = document.querySelector("#keys-view");
  view.innerHTML = `
    <div class="section-title">
      <h3>Agent credentials</h3>
      <button id="create-key-btn" class="primary-btn" type="button">Create API key</button>
    </div>
    <div class="keys-grid" id="keys-grid"></div>
  `;

  const list = document.querySelector("#keys-grid");
  state.apiKeys.forEach((key) => {
    const card = document.createElement("article");
    card.className = "key-card";
    card.innerHTML = `
      <div class="row-between">
        <strong>${key.name}</strong>
        <span class="pill">${key.status}</span>
      </div>
      <p>${key.id}</p>
      <small>Scope: ${key.scope}</small><br />
      <small>Last used: ${key.lastUsed}</small>
    `;
    list.appendChild(card);
  });

  document.querySelector("#create-key-btn").addEventListener("click", () => {
    state.apiKeys.unshift({
      id: `nk_live_${String(state.apiKeys.length + 1).padStart(2, "0")}`,
      name: "New Agent Key",
      scope: "invoke:all",
      lastUsed: "Never",
      status: "active"
    });
    renderKeys();
    showToast("New API key created.");
  });
}

function refreshPlatformTrust() {
  platformTrust.textContent = `${averageTrust()}/100`;
}

function initNavigation() {
  document.querySelectorAll(".nav-link").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });
}

function init() {
  initNavigation();
  renderDashboard();
  renderMarketplace();
  renderSkillDetail();
  renderBilling();
  renderKeys();
  setView("dashboard");
  refreshPlatformTrust();
}

init();
