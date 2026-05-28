function showMessage(target, text, isError) {
    $(target).text(text).toggleClass("error", !!isError);
}

function showLogin() {
    $("#loginPanel").removeClass("hidden");
    $("#todoPanel").addClass("hidden");
}

function showTodos(uid, uname) {
    $("#loginPanel").addClass("hidden");
    $("#todoPanel").removeClass("hidden");
    $("#userInfo").text(uname + " (" + uid + ")");
    loadTodos();
}

function loadSession() {
    $.ajax({
        url: "/session",
        method: "GET",
        success: function (data) {
            if (data.logged_in) {
                showTodos(data.uid, data.uname);
            } else {
                showLogin();
            }
        },
        error: function () {
            showLogin();
        }
    });
}

function loadTodos() {
    $.ajax({
        url: "/todos",
        method: "GET",
        dataType: "json",
        success: function (todos) {
            var list = $("#todoList");
            list.empty();

            if (todos.length === 0) {
                list.append('<li class="empty">등록된 할 일이 없습니다.</li>');
                return;
            }

            $.each(todos, function (_, todo) {
                var item = $("<li>").addClass(todo.completed ? "done" : "");
                var title = $("<span>").text(todo.title);
                var meta = $("<small>").text(todo.datetime);
                var completeBtn = $("<button>")
                    .addClass("complete")
                    .text("완료")
                    .prop("disabled", todo.completed)
                    .on("click", function () {
                        completeTodo(todo.id);
                    });
                var deleteBtn = $("<button>")
                    .addClass("danger")
                    .text("삭제")
                    .on("click", function () {
                        deleteTodo(todo.id);
                    });

                item.append($("<div>").addClass("todo-text").append(title, meta));
                item.append($("<div>").addClass("actions").append(completeBtn, deleteBtn));
                list.append(item);
            });
        },
        error: function (xhr) {
            showMessage("#todoMessage", xhr.responseJSON?.message || "목록 조회 실패", true);
        }
    });
}

function addTodo(title) {
    $.ajax({
        url: "/todos",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ title: title }),
        success: function (data) {
            $("#todoTitle").val("");
            showMessage("#todoMessage", data.message, false);
            loadTodos();
        },
        error: function (xhr) {
            showMessage("#todoMessage", xhr.responseJSON?.message || "추가 실패", true);
        }
    });
}

function completeTodo(id) {
    $.ajax({
        url: "/todos/" + id,
        method: "PUT",
        success: function (data) {
            showMessage("#todoMessage", data.message, false);
            loadTodos();
        },
        error: function (xhr) {
            showMessage("#todoMessage", xhr.responseJSON?.message || "완료 처리 실패", true);
        }
    });
}

function deleteTodo(id) {
    $.ajax({
        url: "/todos/" + id,
        method: "DELETE",
        success: function (data) {
            showMessage("#todoMessage", data.message, false);
            loadTodos();
        },
        error: function (xhr) {
            showMessage("#todoMessage", xhr.responseJSON?.message || "삭제 실패", true);
        }
    });
}

$(function () {
    loadSession();

    $("#loginForm").on("submit", function (event) {
        event.preventDefault();
        $.ajax({
            url: "/login",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                uid: $("#uid").val(),
                upwd: $("#upwd").val()
            }),
            success: function (data) {
                showMessage("#loginMessage", data.message, false);
                loadSession();
            },
            error: function (xhr) {
                showMessage("#loginMessage", xhr.responseJSON?.message || "로그인 실패", true);
            }
        });
    });

    $("#todoForm").on("submit", function (event) {
        event.preventDefault();
        addTodo($("#todoTitle").val());
    });

    $("#logoutBtn").on("click", function () {
        $.ajax({
            url: "/logout",
            method: "POST",
            success: function () {
                showLogin();
            },
            error: function () {
                showMessage("#todoMessage", "로그아웃 실패", true);
            }
        });
    });
});