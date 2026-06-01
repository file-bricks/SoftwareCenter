import {
  createDemoProfile,
  filterEntries,
  parseProfilePayload,
  parseProfileText,
  readProfileFile,
  summarizeProfile,
} from "./library.js";

const STORAGE_KEY = "softwarecenter-web-companion-profile-v1";
const state = {
  profile: null,
  sourceLabel: "Kein Profil geladen",
};

const elements = {
  importInput: document.querySelector("#import-input"),
  importButton: document.querySelector("#import-button"),
  demoButton: document.querySelector("#demo-button"),
  resetButton: document.querySelector("#reset-button"),
  searchInput: document.querySelector("#search-input"),
  tabFilter: document.querySelector("#tab-filter"),
  kindFilter: document.querySelector("#kind-filter"),
  status: document.querySelector("#load-status"),
  installHint: document.querySelector("#install-hint"),
  offlineHint: document.querySelector("#offline-hint"),
  summary: document.querySelector("#summary-cards"),
  tabs: document.querySelector("#tab-list"),
  kinds: document.querySelector("#kind-list"),
  entries: document.querySelector("#entry-list"),
  empty: document.querySelector("#empty-state"),
};

function formatDate(isoString) {
  if (!isoString) {
    return "unbekannt";
  }
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) {
    return isoString;
  }
  return new Intl.DateTimeFormat("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function saveProfile(profile) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      profile,
      saved_at: new Date().toISOString(),
    }),
  );
}

function loadStoredProfile() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw);
    return parsed.profile ?? parsed.payload ?? null;
  } catch (_error) {
    return null;
  }
}

function coerceStoredProfile(profile) {
  if (!profile || typeof profile !== "object") {
    throw new Error("Kein gespeichertes Profil gefunden.");
  }
  if ("formatVersion" in profile && Array.isArray(profile.tabs)) {
    return profile;
  }
  return parseProfilePayload(profile);
}

function detectInstallHint() {
  const agent = navigator.userAgent.toLowerCase();
  if (agent.includes("iphone") || agent.includes("ipad")) {
    return "iPhone/iPad: In Safari über Teilen -> Zum Home-Bildschirm für den schnellen Companion-Zugriff.";
  }
  if (agent.includes("android")) {
    return "Android: Im Browser-Menü App installieren oder Zum Startbildschirm hinzufügen nutzen.";
  }
  return "Desktop: Als lokale PWA im Browser installieren oder als reine Offline-Referenz im Tab geöffnet lassen.";
}

function renderSummary(profile) {
  const summary = summarizeProfile(profile);
  const cards = [
    { label: "Quelle", value: state.sourceLabel },
    { label: "Plattform", value: profile.sourcePlatform },
    { label: "Exportiert", value: formatDate(profile.exportedAt) },
    { label: "App-Version", value: profile.appVersion },
    { label: "Tabs", value: String(summary.tabCount) },
    { label: "Einträge", value: String(summary.entryCount) },
    { label: "Aktiver Tab", value: summary.currentTabName },
  ];

  elements.summary.innerHTML = cards
    .map(
      (card) => `
        <article class="summary-card">
          <span class="summary-label">${escapeHtml(card.label)}</span>
          <strong class="summary-value">${escapeHtml(card.value)}</strong>
        </article>
      `,
    )
    .join("");
}

function renderTabs(profile) {
  elements.tabFilter.innerHTML = [`<option value="all">Alle Tabs</option>`]
    .concat(
      profile.tabs.map((tab) => `<option value="${escapeHtml(tab.name)}">${escapeHtml(tab.name)}</option>`),
    )
    .join("");

  elements.tabFilter.value = "all";

  elements.tabs.innerHTML = profile.tabs
    .map((tab, index) => {
      const entryLabel = `${tab.entries.length} Einträge`;
      const currentBadge = index === profile.currentTabIndex ? '<span class="pill pill-active">Aktiv</span>' : "";
      return `
        <li class="meta-item">
          <div>
            <strong>${escapeHtml(tab.name)}</strong>
            <span>${escapeHtml(tab.viewMode)} · ${entryLabel}</span>
          </div>
          ${currentBadge}
        </li>
      `;
    })
    .join("");
}

function renderKinds(profile) {
  const summary = summarizeProfile(profile);
  const kindEntries = Object.entries(summary.kinds).sort((left, right) => right[1] - left[1]);
  elements.kindFilter.innerHTML = [`<option value="all">Alle Typen</option>`]
    .concat(
      kindEntries.map(([kind]) => `<option value="${escapeHtml(kind)}">${escapeHtml(kind)}</option>`),
    )
    .join("");

  elements.kindFilter.value = "all";

  elements.kinds.innerHTML = kindEntries
    .map(
      ([kind, count]) => `
        <li class="meta-item">
          <div>
            <strong>${escapeHtml(kind)}</strong>
            <span>Eintragstyp aus dem Desktop-Export</span>
          </div>
          <span class="pill">${count}</span>
        </li>
      `,
    )
    .join("");
}

