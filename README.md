# exam1 Todo API

Flask, SQLite, jQuery로 만든 간단한 할 일 관리 API와 웹 UI입니다.  
할 일 데이터는 SQLite 파일(`todo.db`)에 저장하고, 앱에서 실행되는 SQL 쿼리는 별도 MySQL 서버의 `todo_log.query_log` 테이블에 기록합니다.

## DB 로그 IP 설정

MySQL 서버는 Web VM과 분리된 DB VM에서 실행됩니다. DB VM IP는 VirtualBox 네트워크 구성이나 실행 환경에 따라 달라질 수 있습니다.

현재 코드의 기본 MySQL 주소는 `192.168.45.61:3306`입니다. DB VM IP가 다르면 실행 전에 `MYSQL_HOST`를 현재 DB VM IP로 바꿔야 MySQL 쿼리 로그가 기록됩니다.

Linux/macOS:

```bash
export MYSQL_HOST=<현재 DB VM IP>
export MYSQL_PORT=3306
export MYSQL_USER=todoapp
export MYSQL_PASSWORD=123
export MYSQL_DB=todo_log
python app.py
```

Windows PowerShell:

```powershell
$env:MYSQL_HOST="<현재 DB VM IP>"
python app.py
```

MySQL 연결에 실패해도 Flask, SQLite, 웹 화면은 실행됩니다. 다만 이 경우 MySQL 쿼리 로그만 남지 않습니다.

## 실행 방법

```bash
git clone https://github.com/BlakeEdenParker/exam1.git
cd exam1
pip install -r requirements.txt
python app.py
```

브라우저에서 접속합니다.

```text
http://localhost:5000
```

## 로그인 정보

```text
아이디: admin
비밀번호: 1234
```

첫 실행 시 `todo.db`가 자동 생성되고 기본 계정도 함께 생성됩니다.

## 주요 기능

- 로그인 / 로그아웃
- 할 일 목록 조회
- 할 일 추가
- 할 일 완료 처리
- 할 일 삭제
- SQLite 자동 초기화
- MySQL 쿼리 로그 기록

## 프로젝트 구조

```text
app.py
mysql_schema.sql
requirements.txt
README.md
templates/
  index.html
static/
  script.js
  style.css
```

`todo.db`는 실행 중 자동 생성되는 로컬 DB 파일이라 저장소에는 포함하지 않습니다.

## API

로그인 후 세션 쿠키를 유지해야 `/todos` API를 사용할 수 있습니다.

### 로그인

```http
POST /login
Content-Type: application/json

{
  "uid": "admin",
  "upwd": "1234"
}
```

### 로그아웃

```http
POST /logout
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

## SQLite 스키마

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

## MySQL 로그 스키마

앱 시작 시 아래 DB와 테이블 생성을 시도합니다. 같은 DDL은 `mysql_schema.sql`에도 들어 있습니다.

```sql
CREATE DATABASE IF NOT EXISTS todo_log
DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE todo_log;

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

## MySQL 접속 기본값

```text
host: 192.168.45.61
port: 3306
user: todoapp
password: 123
database: todo_log
```

DB VM에서 원격 접속을 허용하려면 MySQL 설정의 `bind-address`가 외부 접속 가능한 값이어야 합니다.

```ini
bind-address = 0.0.0.0
```

## 확인 방법

1. `python app.py` 실행
2. `http://localhost:5000` 접속
3. `admin / 1234`로 로그인
4. 할 일 추가, 조회, 완료, 삭제 버튼 확인
5. DB VM에서 `todo_log.query_log`에 `select`, `insert`, `update`, `delete` 로그가 들어오는지 확인

## 문제 해결

| 증상 | 확인할 내용 |
|---|---|
| `[MySQL log disabled]` 출력 | `MYSQL_HOST`, MySQL 계정, DB VM 네트워크 연결 확인 |
| `Connection refused` | MySQL 서비스 실행 여부, `bind-address`, 3306 포트 확인 |
| `Access denied for user` | `todoapp` 계정 비밀번호와 권한 확인 |
| 화면은 열리지만 로그가 없음 | SQLite 기능은 정상이며 MySQL 접속 정보만 다시 확인 |
