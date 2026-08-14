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

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".play-word");
    if (!button) return;

    const notes = button.dataset.notes.split(",");
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) {
      button.textContent = "Audio is unavailable";
      return;
    }

    const context = new AudioContext();
    await context.resume();
    const start = context.currentTime + 0.04;
    notes.forEach((note, index) => {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      const noteStart = start + index * 0.34;
      oscillator.type = "sine";
      oscillator.frequency.value = frequencies[note];
      gain.gain.setValueAtTime(0.0001, noteStart);
      gain.gain.exponentialRampToValueAtTime(0.16, noteStart + 0.025);
      gain.gain.exponentialRampToValueAtTime(0.0001, noteStart + 0.29);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start(noteStart);
      oscillator.stop(noteStart + 0.3);
    });
    window.setTimeout(() => context.close(), notes.length * 340 + 500);
  });
})();
