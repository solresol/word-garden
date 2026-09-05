(() => {
  "use strict";
  const config = window.ROOTLE_CONFIG;
  const engine = window.ROOTLE_ENGINE;
  if (!config || !engine || !Array.isArray(config.answers)) return;
  const musical = config.site === "solresol";
  const notes = ["do", "re", "mi", "fa", "sol", "la", "si"];
  const day = new Intl.DateTimeFormat("en-CA", { timeZone: config.time_zone, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  const storageKey = "rootle:" + config.site + ":archive-v2";
  const board = document.querySelector("#board");
  const keyboard = document.querySelector("#keyboard");
  const status = document.querySelector("#game-status");
  const hint = document.querySelector("#hint");
  const meanings = document.querySelector("#guess-meanings");
  const shareButton = document.querySelector("#share-button");
  const nextButton = document.querySelector("#new-game-button");
  const hintButton = document.querySelector("#hint-button");
  const storageStatus = document.querySelector("#storage-status");
  let lexicon = null;
  let lexiconFailed = false;
  let saved = null;
  const storageWarning = () => { storageStatus.textContent = "This browser cannot save your progress. Used words can only be remembered while this page stays open."; };
  try { saved = JSON.parse(localStorage.getItem(storageKey)); } catch (_) { storageWarning(); }
  let history = engine.restore(config.answers, saved, day);
  let answerData;
  let solution;
  const rank = { absent: 1, present: 2, correct: 3 };
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const won = () => history.active?.guesses.some((guess) => same(guess, solution));
  const finished = () => won() || history.active?.guesses.length >= 6;

  function persist() {
    try {
      const value = JSON.stringify(history);
      if (localStorage.getItem(storageKey) !== value) localStorage.setItem(storageKey, value);
    } catch (_) { storageWarning(); }
  }

  function translation(guess) {
    const spelling = guess.join(" · ");
    if (lexiconFailed) return spelling + ": dictionary unavailable. Reload to try again.";
    if (!lexicon) return spelling + ": looking up the meaning…";
    const gloss = lexicon[guess.join("")];
    return gloss ? spelling + ": " + gloss : spelling + ": no entry in this dictionary.";
  }

  function render() {
    const state = history.active;
    board.replaceChildren();
    meanings.replaceChildren();
    hint.hidden = true;
    shareButton.hidden = true;
    nextButton.hidden = true;
    keyboard.hidden = !state;
    hintButton.hidden = !state;
    if (!state) {
      document.querySelector("#puzzle-number").textContent = "No unused earlier words";
      status.textContent = config.answers.length
        ? "You have tried all the earlier words. Check back after the next publication."
        : "The first word is still on the home page. Rootle will start when another word is published.";
      meanings.hidden = true;
      return;
    }
    answerData = config.answers.find((answer) => answer.slug === state.slug);
    solution = answerData.tokens;
    const unit = musical ? "note" : "letter";
    document.querySelector("#puzzle-number").textContent = "Word " + history.used.length + " · " + solution.length + " " + unit + (solution.length === 1 ? "" : "s");
    board.style.setProperty("--word-length", solution.length);
    const keyboardState = {};
    for (let row = 0; row < 6; row += 1) {
      const submitted = state.guesses[row];
      const tokens = submitted || (row === state.guesses.length ? state.current : []);
      const marks = submitted ? engine.evaluate(submitted, solution) : [];
      solution.forEach((_, column) => {
        const tile = document.createElement("div");
        tile.className = "tile";
        const token = tokens[column] || "";
        tile.textContent = token;
        tile.setAttribute("aria-label", token ? token + (marks[column] ? ", " + marks[column] : "") : "empty");
        if (token) tile.classList.add("filled");
        if (marks[column]) {
          tile.classList.add(marks[column]);
          if (!keyboardState[token] || rank[marks[column]] > rank[keyboardState[token]]) keyboardState[token] = marks[column];
        }
        board.append(tile);
      });
    }
    keyboard.querySelectorAll(".key[data-key]").forEach((key) => {
      key.classList.remove("correct", "present", "absent");
      const mark = keyboardState[key.dataset.key];
      if (mark) key.classList.add(mark);
    });
    hint.hidden = !state.hint;
    hint.textContent = "Hint: " + answerData.hint;
    meanings.hidden = !musical || !state.guesses.length;
    if (musical) state.guesses.forEach((guess) => {
      const item = document.createElement("li");
      item.textContent = translation(guess);
      meanings.append(item);
    });
    if (finished()) {
      status.textContent = won() ? "Found it: " + answerData.display + "." : "The word was " + answerData.display + ".";
      shareButton.hidden = false;
      nextButton.hidden = !config.answers.some((answer) => !history.used.includes(answer.slug));
      if (nextButton.hidden) status.textContent += " You have tried all the earlier words. Check back after the next publication.";
    }
  }

  function makeKey(label, key, wide = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "key" + (wide ? " wide" : "");
    button.dataset.key = key;
    button.textContent = label;
    button.setAttribute("aria-label", key === "backspace" ? "Backspace" : label);
    return button;
  }

  function makeKeyboard() {
    if (musical) {
      const piano = document.createElement("div");
      piano.className = "piano";
      notes.forEach((note, index) => {
        const key = makeKey(note, note);
        key.classList.add("piano-key");
        key.setAttribute("aria-label", "Play " + note + " (" + (index + 1) + ")");
        piano.append(key);
      });
      [1, 2, 4, 5, 6].forEach((boundary) => {
        const sharp = document.createElement("span");
        sharp.className = "piano-black-key";
        sharp.style.left = (boundary * 100 / 7) + "%";
        sharp.setAttribute("aria-hidden", "true");
        piano.append(sharp);
      });
      const controls = document.createElement("div");
      controls.className = "keyboard-row piano-controls";
      controls.append(makeKey("Backspace", "backspace", true), makeKey("Enter", "enter", true));
      keyboard.append(piano, controls);
    } else {
      ["qwertyuiop", "asdfghjkl", "zxcvbnm"].forEach((letters, index) => {
        const row = document.createElement("div");
        row.className = "keyboard-row";
        if (index === 2) row.append(makeKey("Enter", "enter", true));
        [...letters].forEach((letter) => row.append(makeKey(letter.toUpperCase(), letter)));
        if (index === 2) row.append(makeKey("⌫", "backspace", true));
        keyboard.append(row);
      });
    }
  }

  function input(key) {
    const state = history.active;
    if (!state) return;
    if (musical && notes.includes(key)) {
      const button = keyboard.querySelector('[data-key="' + key + '"]');
      button.classList.add("pressed");
      window.setTimeout(() => button.classList.remove("pressed"), 180);
      window.SOLRESOL_AUDIO.play([key]).catch(() => { status.textContent = "Audio is unavailable; you can still enter notes."; });
    }
    if (finished()) return;
    if (key === "enter") {
      if (state.current.length !== solution.length) {
        status.textContent = "The guess needs " + solution.length + " " + (musical ? "note" : "letter") + (solution.length === 1 ? "" : "s") + ".";
        return;
      }
      state.guesses.push([...state.current]);
      state.current = [];
      status.textContent = "";
    } else if (key === "backspace") state.current.pop();
    else if ((musical ? notes.includes(key) : /^[a-z]$/.test(key)) && state.current.length < solution.length) state.current.push(key);
    else return;
    persist();
    render();
  }

  makeKeyboard();
  keyboard.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-key]");
    if (button) input(button.dataset.key);
  });
  document.addEventListener("keydown", (event) => {
    if (event.metaKey || event.ctrlKey || event.altKey || event.target.closest("input, textarea, select, [contenteditable=true]")) return;
    if (event.key === "Enter" && event.target.closest("button, summary, a") && !event.target.closest("#keyboard")) return;
    let key = event.key.toLowerCase();
    if (musical && /^[1-7]$/.test(key)) key = notes[Number(key) - 1];
    if (["enter", "backspace"].includes(key) || (musical ? notes.includes(key) : /^[a-z]$/.test(key))) {
      event.preventDefault();
      input(key);
    }
  });
  hintButton.addEventListener("click", () => {
    if (!history.active) return;
    history.active.hint = true;
    persist();
    render();
  });
  shareButton.addEventListener("click", async () => {
    const state = history.active;
    const rows = state.guesses.map((guess) => engine.evaluate(guess, solution).map((mark) => ({ correct: "🟩", present: "🟨", absent: "⬜" }[mark])).join(""));
    const text = "Rootle " + config.language + " · archive " + (won() ? state.guesses.length : "X") + "/6\n" + rows.join("\n") + "\n" + location.origin + "/rootle/";
    try { await navigator.clipboard.writeText(text); shareButton.textContent = "Copied"; }
    catch (_) { window.prompt("Copy your result", text); }
  });
  nextButton.addEventListener("click", () => {
    if (!finished()) return;
    history = engine.nextPuzzle(config.answers, history, day);
    persist();
    status.textContent = "";
    shareButton.textContent = "Copy result";
    render();
  });
  window.addEventListener("storage", (event) => { if (event.key === storageKey) location.reload(); });
  persist();
  render();
  if (musical) fetch(config.lexicon).then((response) => {
    if (!response.ok) throw new Error("Dictionary request failed");
    return response.json();
  }).then((data) => {
    if (!data.words || typeof data.words !== "object") throw new Error("Invalid dictionary");
    lexicon = data.words;
    render();
  }).catch(() => { lexiconFailed = true; render(); });
})();
