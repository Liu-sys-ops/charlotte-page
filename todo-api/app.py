# -*- coding: utf-8 -*-
"""
待办清单 REST API —— Flask + SQLite

运行：
    pip install -r requirements.txt
    python app.py

接口：
    GET    /api/todos
    POST   /api/todos
    PUT    /api/todos/<id>
    DELETE /api/todos/<id>
"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("TODO_DB_PATH", BASE_DIR / "todos.db"))

app = Flask(__name__)
app.json.ensure_ascii = False
app.config["PROPAGATE_EXCEPTIONS"] = False


# ---------------------------------------------------------------------------
# 数据库
# ---------------------------------------------------------------------------
def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT    NOT NULL,
                done       INTEGER NOT NULL DEFAULT 0,
                created_at TEXT    NOT NULL,
                updated_at TEXT    NOT NULL
            )
            """
        )
        db.commit()


def row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# ---------------------------------------------------------------------------
# 统一返回格式
# ---------------------------------------------------------------------------
def ok(data=None, msg: str = "ok"):
    return jsonify({"code": 0, "data": data, "msg": msg})


def fail(code: int, msg: str, http_status: int = 400):
    return jsonify({"code": code, "data": None, "msg": msg}), http_status


# ---------------------------------------------------------------------------
# 参数校验
# ---------------------------------------------------------------------------
def read_json_body():
    if not request.is_json:
        return None, "请求体必须是 application/json"
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, "JSON 格式不正确，必须是对象"
    return body, None


def validate_title(value):
    if value is None:
        return None, "缺少字段 title"
    if not isinstance(value, str):
        return None, "title 必须是字符串"
    value = value.strip()
    if not value:
        return None, "title 不能为空"
    if len(value) > 100:
        return None, "title 长度不能超过 100 个字符"
    return value, None


def validate_done(value):
    if type(value) is not bool:
        return None, "done 必须是布尔值 true 或 false"
    return value, None


# ---------------------------------------------------------------------------
# 接口
# ---------------------------------------------------------------------------
@app.get("/api/todos")
def list_todos():
    rows = get_db().execute("SELECT * FROM todos ORDER BY id ASC").fetchall()
    return ok([row_to_dict(row) for row in rows])


@app.post("/api/todos")
def create_todo():
    body, error = read_json_body()
    if error:
        return fail(400, error)

    title, error = validate_title(body.get("title"))
    if error:
        return fail(400, error)

    if "done" in body:
        done, error = validate_done(body["done"])
        if error:
            return fail(400, error)
    else:
        done = False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db = get_db()
    cursor = db.execute(
        "INSERT INTO todos (title, done, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (title, int(done), now, now),
    )
    db.commit()

    row = db.execute("SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return ok(row_to_dict(row), "创建成功")


@app.put("/api/todos/<int:todo_id>")
def update_todo(todo_id: int):
    body, error = read_json_body()
    if error:
        return fail(400, error)

    updates: dict[str, object] = {}
    if "title" in body:
        title, error = validate_title(body["title"])
        if error:
            return fail(400, error)
        updates["title"] = title

    if "done" in body:
        done, error = validate_done(body["done"])
        if error:
            return fail(400, error)
        updates["done"] = int(done)

    if not updates:
        return fail(400, "至少提供 title 或 done 中的一个字段")

    db = get_db()
    row = db.execute("SELECT id FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        return fail(404, "任务不存在", 404)

    updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    columns = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [todo_id]
    db.execute(f"UPDATE todos SET {columns} WHERE id = ?", values)
    db.commit()

    updated = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return ok(row_to_dict(updated), "更新成功")


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id: int):
    db = get_db()
    row = db.execute("SELECT id FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        return fail(404, "任务不存在", 404)

    db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    return ok({"id": todo_id}, "删除成功")


# ---------------------------------------------------------------------------
# 全局错误处理：任何异常都返回 JSON
# ---------------------------------------------------------------------------
@app.errorhandler(HTTPException)
def handle_http_exception(exc: HTTPException):
    messages = {404: "接口不存在", 405: "请求方法不允许"}
    message = messages.get(exc.code, exc.description or "请求错误")
    return fail(exc.code or 500, message, exc.code or 500)


@app.errorhandler(Exception)
def handle_exception(exc: Exception):
    app.logger.error("Unhandled exception: %s", exc)
    app.logger.error(traceback.format_exc())
    return fail(500, "服务器内部错误", 500)


# ---------------------------------------------------------------------------
# CORS：方便本地前端/调试页面直接调用
# ---------------------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
