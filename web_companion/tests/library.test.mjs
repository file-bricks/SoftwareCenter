import test from "node:test";
import assert from "node:assert/strict";

import {
  createDemoProfile,
  filterEntries,
  parseProfilePayload,
  parseProfileText,
  summarizeProfile,
} from "../library.js";

test("parseProfilePayload akzeptiert Demo-Profil", () => {
  const parsed = parseProfilePayload(createDemoProfile());
  assert.equal(parsed.tabs.length, 3);
  assert.equal(parsed.currentTabIndex, 1);
});

test("parseProfilePayload lehnt falsches Format ab", () => {
  assert.throws(
    () => parseProfilePayload({ format: "falsch", format_version: 1, tabs: [] }),
    /Unbekanntes Profilformat/,
  );
});

test("parseProfileText lehnt ungültiges JSON ab", () => {
  assert.throws(
    () => parseProfileText("{ kaputt"),
    /kein gültiges JSON/,
  );
});

test("filterEntries sucht über Label, Tab und Notiz", () => {
  const parsed = parseProfilePayload(createDemoProfile());
  const result = filterEntries(parsed, { search: "literatur" });
  assert.equal(result.length, 1);
  assert.equal(result[0].label, "Zotero");
});

test("filterEntries filtert nach Tab und Typ", () => {
  const parsed = parseProfilePayload(createDemoProfile());
  const result = filterEntries(parsed, { tab: "Arbeit", kind: "url" });
  assert.equal(result.length, 1);
  assert.equal(result[0].label, "Ticket-Board");
});

test("summarizeProfile zählt Einträge pro Typ", () => {
  const parsed = parseProfilePayload(createDemoProfile());
  const summary = summarizeProfile(parsed);
  assert.equal(summary.entryCount, 5);
  assert.equal(summary.kinds.file, 2);
  assert.equal(summary.kinds.url, 1);
  assert.equal(summary.currentTabName, "Recherche");
});
