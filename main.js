function episodeSummary(text, maxLength) {
  const singleLine = text.split("\n").filter(Boolean)[0] || "";
  return singleLine.length > maxLength ? singleLine.slice(0, maxLength) + "…" : singleLine;
}

function episodeLabel(ep) {
  const seasonPart = ep.season ? `S${ep.season} · ` : "";
  const episodePart = ep.episodeNumber != null ? `EP${ep.episodeNumber} · ` : "";
  return `${seasonPart}${episodePart}${ep.title}`;
}

function renderEpisodeList(episodes) {
  const container = document.getElementById("episode-list");
  const template = document.getElementById("episode-template");
  container.innerHTML = "";

  episodes.forEach((ep) => {
    const node = template.content.cloneNode(true);
    node.querySelector(".ep-title").textContent = episodeLabel(ep);
    node.querySelector(".ep-meta").textContent = ep.pubDate;
    node.querySelector(".ep-desc").textContent = episodeSummary(ep.summary || ep.description, 80);

    const card = node.querySelector(".episode-card");
    card.dataset.episodeId = ep.id;

    const toggleBtn = node.querySelector(".ep-toggle");
    toggleBtn.addEventListener("click", () => toggleEpisodeDetail(card, ep, toggleBtn));

    container.appendChild(node);
  });
}

function platformLinkHtml(label, url) {
  return url ? `<a href="${url}" target="_blank" rel="noopener">${label}</a>` : "";
}

function renderEpisodeDetail(detailEl, ep) {
  if (detailEl.dataset.rendered === "true") return;
  detailEl.dataset.rendered = "true";

  const audio = document.createElement("audio");
  audio.className = "ep-audio";
  audio.controls = true;
  audio.src = ep.audioUrl;
  detailEl.appendChild(audio);

  if (ep.patreonPost) {
    const patreonLink = document.createElement("a");
    patreonLink.className = "ep-patreon-post";
    patreonLink.href = ep.patreonPost.url;
    patreonLink.target = "_blank";
    patreonLink.rel = "noopener";
    patreonLink.textContent = `本集會員限定內容：《${ep.patreonPost.title}》 →`;
    detailEl.appendChild(patreonLink);
  }

  const siteCommentsHeading = document.createElement("h4");
  siteCommentsHeading.textContent = "留言";
  detailEl.appendChild(siteCommentsHeading);

  const siteComments = document.createElement("div");
  siteComments.className = "ep-site-comments";
  detailEl.appendChild(siteComments);
  mountSiteComments(siteComments, ep.id);

  const desc = document.createElement("p");
  desc.className = "ep-desc-full";
  desc.style.whiteSpace = "pre-line";
  desc.textContent = ep.description;
  detailEl.appendChild(desc);

  const links = document.createElement("div");
  links.className = "ep-links";
  links.innerHTML = [
    platformLinkHtml("SoundOn 收聽", ep.soundonUrl),
    platformLinkHtml("Apple Podcasts", ep.appleUrl),
    platformLinkHtml("Spotify", ep.spotifyUrl),
  ].join("");
  detailEl.appendChild(links);
}

function canonicalPathname() {
  return location.pathname.endsWith("/") ? `${location.pathname}index.html` : location.pathname;
}

function episodeShareUrl(ep) {
  return `${canonicalPathname()}?ep=${ep.id}`;
}

function resetEpisodeDetail(detailEl) {
  const siteComments = detailEl.querySelector(".ep-site-comments");
  if (siteComments) unmountSiteComments(siteComments);
  detailEl.innerHTML = "";
  detailEl.dataset.rendered = "false";
}

function collapseAllExcept(exceptCard) {
  document.querySelectorAll(".episode-card").forEach((otherCard) => {
    if (otherCard === exceptCard) return;
    const otherDetail = otherCard.querySelector(".ep-detail");
    if (!otherDetail.hasAttribute("hidden")) {
      otherDetail.setAttribute("hidden", "");
      resetEpisodeDetail(otherDetail);
      otherCard.querySelector(".ep-toggle").textContent = "展開";
    }
  });
}

function expandEpisode(card, ep, toggleBtn) {
  const detail = card.querySelector(".ep-detail");
  collapseAllExcept(card);
  history.pushState(null, "", episodeShareUrl(ep));
  renderEpisodeDetail(detail, ep);
  detail.removeAttribute("hidden");
  toggleBtn.textContent = "收合";
}

function toggleEpisodeDetail(card, ep, toggleBtn) {
  const detail = card.querySelector(".ep-detail");
  const isHidden = detail.hasAttribute("hidden");
  if (isHidden) {
    expandEpisode(card, ep, toggleBtn);
  } else {
    detail.setAttribute("hidden", "");
    resetEpisodeDetail(detail);
    toggleBtn.textContent = "展開";
  }
}

function populateEpisodeJump(episodes) {
  const select = document.getElementById("episode-jump");
  if (!select) return;
  episodes.forEach((ep) => {
    const option = document.createElement("option");
    option.value = ep.id;
    option.textContent = episodeLabel(ep);
    select.appendChild(option);
  });
}

function jumpToEpisodeComments(episodeId, episodes) {
  const card = document.querySelector(`.episode-card[data-episode-id="${episodeId}"]`);
  const ep = episodes.find((e) => e.id === episodeId);
  if (!card || !ep) return;

  const detail = card.querySelector(".ep-detail");
  if (detail.hasAttribute("hidden")) {
    const toggleBtn = card.querySelector(".ep-toggle");
    expandEpisode(card, ep, toggleBtn);
  }

  detail.querySelector(".ep-site-comments").scrollIntoView({ behavior: "smooth", block: "start" });
}

