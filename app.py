import os
import sqlite3
from datetime import datetime
from functools import wraps

import pymysql
from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "todo.db")

MYSQL_HOST = os.getenv("MYSQL_HOST", "192.168.45.61")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "todoapp")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123")
MYSQL_DB = os.getenv("MYSQL_DB", "todo_log")

DEFAULT_UID = "admin"
DEFAULT_PASSWORD = "1234"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "exam1-local-secret-key")


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def query_type(sql):
    return sql.strip().split(None, 1)[0].lower()


def format_sql(sql, params=None):
    if not params:
        return sql

    values = params if isinstance(params, (list, tuple)) else tuple(params)
    result = sql
    for value in values:
        if value is None:
            rendered = "NULL"
        elif isinstance(value, (int, float)):
            rendered = str(value)
        else:
            rendered = "'" + str(value).replace("'", "''") + "'"
        result = result.replace("?", rendered, 1)
    return result


def get_sqlite():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_mysql():
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=2,
        )
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
            )
            cur.execute(f"USE `{MYSQL_DB}`")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS query_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    type VARCHAR(20) NOT NULL,
                    `sql` TEXT NOT NULL,
                    dateime DATETIME NOT NULL
                )
                """
            )
        conn.close()
        return True
    except Exception as exc:
        print(f"[MySQL log disabled] {exc}")
        return False


MYSQL_READY = init_mysql()


def log_query(sql, params=None):
    if not MYSQL_READY:
        return

    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=2,
        )
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO query_log (type, `sql`, dateime) VALUES (%s, %s, %s)",
                (query_type(sql), format_sql(sql, params), now_text()),
            )
        conn.close()
    except Exception as exc:
        print(f"[MySQL log failed] {exc}")


def execute_sql(sql, params=None, fetchone=False, fetchall=False):
    log_query(sql, params)
    conn = get_sqlite()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    data = None
    if fetchone:
        data = cur.fetchone()
    elif fetchall:
        data = cur.fetchall()
    conn.commit()
    conn.close()
    return data


def init_sqlite():
    conn = get_sqlite()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS member (
            idx INTEGER PRIMARY KEY AUTOINCREMENT,
            uname TEXT NOT NULL,
            uid TEXT NOT NULL UNIQUE,
            upwd TEXT NOT NULL,
            datetime TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS todolist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            uid TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            datetime TEXT NOT NULL
        )
        """
    )
    cur.execute("SELECT idx FROM member WHERE uid = ?", (DEFAULT_UID,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO member (uname, uid, upwd, datetime) VALUES (?, ?, ?, ?)",
            (
                "Admin",
                DEFAULT_UID,
                generate_password_hash(DEFAULT_PASSWORD),
                now_text(),
            ),
        )
    conn.commit()
    conn.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "uid" not in session:
            return jsonify({"ok": False, "message": "로그인이 필요합니다."}), 401
        return view(*args, **kwargs)

    return wrapped


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/session")
def current_session():
    if "uid" not in session:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "uid": session["uid"], "uname": session["uname"]})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    uid = (data.get("uid") or "").strip()
    upwd = data.get("upwd") or ""

    member = execute_sql(
        "SELECT idx, uname, uid, upwd FROM member WHERE uid = ?",
        (uid,),
        fetchone=True,
    )
    if member is None or not check_password_hash(member["upwd"], upwd):
        return jsonify({"ok": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401

    session["uid"] = member["uid"]
    session["uname"] = member["uname"]
    return jsonify({"ok": True, "message": "로그인되었습니다.", "uid": member["uid"]})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True, "message": "로그아웃되었습니다."})


@app.route("/todos", methods=["GET"])
@login_required
def get_todos():
    rows = execute_sql(
        """
        SELECT id, title, uid, completed, datetime
        FROM todolist
        WHERE uid = ?
        ORDER BY id DESC
        """,
        (session["uid"],),
        fetchall=True,
    )
    todos = [
        {
            "id": row["id"],
            "title": row["title"],
            "uid": row["uid"],
            "completed": bool(row["completed"]),
            "datetime": row["datetime"],
        }
        for row in rows
    ]
    return jsonify(todos)


@app.route("/todos", methods=["POST"])
@login_required
def add_todo():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "message": "할 일을 입력하세요."}), 400

    execute_sql(
        "INSERT INTO todolist (title, uid, completed, datetime) VALUES (?, ?, ?, ?)",
        (title, session["uid"], 0, now_text()),
    )
    return jsonify({"ok": True, "message": "할 일이 추가되었습니다."}), 201


@app.route("/todos/<int:todo_id>", methods=["PUT"])
@login_required
def complete_todo(todo_id):
    todo = execute_sql(
        "SELECT id FROM todolist WHERE id = ? AND uid = ?",
        (todo_id, session["uid"]),
        fetchone=True,
    )
    if todo is None:
        return jsonify({"ok": False, "message": "할 일을 찾을 수 없습니다."}), 404

    execute_sql(
        "UPDATE todolist SET completed = 1 WHERE id = ? AND uid = ?",
        (todo_id, session["uid"]),
    )
    return jsonify({"ok": True, "message": "완료 처리되었습니다."})


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
@login_required
def delete_todo(todo_id):
    todo = execute_sql(
        "SELECT id FROM todolist WHERE id = ? AND uid = ?",
        (todo_id, session["uid"]),
        fetchone=True,
    )
    if todo is None:
        return jsonify({"ok": False, "message": "할 일을 찾을 수 없습니다."}), 404

    execute_sql("DELETE FROM todolist WHERE id = ? AND uid = ?", (todo_id, session["uid"]))
    return jsonify({"ok": True, "message": "삭제되었습니다."})


if __name__ == "__main__":
    init_sqlite()
    app.run(host="0.0.0.0", port=5000, debug=False)