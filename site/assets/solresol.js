(() => {
  const frequencies = {
    do: 261.63,
    re: 293.66,
    mi: 329.63,
    fa: 349.23,
    sol: 392.0,
    la: 440.0,
    si: 493.88,
  };

  let context;
  async function play(notes, breaks = [], onNote = () => {}) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) throw new Error("Audio unavailable");
    context ||= new AudioContext();
    await context.resume();
    const start = context.currentTime + 0.04;
    let offset = 0;
    notes.forEach((note, index) => {
      if (breaks.includes(index)) offset += 0.22;
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      const noteStart = start + offset;
      oscillator.type = "sine";
      oscillator.frequency.value = frequencies[note];
      gain.gain.setValueAtTime(0.0001, noteStart);
      gain.gain.exponentialRampToValueAtTime(0.16, noteStart + 0.025);
      gain.gain.exponentialRampToValueAtTime(0.0001, noteStart + 0.29);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start(noteStart);
      oscillator.stop(noteStart + 0.3);
      oscillator.onended = () => { oscillator.disconnect(); gain.disconnect(); };
      window.setTimeout(() => onNote(index), (offset + 0.04) * 1000);
      window.setTimeout(() => onNote(-1), (offset + 0.34) * 1000);
      offset += 0.34;
    });
    await new Promise((resolve) => window.setTimeout(resolve, offset * 1000 + 100));
    onNote(-1);
  }
  window.SOLRESOL_AUDIO = { play };

  const randomIndex = (length) => {
    if (window.crypto?.getRandomValues) {
      const value = new Uint32Array(1);
      window.crypto.getRandomValues(value);
      return value[0] % length;
    }
    return Math.floor(Math.random() * length);
  };

  const drawNotation = (hat, avoid = null) => {
    const panels = [...hat.querySelectorAll("[data-notation]")];
    const choices = panels.filter((panel) => panel.dataset.notation !== avoid);
    const selected = choices[randomIndex(choices.length)];
    panels.forEach((panel) => {
      panel.hidden = panel !== selected;
    });
    return selected.dataset.notation;
  };

  document.querySelectorAll("[data-notation-hat]").forEach((hat) => {
    hat.dataset.currentNotation = drawNotation(hat);
  });

  document.addEventListener("click", async (event) => {
    const shuffle = event.target.closest("[data-notation-shuffle]");
    if (shuffle) {
      const hat = shuffle.closest("[data-notation-hat]");
      hat.dataset.currentNotation = drawNotation(hat, hat.dataset.currentNotation);
      return;
    }

    const button = event.target.closest(".play-word");
    if (!button) return;

    const notes = button.dataset.notes.split(",");
    const breaks = (button.dataset.breaks || "").split(",").filter(Boolean).map(Number);
    const originalLabel = button.textContent;
    const spelling = button.closest(".solresol-spelling");
    const visualNotes = spelling.querySelectorAll("[data-note-index]");
    button.disabled = true;
    button.textContent = "♪ Playing…";
    try {
      await play(notes, breaks, (index) => {
        visualNotes.forEach((element) => {
          element.classList.toggle("is-playing", Number(element.dataset.noteIndex) === index);
        });
      });
      button.textContent = originalLabel;
    } catch (_) {
      button.textContent = "Audio unavailable · try again";
    } finally {
      visualNotes.forEach((element) => element.classList.remove("is-playing"));
      button.disabled = false;
    }
  });
})();
