const PROFILE_FORMAT = "softwarecenter-profile-v1";
const PROFILE_FORMAT_VERSION = 1;

export function createDemoProfile() {
  return {
    format: PROFILE_FORMAT,
    format_version: PROFILE_FORMAT_VERSION,
    app_version: "1.0.0",
    source_platform: "win32",
    exported_at: "2026-06-01T09:00:00Z",
    current_tab: 1,
    tabs: [
      {
        name: "Arbeit",
        view_mode: "tiles",
        entries: [
          {
            label: "VS Code",
            path: "C:/Tools/VSCode/Code.exe",
            kind: "file",
            notes: "Haupteditor für Python und Markdown.",
          },
          {
            label: "Ticket-Board",
            path: "https://tickets.example.invalid",
            kind: "url",
            notes: "Browser-Startseite für das Tagesboard.",
          },
        ],
      },
      {
        name: "Recherche",
        view_mode: "list",
        entries: [
          {
            label: "Zotero",
            path: "C:/Programme/Zotero/zotero.exe",
            kind: "file",
            notes: "Literatur und PDF-Sammlung.",
          },
          {
            label: "DocFetcher",
            path: "C:/Portable/DocFetcher/DocFetcher.exe",
            kind: "script",
            notes: "Schnellsuche über lokale Archive.",
          },
        ],
      },
      {
        name: "Linux-Tools",
        view_mode: "tiles",
        entries: [
          {
            label: "DBeaver",
            path: "/usr/share/applications/dbeaver.desktop",
            kind: "linux_desktop",
            notes: "DB-Zugriff auf dem Linux-Rechner.",
          },
        ],
      },
    ],
  };
}

function normalizeEntry(entry, tabName) {
  if (!entry || typeof entry !== "object") {
    return null;
  }
  const path = String(entry.path ?? "").trim();
  if (!path) {
    return null;
  }
  const label = String(entry.label ?? "").trim() || path;
  const kind = String(entry.kind ?? "unknown").trim() || "unknown";
  const notes = entry.notes == null ? "" : String(entry.notes).trim();
  return {
    label,
    path,
    kind,
    notes,
    tabName,
  };
}

export function parseProfilePayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Das Profil ist kein JSON-Objekt.");
  }
  if (payload.format !== PROFILE_FORMAT || payload.format_version !== PROFILE_FORMAT_VERSION) {
    throw new Error("Unbekanntes Profilformat.");
  }
  if (!Array.isArray(payload.tabs) || payload.tabs.length === 0) {
    throw new Error("Das Profil enthält keine Tabs.");
  }

  const tabs = payload.tabs
    .filter((tab) => tab && typeof tab === "object")
    .map((tab, index) => {
      const name = String(tab.name ?? `Tab ${index + 1}`).trim() || `Tab ${index + 1}`;
      const viewMode = String(tab.view_mode ?? "tiles").toLowerCase() === "list" ? "list" : "tiles";
      const entries = Array.isArray(tab.entries)
        ? tab.entries.map((entry) => normalizeEntry(entry, name)).filter(Boolean)
        : [];
      return {
        name,
        viewMode,
        entries,
      };
    })
    .filter((tab) => tab.entries.length > 0 || tab.name);

  if (tabs.length === 0) {
    throw new Error("Das Profil enthält keine lesbaren Tabs.");
  }

  const currentTabIndex = Number.isInteger(payload.current_tab) ? payload.current_tab : Number.parseInt(payload.current_tab ?? "0", 10);
  return {
    format: PROFILE_FORMAT,
    formatVersion: PROFILE_FORMAT_VERSION,
    appVersion: String(payload.app_version ?? "unbekannt"),
    sourcePlatform: String(payload.source_platform ?? "unbekannt"),
    exportedAt: String(payload.exported_at ?? ""),
    currentTabIndex: Number.isFinite(currentTabIndex) && currentTabIndex >= 0 ? currentTabIndex : 0,
    tabs,
  };
}

export function flattenEntries(profile) {
  return profile.tabs.flatMap((tab) =>
    tab.entries.map((entry) => ({
      ...entry,
      viewMode: tab.viewMode,
    })),
  );
}

export function summarizeProfile(profile) {
  const entries = flattenEntries(profile);
  const byKind = {};
  for (const entry of entries) {
    byKind[entry.kind] = (byKind[entry.kind] ?? 0) + 1;
  }
  const currentTab = profile.tabs[profile.currentTabIndex] ?? profile.tabs[0] ?? null;
  return {
    tabCount: profile.tabs.length,
    entryCount: entries.length,
    currentTabName: currentTab ? currentTab.name : "Keine",
    kinds: byKind,
  };
}

export function filterEntries(profile, filters = {}) {
  const search = String(filters.search ?? "").trim().toLowerCase();
  const tab = String(filters.tab ?? "all");
  const kind = String(filters.kind ?? "all");

  return flattenEntries(profile).filter((entry) => {
    if (tab !== "all" && entry.tabName !== tab) {
      return false;
    }
    if (kind !== "all" && entry.kind !== kind) {
      return false;
    }
    if (!search) {
      return true;
    }
    return [
      entry.label,
      entry.path,
      entry.kind,
      entry.notes,
      entry.tabName,
    ].some((part) => part.toLowerCase().includes(search));
  });
}

export async function readProfileFile(file) {
  const text = await file.text();
  return parseProfileText(text);
}

export function parseProfileText(text) {
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch (error) {
    throw new Error("Die Datei enthält kein gültiges JSON.");
  }
  return parseProfilePayload(parsed);
}
