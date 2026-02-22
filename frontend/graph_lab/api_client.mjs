function normalizeApiBase(apiBase) {
  return String(apiBase || "").replace(/\/+$/, "");
}

async function parseResponsePayload(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch (_) {
    return { _raw_text: text };
  }
}

function extractErrorMessage(payload) {
  if (!payload || typeof payload !== "object") return "";
  const raw = payload.error || payload.message || payload.detail || "";
  return String(raw || "").trim();
}

async function requestJson(apiBase, path, init) {
  const url = `${normalizeApiBase(apiBase)}${path}`;
  const response = await fetch(url, init);
  const payload = await parseResponsePayload(response);
  return {
    ok: Boolean(response.ok),
    status: Number(response.status),
    payload,
  };
}

function throwRequestError(path, result) {
  const tail = extractErrorMessage(result && result.payload);
  const suffix = tail ? `: ${tail}` : "";
  throw new Error(`${path} request failed (${Number(result && result.status)})${suffix}`);
}

async function requestJsonOrThrow(apiBase, path, init) {
  const result = await requestJson(apiBase, path, init);
  if (!result.ok) {
    throwRequestError(path, result);
  }
  return result.payload || {};
}

export async function getGraphTemplates(apiBase) {
  return requestJsonOrThrow(apiBase, "/api/graph/templates");
}

export async function validateGraphContract(apiBase, graphPayload) {
  return requestJsonOrThrow(apiBase, "/api/graph/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(graphPayload),
  });
}

export async function runGraph(apiBase, runPayload, runAsync) {
  return requestJsonOrThrow(apiBase, `/api/graph/runs?async=${runAsync ? 1 : 0}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(runPayload),
  });
}

export async function getGraphRun(apiBase, graphRunId) {
  const rid = encodeURIComponent(String(graphRunId || ""));
  return requestJsonOrThrow(apiBase, `/api/graph/runs/${rid}`);
}

export async function getGraphRunMaybe(apiBase, graphRunId) {
  const rid = encodeURIComponent(String(graphRunId || ""));
  return requestJson(apiBase, `/api/graph/runs/${rid}`);
}

export async function getGraphRunSummaryMaybe(apiBase, graphRunId) {
  const rid = encodeURIComponent(String(graphRunId || ""));
  return requestJson(apiBase, `/api/graph/runs/${rid}/summary`);
}

export async function cancelGraphRun(apiBase, graphRunId, reason) {
  const rid = encodeURIComponent(String(graphRunId || ""));
  return requestJsonOrThrow(apiBase, `/api/graph/runs/${rid}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: String(reason || "graph_lab_manual_cancel") }),
  });
}

export async function retryGraphRun(apiBase, graphRunId, runAsync, retryPayload) {
  const rid = encodeURIComponent(String(graphRunId || ""));
  return requestJsonOrThrow(apiBase, `/api/graph/runs/${rid}/retry?async=${runAsync ? 1 : 0}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(retryPayload),
  });
}

export async function createBaseline(apiBase, baselinePayload) {
  return requestJsonOrThrow(apiBase, "/api/baselines", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(baselinePayload),
  });
}

export async function evaluatePolicyGate(apiBase, policyPayload) {
  return requestJsonOrThrow(apiBase, "/api/compare/policy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policyPayload),
  });
}
