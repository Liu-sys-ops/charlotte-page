async function demoFetch() {
  const statusEl = document.getElementById("fetchStatus");
  const start = performance.now();
  statusEl.textContent = "请求中...";

  try {
    const res = await fetch("data.json", { cache: "no-store" });
    const data = await res.json();
    const ms = Math.round(performance.now() - start);
    statusEl.textContent = `GET ${res.status} ${res.statusText} · ${ms} ms · ${data.project}`;
    console.log("fetch:", { method: "GET", status: res.status, ms, data });
  } catch (err) {
    const ms = Math.round(performance.now() - start);
    statusEl.textContent = `fetch 失败 · ${ms} ms`;
    console.error(err);
  }
}

document.getElementById("fetchBtn").addEventListener("click", demoFetch);
window.demoFetch = demoFetch;
