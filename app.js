(function () {
  "use strict";

  var baseUrl = (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL || "").replace(/\/+$/, "");
  var listEl = document.getElementById("todoList");
  var stateEl = document.getElementById("todoState");
  var stateText = document.getElementById("todoStateText");
  var retryBtn = document.getElementById("todoRetry");
  var form = document.getElementById("todoForm");
  var input = document.getElementById("todoInput");
  var addBtn = document.getElementById("todoAddBtn");
  var messageEl = document.getElementById("todoMessage");

  function sleep(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  function showMessage(text, isError) {
    messageEl.textContent = text || "";
    messageEl.className = "todo-message" + (isError ? " error" : "");
  }

  function showState(kind, text) {
    stateEl.hidden = false;
    stateEl.className = "todo-state " + kind;
    stateText.textContent = text;
    retryBtn.hidden = kind !== "error";
    listEl.hidden = true;
  }

  function showList() {
    stateEl.hidden = true;
    listEl.hidden = false;
  }

  function explainError(err) {
    if (err && err.name === "TypeError") {
      return "网络请求失败：后端未启动、地址写错或 CORS 未放行";
    }
    return err && err.message ? err.message : "未知错误";
  }

  async function api(path, options) {
    var res = await fetch(baseUrl + path, Object.assign({ cache: "no-store" }, options || {}));
    var payload = null;
    try {
      payload = await res.json();
    } catch (err) {
      payload = null;
    }
    if (!res.ok || !payload || payload.code !== 0) {
      throw new Error((payload && payload.msg) || ("HTTP " + res.status));
    }
    return payload.data;
  }

  function renderTodos(todos) {
    listEl.innerHTML = "";
    todos.forEach(function (todo) {
      var li = document.createElement("li");
      li.className = "todo-item";

      var title = document.createElement("span");
      title.className = "todo-title";
      title.textContent = todo.title;

      var del = document.createElement("button");
      del.type = "button";
      del.className = "todo-delete";
      del.textContent = "删除";
      del.addEventListener("click", function () {
        removeTodo(todo.id, del);
      });

      li.appendChild(title);
      li.appendChild(del);
      listEl.appendChild(li);
    });
  }

  async function loadTodos() {
    showMessage("");
    showState("loading", "加载中...");
    var started = Date.now();
    try {
      var todos = await api("/api/todos");
      var remain = 300 - (Date.now() - started);
      if (remain > 0) await sleep(remain);

      if (!todos.length) {
        showState("empty", "暂无任务，先添加一条吧");
      } else {
        renderTodos(todos);
        showList();
      }
    } catch (err) {
      showState("error", "加载失败：" + explainError(err));
      console.error(err);
    }
  }

  async function removeTodo(id, button) {
    button.disabled = true;
    button.textContent = "删除中";
    try {
      await api("/api/todos/" + encodeURIComponent(id), { method: "DELETE" });
      showMessage("已删除");
      await loadTodos();
    } catch (err) {
      button.disabled = false;
      button.textContent = "删除";
      showMessage("删除失败：" + explainError(err), true);
    }
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    var title = input.value.trim();
    if (!title) {
      showMessage("请输入任务内容", true);
      input.focus();
      return;
    }

    addBtn.disabled = true;
    addBtn.textContent = "添加中...";
    try {
      await api("/api/todos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title, done: false })
      });
      input.value = "";
      showMessage("已添加");
      await loadTodos();
    } catch (err) {
      showMessage("添加失败：" + explainError(err), true);
    } finally {
      addBtn.disabled = false;
      addBtn.textContent = "新增";
    }
  });

  retryBtn.addEventListener("click", loadTodos);

  if (!baseUrl) {
    showState("error", "加载失败：没有配置 API_BASE_URL，请检查 config.js");
    return;
  }

  if (location.hash === "#todo") {
    var listBtn = document.querySelector('.tab-btn[data-tab="list"]');
    if (listBtn) listBtn.click();
  }

  loadTodos();
})();
