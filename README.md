# exam1 Todo API

Flask + SQLite + jQuery로 만든 할 일 관리 API 및 웹 UI입니다.  
SQLite에는 회원과 할 일 데이터를 저장하고, MySQL 서버가 실행 중이면 기능 수행 중 발생한 SQL 쿼리를 `todo_log.query_log` 테이블에 기록합니다.

## 실행 방법

```bash
git clone <저장소 주소>
cd exam1
pip install -r requirements.txt
python app.py
```

브라우저에서 아래 주소로 접속합니다.

```text
http://localhost:5000
```

## 기본 로그인 정보

```text
아이디: admin
비밀번호: 1234
```

앱 최초 실행 시 `todo.db` 파일이 자동 생성되고, 위 기본 회원도 자동 등록됩니다.

## 주요 파일

```text
app.py
todo.db
templates/index.html
static/script.js
static/style.css
mysql_schema.sql
requirements.txt
README.md
```

## SQLite 테이블

```sql
CREATE TABLE IF NOT EXISTS member (
    idx INTEGER PRIMARY KEY AUTOINCREMENT,
    uname TEXT NOT NULL,
    uid TEXT NOT NULL UNIQUE,
    upwd TEXT NOT NULL,
    datetime TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS todolist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    uid TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    datetime TEXT NOT NULL
);
```

## MySQL 로그 테이블

앱은 기본값으로 DB VM `192.168.45.61:3306`, 사용자 `todoapp`, 비밀번호 `123`, DB명 `todo_log`에 접속을 시도합니다. MySQL 접속 정보가 다르면 환경변수로 지정할 수 있습니다.

```bash
set MYSQL_HOST=192.168.45.61
set MYSQL_PORT=3306
set MYSQL_USER=todoapp
set MYSQL_PASSWORD=123
set MYSQL_DB=todo_log
python app.py
```

DDL은 `mysql_schema.sql`에도 포함되어 있으며, 앱 시작 시 자동 생성도 시도합니다.

```sql
CREATE TABLE IF NOT EXISTS query_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    `sql` TEXT NOT NULL,
    dateime DATETIME NOT NULL
);
```

로그 확인:

```sql
SELECT type, `sql`, dateime
FROM todo_log.query_log
ORDER BY id DESC;
```

MySQL 서버가 꺼져 있어도 Flask, SQLite, 웹 UI 기능은 실행됩니다. 서버가 켜져 있고 접속 정보가 맞으면 쿼리 로그가 자동 기록됩니다.

## API 테스트

로그인 후 세션 쿠키를 유지해야 `/todos` API를 사용할 수 있습니다. Postman에서는 같은 탭에서 아래 순서대로 호출하면 됩니다.

### 로그인

```http
POST /login
Content-Type: application/json

{
  "uid": "admin",
  "upwd": "1234"
}
```

### 할 일 조회

```http
GET /todos
```

### 할 일 추가

```http
POST /todos
Content-Type: application/json

{
  "title": "Flask 과제 제출"
}
```

### 완료 처리

```http
PUT /todos/1
```

### 삭제

```http
DELETE /todos/1
```

## 기능 확인 방법

1. `python app.py` 실행
2. `http://localhost:5000` 접속
3. `admin / 1234`로 로그인
4. 할 일 추가, 조회, 완료, 삭제 버튼 확인
5. MySQL 사용 시 `todo_log.query_log`에서 `select`, `insert`, `update`, `delete` 로그 확인