const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(API_BASE + path, {
    ...options,
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {}
    throw new Error(detail);
  }
  return response.json();
}

export const api = {
  health: () => request("/health"),
  patients: () => request("/patients"),
  twin: id => request("/patients/" + id + "/twin"),
  observations: (id, n = 96) => request("/patients/" + id + "/observations?n=" + n),
  evaluation: () => request("/evaluation"),
  reset: id => request("/simulation/reset", {
    method: "POST", body: JSON.stringify({patient_id: id}),
  }),
  step: (id, steps = 1) => request("/simulation/step", {
    method: "POST", body: JSON.stringify({patient_id: id, steps}),
  }),
  scenario: (id, scenario) => request("/patients/" + id + "/scenarios", {
    method: "POST", body: JSON.stringify({scenario}),
  }),
  retrospective: (id, n = 288) => request("/patients/" + id + "/retrospective?n=" + n),
};
