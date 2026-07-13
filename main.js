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
    node.querySelector(".ep-desc").textContent = episodeSummary(ep.description, 80);

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

  const comments = document.createElement("div");
  comments.className = "ep-comments";
  detailEl.appendChild(comments);
  mountGiscus(comments, `${location.origin}${episodeShareUrl(ep)}`);
}

function episodeShareUrl(ep) {
  return `${location.pathname}?ep=${ep.id}`;
}

function collapseAllExcept(exceptCard) {
  document.querySelectorAll(".episode-card").forEach((otherCard) => {
    if (otherCard === exceptCard) return;
    const otherDetail = otherCard.querySelector(".ep-detail");
    if (!otherDetail.hasAttribute("hidden")) {
      otherDetail.setAttribute("hidden", "");
      otherCard.querySelector(".ep-toggle").textContent = "展開";
    }
  });
}

function toggleEpisodeDetail(card, ep, toggleBtn) {
  const detail = card.querySelector(".ep-detail");
  const isHidden = detail.hasAttribute("hidden");
  if (isHidden) {
    collapseAllExcept(card);
    history.pushState(null, "", episodeShareUrl(ep));
    renderEpisodeDetail(detail, ep);
    detail.removeAttribute("hidden");
    toggleBtn.textContent = "收合";
  } else {
    detail.setAttribute("hidden", "");
    toggleBtn.textContent = "展開";
  }
}

function applyDeepLinkFromUrl(episodes) {
  const epId = new URLSearchParams(location.search).get("ep");
  if (!epId) return;
  const card = document.querySelector(`.episode-card[data-episode-id="${epId}"]`);
  if (!card) return;
  const ep = episodes.find((e) => e.id === epId);
  const toggleBtn = card.querySelector(".ep-toggle");
  toggleEpisodeDetail(card, ep, toggleBtn);
  card.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadEpisodes() {
  const res = await fetch("episodes.json");
  const data = await res.json();
  renderEpisodeList(data.episodes);
  applyDeepLinkFromUrl(data.episodes);
  return data.episodes;
}

if (document.getElementById("episode-list")) {
  loadEpisodes();
}

const GISCUS_CONFIG = {
  repo: "subyub/subyubperweek",
  repoId: "PASTE_FROM_GISCUS_APP",
  category: "Comments",
  categoryId: "PASTE_FROM_GISCUS_APP",
};

function mountGiscus(container, shareUrl) {
  container.innerHTML = "";
  const script = document.createElement("script");
  script.src = "https://giscus.app/client.js";
  script.async = true;
  script.crossOrigin = "anonymous";
  script.setAttribute("data-repo", GISCUS_CONFIG.repo);
  script.setAttribute("data-repo-id", GISCUS_CONFIG.repoId);
  script.setAttribute("data-category", GISCUS_CONFIG.category);
  script.setAttribute("data-category-id", GISCUS_CONFIG.categoryId);
  script.setAttribute("data-mapping", "url");
  script.setAttribute("data-strict", "0");
  script.setAttribute("data-reactions-enabled", "1");
  script.setAttribute("data-input-position", "bottom");
  script.setAttribute("data-theme", "preferred_color_scheme");
  script.setAttribute("data-lang", "zh-TW");
  container.appendChild(script);
}
