const { test } = require("node:test");
const assert = require("node:assert/strict");
const { evaluate, nextPuzzle, restore } = require("../site/assets/rootle-engine.js");
const answers = [
  { slug: "solresol", tokens: ["sol", "re", "sol"] },
  { slug: "do", tokens: ["do"] },
  { slug: "re", tokens: ["re"] },
];
const day = "2026-09-05";

test("random draws remove used words, exhaust the pool, and admit later publications", () => {
  let history = nextPuzzle(answers, { used: [] }, day, () => 0.5);
  assert.equal(history.active.slug, "do");
  history = nextPuzzle(answers, history, day, () => 0.99);
  assert.equal(history.active.slug, "re");
  history = nextPuzzle(answers, history, day, () => 0);
  assert.equal(history.active.slug, "solresol");
  assert.equal(new Set(history.used).size, 3);
  history = nextPuzzle(answers, history, day);
  assert.equal(history.active, null);
  assert.equal(restore(answers, history, "2026-09-06").active, null);
  const expanded = [...answers, { slug: "mi", tokens: ["mi"] }];
  assert.equal(restore(expanded, history, "2026-09-07").active.slug, "mi");
});

test("reload retains the answer, entered notes, guesses, and hint", () => {
  const history = nextPuzzle(answers, { used: [] }, day, () => 0);
  history.active.guesses.push(["do", "re", "mi"]);
  history.active.current = ["sol"];
  history.active.hint = true;
  assert.deepEqual(restore(answers, history, day, () => 0.99), history);
  const tomorrow = restore(answers, history, "2026-09-06", () => 0);
  assert.equal(tomorrow.active.slug, "do");
  assert.deepEqual(tomorrow.used, ["solresol", "do"]);
});

test("stale or damaged saves do not restore an ineligible answer", () => {
  const saved = nextPuzzle(answers, { used: [] }, day, () => 0);
  assert.equal(restore(answers.slice(1), saved, day, () => 0).active.slug, "do");
  saved.active.guesses = "damaged";
  assert.equal(restore(answers, saved, day, () => 0).active.slug, "do");
  assert.ok(restore(answers, { used: "damaged", active: 4 }, day).active);
  assert.equal(restore([], null, day).active, null);
});

test("duplicate notes use one occurrence each, with exact positions counted first", () => {
  assert.deepEqual(evaluate(["sol", "sol", "sol"], ["sol", "re", "sol"]), ["correct", "absent", "correct"]);
  assert.deepEqual(evaluate(["re", "sol", "do"], ["sol", "re", "sol"]), ["present", "present", "absent"]);
  assert.deepEqual(evaluate([..."eerie"], [..."serve"]), ["absent", "correct", "correct", "absent", "correct"]);
});
