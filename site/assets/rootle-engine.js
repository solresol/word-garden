/* Pure game rules shared by the browser and the regression tests. */
((root) => {
  "use strict";
  function evaluate(guess, solution) {
    const marks = solution.map(() => "absent");
    const remaining = {};
    solution.forEach((token, index) => {
      if (guess[index] === token) marks[index] = "correct";
      else remaining[token] = (remaining[token] || 0) + 1;
    });
    guess.forEach((token, index) => {
      if (marks[index] !== "correct" && remaining[token] > 0) {
        marks[index] = "present";
        remaining[token] -= 1;
      }
    });
    return marks;
  }
  function nextPuzzle(answers, history, day, random = Math.random) {
    const used = new Set(history.used || []);
    const available = answers.filter((answer) => !used.has(answer.slug));
    if (!available.length) return { used: [...used], active: null };
    const answer = available[Math.floor(random() * available.length)];
    used.add(answer.slug);
    return { used: [...used], active: { slug: answer.slug, tokens: answer.tokens, day, guesses: [], current: [], hint: false } };
  }
  function restore(answers, saved, day, random = Math.random) {
    const history = { used: Array.isArray(saved?.used) ? saved.used.filter((slug) => typeof slug === "string") : [], active: null };
    const active = saved?.active;
    const answer = answers.find((entry) => entry.slug === active?.slug);
    const validTokens = (tokens) => Array.isArray(tokens) && tokens.every((token) => typeof token === "string");
    if (answer && active.day === day && JSON.stringify(active.tokens) === JSON.stringify(answer.tokens)
      && Array.isArray(active.guesses) && active.guesses.length <= 6
      && active.guesses.every((guess) => validTokens(guess) && guess.length === answer.tokens.length)
      && validTokens(active.current) && active.current.length <= answer.tokens.length) {
      history.active = active;
      if (!history.used.includes(active.slug)) history.used.push(active.slug);
      return history;
    }
    return nextPuzzle(answers, history, day, random);
  }
  const api = { evaluate, nextPuzzle, restore };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ROOTLE_ENGINE = api;
})(typeof window !== "undefined" ? window : globalThis);