function renderEntries(profile) {
  const entries = filterEntries(profile, {
    search: elements.searchInput.value,
    tab: elements.tabFilter.value,
    kind: elements.kindFilter.value,
  });

  elements.entries.innerHTML = entries
    .map(
      (entry) => `
        <article class="entry-card">
          <div class="entry-card__header">
            <div>
              <h3>${escapeHtml(entry.label)}</h3>
              <p>${escapeHtml(entry.path)}</p>
            </div>
            <div class="entry-card__pills">
              <span class="pill">${escapeHtml(entry.kind)}</span>
              <span class="pill">${escapeHtml(entry.tabName)}</span>
            </div>
          </div>
          <div class="entry-card__body">
            <p>${entry.notes ? escapeHtml(entry.notes) : "Keine Notiz im Export vorhanden."}</p>
          </div>
        </article>
      `,
    )
    .join("");

  const hasEntries = entries.length > 0;
  elements.empty.hidden = hasEntries;
  elements.entries.hidden = !hasEntries;
}

function renderProfile(profile) {
  state.profile = profile;
  renderSummary(profile);
  renderTabs(profile);
  renderKinds(profile);
  renderEntries(profile);
}

function setStatus(message, kind = "info") {
  elements.status.textContent = message;
  elements.status.dataset.kind = kind;
}

function updateOfflineHint() {
  elements.offlineHint.textContent = navigator.onLine
    ? "Online oder lokaler Host erkannt. Nach dem ersten Laden bleibt der letzte Profilstand offline verfügbar."
    : "Offline-Modus aktiv. Der zuletzt geladene Profilstand kommt aus dem lokalen Browser-Speicher.";
}

async function handleFileImport() {
  const [file] = elements.importInput.files ?? [];
  if (!file) {
    return;
  }
  try {
    const profile = await readProfileFile(file);
    state.sourceLabel = file.name;
    saveProfile(profile);
    renderProfile(profile);
    setStatus(`Profil geladen: ${file.name}`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    elements.importInput.value = "";
  }
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  navigator.serviceWorker.register("./sw.js").catch(() => {
    setStatus("Service Worker konnte lokal nicht registriert werden.", "warning");
  });
}

function loadDemoProfile() {
  const profile = parseProfilePayload(createDemoProfile());
  state.sourceLabel = "Demo-Profil";
  saveProfile(profile);
  renderProfile(profile);
  setStatus("Demo-Profil geladen.", "success");
}

function clearStoredProfile() {
  localStorage.removeItem(STORAGE_KEY);
  state.profile = null;
  elements.summary.innerHTML = "";
  elements.tabs.innerHTML = "";
  elements.kinds.innerHTML = "";
  elements.entries.innerHTML = "";
  elements.empty.hidden = false;
  elements.entries.hidden = true;
  elements.tabFilter.innerHTML = '<option value="all">Alle Tabs</option>';
  elements.kindFilter.innerHTML = '<option value="all">Alle Typen</option>';
  state.sourceLabel = "Kein Profil geladen";
  setStatus("Lokaler Profilstand entfernt.", "info");
}

function bindEvents() {
  elements.importButton.addEventListener("click", () => elements.importInput.click());
  elements.importInput.addEventListener("change", handleFileImport);
  elements.demoButton.addEventListener("click", loadDemoProfile);
  elements.resetButton.addEventListener("click", clearStoredProfile);
  elements.searchInput.addEventListener("input", () => {
    if (state.profile) {
      renderEntries(state.profile);
    }
  });
  elements.tabFilter.addEventListener("change", () => {
    if (state.profile) {
      renderEntries(state.profile);
    }
  });
  elements.kindFilter.addEventListener("change", () => {
    if (state.profile) {
      renderEntries(state.profile);
    }
  });
  window.addEventListener("online", updateOfflineHint);
  window.addEventListener("offline", updateOfflineHint);
}

function boot() {
  elements.installHint.textContent = detectInstallHint();
  updateOfflineHint();
  bindEvents();
  registerServiceWorker();

  const params = new URLSearchParams(window.location.search);
  if (params.get("demo") === "1") {
    loadDemoProfile();
    return;
  }

  const stored = loadStoredProfile();
  if (stored) {
    try {
      const profile = coerceStoredProfile(stored);
      state.sourceLabel = "Zuletzt geladenes Profil";
      renderProfile(profile);
      setStatus("Letztes Profil aus dem Browser-Speicher wiederhergestellt.", "info");
      return;
    } catch (_error) {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  setStatus("Noch kein Profil geladen. Importiere eine `softwarecenter-profile-v1.json` oder starte mit Demo.", "info");
}

boot();
