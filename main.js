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

function toggleEpisodeDetail(card, ep, toggleBtn) {
  const detail = card.querySelector(".ep-detail");
  const isHidden = detail.hasAttribute("hidden");
  if (isHidden) {
    detail.removeAttribute("hidden");
    toggleBtn.textContent = "收合";
  } else {
    detail.setAttribute("hidden", "");
    toggleBtn.textContent = "展開";
  }
}

async function loadEpisodes() {
  const res = await fetch("episodes.json");
  const data = await res.json();
  renderEpisodeList(data.episodes);
  return data.episodes;
}

if (document.getElementById("episode-list")) {
  loadEpisodes();
}