function applyDeepLinkFromUrl(episodes) {
  const epId = new URLSearchParams(location.search).get("ep");
  if (!epId) return;
  const card = document.querySelector(`.episode-card[data-episode-id="${epId}"]`);
  if (!card) return;
  const ep = episodes.find((e) => e.id === epId);
  if (!ep) return;
  const toggleBtn = card.querySelector(".ep-toggle");
  toggleEpisodeDetail(card, ep, toggleBtn);
  card.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadEpisodes() {
  const res = await fetch("episodes.json");
  const data = await res.json();
  renderEpisodeList(data.episodes);
  populateEpisodeJump(data.episodes);
  applyDeepLinkFromUrl(data.episodes);
  return data.episodes;
}

async function loadPatreonBanner() {
  const banner = document.getElementById("patreon-banner");
  if (!banner) return;

  try {
    const res = await fetch("patreon-latest.json");
    if (!res.ok) return;
    const data = await res.json();
    if (!data || !data.title || !data.url) return;

    const link = document.createElement("a");
    link.href = data.url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = `🎧 本週 Patreon 會員內容：《${data.title}》 立即收聽 →`;
    banner.appendChild(link);
    banner.removeAttribute("hidden");
  } catch (err) {}
}

if (document.getElementById("episode-list")) {
  loadPatreonBanner();
  loadEpisodes().then((episodes) => {
    const jumpSelect = document.getElementById("episode-jump");
    jumpSelect.addEventListener("change", (event) => {
      const episodeId = event.target.value;
      jumpSelect.value = "";
      if (!episodeId) return;
      jumpToEpisodeComments(episodeId, episodes);
    });
  });
}

const TURNSTILE_SITE_KEY = "0x4AAAAAAD1yRjYHvUH53sdL";

function renderCommentItem(comment) {
  const item = document.createElement("div");
  item.className = "site-comment-item";

  const meta = document.createElement("p");
  meta.className = "site-comment-meta";
  meta.textContent = `${comment.nickname || "匿名"} · ${comment.created_at}`;

  const body = document.createElement("p");
  body.className = "site-comment-body";
  body.textContent = comment.body;

  item.appendChild(meta);
  item.appendChild(body);
  return item;
}

async function fetchSiteComments(episodeId) {
  const res = await fetch(`/api/comments?episodeId=${encodeURIComponent(episodeId)}`);
  if (!res.ok) throw new Error("留言載入失敗");
  return res.json();
}

async function submitSiteComment(episodeId, nickname, body, turnstileToken) {
  const res = await fetch("/api/comments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ episodeId, nickname, body, turnstileToken }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "留言送出失敗");
  }
  return res.json();
}

function mountSiteComments(container, episodeId) {
  container.innerHTML = "";

  const list = document.createElement("div");
  list.className = "site-comment-list";
  list.textContent = "載入中…";
  container.appendChild(list);

  const form = document.createElement("form");
  form.className = "site-comment-form";

  const nicknameInput = document.createElement("input");
  nicknameInput.type = "text";
  nicknameInput.placeholder = "暱稱（可留空）";
  nicknameInput.maxLength = 50;

  const bodyInput = document.createElement("textarea");
  bodyInput.placeholder = "想講咩都得";
  bodyInput.maxLength = 1000;
  bodyInput.required = true;

  const turnstileEl = document.createElement("div");

  const submitBtn = document.createElement("button");
  submitBtn.type = "submit";
  submitBtn.textContent = "送出";

  const errorEl = document.createElement("p");
  errorEl.className = "site-comment-error";
  errorEl.hidden = true;

  form.appendChild(nicknameInput);
  form.appendChild(bodyInput);
  form.appendChild(turnstileEl);
  form.appendChild(submitBtn);
  form.appendChild(errorEl);
  container.appendChild(form);

  let widgetId = null;

  function renderTurnstileWidget() {
    if (!turnstileEl.isConnected) return;
    if (window.turnstile) {
      widgetId = window.turnstile.render(turnstileEl, { sitekey: TURNSTILE_SITE_KEY });
      container.dataset.turnstileWidgetId = String(widgetId);
    } else {
      setTimeout(renderTurnstileWidget, 100);
    }
  }
  renderTurnstileWidget();

  fetchSiteComments(episodeId)
    .then((comments) => {
      list.innerHTML = "";
      if (comments.length === 0) {
        list.textContent = "仲未有留言，做第一個留言嘅人啦。";
        return;
      }
      comments.forEach((comment) => list.appendChild(renderCommentItem(comment)));
    })
    .catch(() => {
      list.textContent = "留言載入失敗，請重新整理再試。";
    });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.hidden = true;

    const token =
      window.turnstile && widgetId != null ? window.turnstile.getResponse(widgetId) : "";

    try {
      const newComment = await submitSiteComment(
        episodeId,
        nicknameInput.value,
        bodyInput.value,
        token
      );
      if (list.querySelector(".site-comment-item") === null) {
        list.innerHTML = "";
      }
      list.insertBefore(renderCommentItem(newComment), list.firstChild);
      bodyInput.value = "";
      nicknameInput.value = "";
      if (window.turnstile && widgetId != null) window.turnstile.reset(widgetId);
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.hidden = false;
    }
  });
}

function unmountSiteComments(container) {
  const widgetId = container.dataset.turnstileWidgetId;
  if (window.turnstile && widgetId) {
    window.turnstile.remove(widgetId);
  }
}
