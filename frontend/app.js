(() => {
  const form = document.getElementById("search-form");
  const input = document.getElementById("product-input");
  const statusMessage = document.getElementById("status-message");
  const dashboard = document.getElementById("dashboard");
  const cardsEl = document.getElementById("cards");
  const recommendationEl = document.getElementById("recommendation");
  const submitButton = form.querySelector("button");

  // Anonymous, random per-browser-tab token used only to group analytics
  // events (e.g. "3 distinct sessions searched today"). It contains no
  // personal data, is never sent anywhere except as an opaque string, and
  // disappears when the tab closes.
  const SESSION_KEY = "bri_anon_session";
  let sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = crypto.getRandomValues(new Uint32Array(4)).join("");
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }

  const PLATFORM_LABELS = {
    amazon: "Amazon",
    nykaa: "Nykaa",
    myntra: "Myntra",
    tira: "Tira",
    ajio: "AJIO",
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const product = input.value.trim();
    if (!product) return;

    setLoading(true);
    statusMessage.textContent = `Fetching reviews for "${product}" across platforms…`;
    statusMessage.classList.remove("error");
    dashboard.hidden = true;

    try {
      const url = `/api/search?product=${encodeURIComponent(product)}&session=${encodeURIComponent(sessionId)}`;
      const response = await fetch(url);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong. Please try again.");
      }

      renderDashboard(data);
      statusMessage.textContent = "";
    } catch (err) {
      statusMessage.textContent = err.message;
      statusMessage.classList.add("error");
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    submitButton.textContent = isLoading ? "Searching…" : "Search";
  }

  function renderDashboard(data) {
    cardsEl.innerHTML = "";
    recommendationEl.innerHTML = "";

    if (data.recommendation) {
      const { platform, reason } = data.recommendation;
      recommendationEl.innerHTML = `🏆 Best platform for <strong>${escapeHtml(data.product)}</strong>: ` +
        `<strong>${PLATFORM_LABELS[platform] || platform}</strong> — ${escapeHtml(reason)}`;
      recommendationEl.hidden = false;
    } else {
      recommendationEl.innerHTML = "We couldn't gather enough data to recommend a platform for this product right now.";
      recommendationEl.hidden = false;
    }

    data.platforms.forEach((card) => cardsEl.appendChild(buildCard(card)));
    dashboard.hidden = false;
  }

  function buildCard(card) {
    const wrapper = document.createElement("article");
    wrapper.className = "card";

    const title = document.createElement("h2");
    title.textContent = PLATFORM_LABELS[card.platform] || card.platform;
    wrapper.appendChild(title);

    if (card.status !== "ok") {
      const unavailable = document.createElement("p");
      unavailable.className = "unavailable";
      unavailable.textContent = card.message || "Data unavailable for this platform";
      wrapper.appendChild(unavailable);
      return wrapper;
    }

    const rating = document.createElement("p");
    rating.className = "rating";
    rating.textContent = card.rating != null ? `★ ${card.rating.toFixed(1)} / 5` : "Rating unavailable";
    wrapper.appendChild(rating);

    const reviewCount = document.createElement("p");
    reviewCount.className = "review-count";
    reviewCount.textContent = `${card.review_count.toLocaleString()} reviews analysed`;
    wrapper.appendChild(reviewCount);

    if (card.sentiment) {
      wrapper.appendChild(buildDonut(card.sentiment));
    }

    if (card.keywords && card.keywords.length) {
      const keywordsEl = document.createElement("div");
      keywordsEl.className = "keywords";
      card.keywords.forEach((word) => {
        const chip = document.createElement("span");
        chip.className = "keyword-chip";
        chip.textContent = word;
        keywordsEl.appendChild(chip);
      });
      wrapper.appendChild(keywordsEl);
    }

    return wrapper;
  }

  function buildDonut(sentiment) {
    const wrap = document.createElement("div");
    wrap.className = "donut-wrap";

    const positive = sentiment.positive || 0;
    const neutral = sentiment.neutral || 0;
    const negative = sentiment.negative || 0;

    const positiveEnd = positive;
    const neutralEnd = positiveEnd + neutral;

    const donut = document.createElement("div");
    donut.className = "donut";
    donut.style.background =
      `conic-gradient(var(--positive) 0% ${positiveEnd}%, ` +
      `var(--neutral) ${positiveEnd}% ${neutralEnd}%, ` +
      `var(--negative) ${neutralEnd}% 100%)`;
    donut.setAttribute("role", "img");
    donut.setAttribute(
      "aria-label",
      `Sentiment breakdown: ${positive}% positive, ${neutral}% neutral, ${negative}% negative`
    );
    wrap.appendChild(donut);

    const legend = document.createElement("div");
    legend.className = "legend";
    legend.innerHTML = `
      <span><i class="dot positive"></i>Positive ${positive}%</span>
      <span><i class="dot neutral"></i>Neutral ${neutral}%</span>
      <span><i class="dot negative"></i>Negative ${negative}%</span>
    `;
    wrap.appendChild(legend);

    return wrap;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
})();
