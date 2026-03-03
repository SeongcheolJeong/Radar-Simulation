export function toFlowNode(node, idx) {
  const id = String(node && node.id ? node.id : `node_${idx + 1}`);
  const nType = String(node && node.type ? node.type : "SceneSource");
  const ui = node && typeof node.ui === "object" ? node.ui : {};
  const pos = ui && typeof ui === "object" && ui.position ? ui.position : null;
  const px = Number(pos && pos.x);
  const py = Number(pos && pos.y);
  const col = idx % 4;
  const row = Math.floor(idx / 4);
  const position = {
    x: Number.isFinite(px) ? px : 50 + col * 240,
    y: Number.isFinite(py) ? py : 50 + row * 140,
  };
  const params = node && typeof node.params === "object" ? node.params : {};
  return {
    id,
    type: "default",
    position,
    data: {
      label: `${nType}\n${id}`,
      nodeType: nType,
      params,
    },
  };
}

export function normalizeRepoPath(pathValue) {
  if (!pathValue || typeof pathValue !== "string") return null;
  const raw = pathValue.trim();
  if (!raw) return null;
  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;
  const markers = ["/Codex_test/", "/workspace/myproject/"];
  let candidate = raw;
  for (const marker of markers) {
    const idx = raw.indexOf(marker);
    if (idx >= 0) {
      candidate = raw.slice(idx + marker.length);
      break;
    }
  }
  if (candidate.startsWith("/")) {
    // Absolute filesystem paths (for example /tmp/...) are not web-served.
    // Only keep paths that were rewritten through known repo markers.
    return candidate === raw ? null : candidate;
  }
  try {
    const u = new URL(candidate, `${window.location.origin}/`);
    if (u.origin === window.location.origin) {
      return `${u.pathname}${u.search}${u.hash}`;
    }
    return u.href;
  } catch (_) {
    return `/${candidate.replace(/^\/+/, "")}`;
  }
}

export function toGraphPayload(opts) {
  const nodes = (opts.nodes || []).map((n) => ({
    id: String(n.id),
    type: String(n.data && n.data.nodeType ? n.data.nodeType : "SceneSource"),
    params: (n.data && typeof n.data.params === "object") ? n.data.params : {},
    ui: {
      position: {
        x: Number(n.position && n.position.x ? n.position.x : 0),
        y: Number(n.position && n.position.y ? n.position.y : 0),
      },
    },
  }));
  const edges = (opts.edges || []).map((e, i) => ({
    id: String(e.id || `e${i + 1}`),
    source: String(e.source || ""),
    target: String(e.target || ""),
    contract: String(e.data && e.data.contract ? e.data.contract : "generic"),
  }));
  return {
    version: "web_e2e_graph_schema_v1",
    graph_id: String(opts.graphId || "graph_lab"),
    profile: String(opts.profile || "fast_debug"),
    nodes,
    edges,
  };
}
