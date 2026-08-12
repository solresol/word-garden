(() => {
  "use strict";

  const config = window.ROOTLE_CONFIG;
  if (!config || !Array.isArray(config.answers) || config.answers.length === 0) return;

  const now = new Date();
  const todayUTC = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const anchorParts = config.anchor.split("-").map(Number);
  const anchorUTC = Date.UTC(anchorParts[0], anchorParts[1] - 1, anchorParts[2]);
  const puzzle = Math.max(0, Math.floor((todayUTC - anchorUTC) / 86400000));
  const answerData = config.answers[puzzle % config.answers.length];
  const solution = answerData.answer.toLowerCase();
  const maxRows = 6;
  const dateKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  const storageKey = `rootle:${config.site}:${dateKey}`;
  const board = document.querySelector("#board");
  const keyboard = document.querySelector("#keyboard");
  const status = document.querySelector("#game-status");
  const hint = document.querySelector("#hint");
  const shareButton = document.querySelector("#share-button");
  const replayButton = document.querySelector("#new-game-button");
  const hintButton = document.querySelector("#hint-button");
  document.querySelector("#puzzle-number").textContent = `Puzzle ${puzzle + 1} · ${solution.length} letters`;
  board.style.setProperty("--word-length", solution.length);

  let state = { guesses: [], current: "", finished: false, won: false, hint: false };
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey));
    if (saved && Array.isArray(saved.guesses)) state = { ...state, ...saved };
  } catch (_) {
    // A blocked or corrupt localStorage should not block the game.
  }

  const rank = { absent: 1, present: 2, correct: 3 };
  const keyboardState = {};

  function evaluate(guess) {
    const result = Array(solution.length).fill("absent");
    const remaining = {};
    for (let index = 0; index < solution.length; index += 1) {
      if (guess[index] === solution[index]) result[index] = "correct";
      else remaining[solution[index]] = (remaining[solution[index]] || 0) + 1;
    }
    for (let index = 0; index < solution.length; index += 1) {
      if (result[index] === "correct") continue;
      const letter = guess[index];
      if (remaining[letter] > 0) {
        result[index] = "present";
        remaining[letter] -= 1;
      }
    }
    return result;
  }

  function persist() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch (_) {
      // The game remains playable without persistence.
    }
  }

  function render() {
    board.replaceChildren();
    Object.keys(keyboardState).forEach((key) => delete keyboardState[key]);
    for (let row = 0; row < maxRows; row += 1) {
      const submitted = state.guesses[row];
      const letters = submitted || (row === state.guesses.length ? state.current : "");
      const marks = submitted ? evaluate(submitted) : [];
      for (let column = 0; column < solution.length; column += 1) {
        const tile = document.createElement("div");
        tile.className = "tile";
        const letter = letters[column] || "";
        tile.textContent = letter;
        tile.setAttribute("aria-label", letter ? `${letter}${marks[column] ? `, ${marks[column]}` : ""}` : "empty");
        if (letter) tile.classList.add("filled");
        if (marks[column]) {
          tile.classList.add(marks[column]);
          if (!keyboardState[letter] || rank[marks[column]] > rank[keyboardState[letter]]) keyboardState[letter] = marks[column];
        }
        board.append(tile);
      }
    }
    keyboard.querySelectorAll(".key[data-key]").forEach((key) => {
      key.classList.remove("correct", "present", "absent");
      const mark = keyboardState[key.dataset.key];
      if (mark) key.classList.add(mark);
    });
    hint.hidden = !state.hint;
    hint.textContent = `Hint: ${answerData.hint}`;
    if (state.finished) {
      status.textContent = state.won ? `Found it: ${answerData.display}.` : `Today’s word was ${answerData.display}.`;
      shareButton.hidden = false;
      replayButton.hidden = false;
    }
  }

  function makeKeyboard() {
    const rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];
    rows.forEach((letters, index) => {
      const row = document.createElement("div");
      row.className = "keyboard-row";
      if (index === 2) row.append(makeKey("Enter", "enter", true));
      [...letters].forEach((letter) => row.append(makeKey(letter.toUpperCase(), letter, false)));
      if (index === 2) row.append(makeKey("⌫", "backspace", true));
      keyboard.append(row);
    });
  }

  function makeKey(label, key, wide) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `key${wide ? " wide" : ""}`;
    button.dataset.key = key;
    button.textContent = label;
    button.setAttribute("aria-label", key === "backspace" ? "Backspace" : label);
    return button;
  }

  function submit() {
    if (state.current.length !== solution.length) {
      status.textContent = `The guess needs ${solution.length} letters.`;
      return;
    }
    state.guesses.push(state.current);
    state.won = state.current === solution;
    state.current = "";
    state.finished = state.won || state.guesses.length >= maxRows;
    status.textContent = "";
    persist();
    render();
  }

  function input(key) {
    if (state.finished) return;
    if (key === "enter") submit();
    else if (key === "backspace") {
      state.current = state.current.slice(0, -1);
      render();
    } else if (/^[a-z]$/.test(key) && state.current.length < solution.length) {
      state.current += key;
      render();
    }
  }

  function shareText() {
    const rows = state.guesses.map((guess) => evaluate(guess).map((mark) => ({ correct: "🟩", present: "🟨", absent: "⬜" }[mark])).join(""));
    return `Rootle ${config.language} #${puzzle + 1} ${state.won ? state.guesses.length : "X"}/${maxRows}\n${rows.join("\n")}\n${location.origin}/rootle/`;
  }

  makeKeyboard();
  keyboard.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-key]");
    if (button) input(button.dataset.key);
  });
  document.addEventListener("keydown", (event) => {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    if (event.key === "Enter") input("enter");
    else if (event.key === "Backspace") input("backspace");
    else input(event.key.toLowerCase());
  });
  hintButton.addEventListener("click", () => {
    state.hint = true;
    persist();
    render();
  });
  shareButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(shareText());
      shareButton.textContent = "Copied";
    } catch (_) {
      window.prompt("Copy your result", shareText());
    }
  });
  replayButton.addEventListener("click", () => {
    state = { guesses: [], current: "", finished: false, won: false, hint: false };
    persist();
    status.textContent = "";
    shareButton.hidden = true;
    replayButton.hidden = true;
    render();
  });
  render();
})();
