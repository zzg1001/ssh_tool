"""添加/编辑连接表单"""

import uuid
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Input, Label, Checkbox
from textual.screen import Screen
from textual.binding import Binding

from ..storage import storage, Connection


class ConnectionForm(Screen):
    """连接表单界面"""

    BINDINGS = [
        Binding("escape", "cancel", "取消"),
        Binding("ctrl+s", "save", "保存"),
    ]

    CSS = """
    ConnectionForm {
        align: center middle;
    }

    #form-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }

    #form-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    .form-row {
        height: 3;
        margin-bottom: 1;
    }

    .form-row Label {
        width: 12;
        height: 3;
        content-align: left middle;
    }

    .form-row Input {
        width: 1fr;
    }

    #buttons {
        height: 3;
        margin-top: 1;
        align: center middle;
    }

    #buttons Button {
        margin: 0 1;
    }

    #save-password-row {
        height: 3;
        margin-bottom: 1;
    }

    #save-password-row Label {
        width: 12;
    }
    """

    def __init__(self, connection: Connection = None):
        super().__init__()
        self.connection = connection
        self.is_edit = connection is not None

    def compose(self) -> ComposeResult:
        title = "编辑连接" if self.is_edit else "添加连接"
        with Container(id="form-container"):
            yield Static(title, id="form-title")

            with Horizontal(classes="form-row"):
                yield Label("名称:")
                yield Input(
                    placeholder="连接名称",
                    id="input-name",
                    value=self.connection.name if self.is_edit else "",
                )

            with Horizontal(classes="form-row"):
                yield Label("主机:")
                yield Input(
                    placeholder="IP 或域名",
                    id="input-host",
                    value=self.connection.host if self.is_edit else "",
                )

            with Horizontal(classes="form-row"):
                yield Label("端口:")
                yield Input(
                    placeholder="22",
                    id="input-port",
                    value=str(self.connection.port) if self.is_edit else "22",
                )

            with Horizontal(classes="form-row"):
                yield Label("用户名:")
                yield Input(
                    placeholder="用户名",
                    id="input-username",
                    value=self.connection.username if self.is_edit else "",
                )

            with Horizontal(classes="form-row"):
                yield Label("密码:")
                yield Input(
                    placeholder="留空使用密钥",
                    id="input-password",
                    password=True,
                    value=self.connection.password if self.is_edit else "",
                )

            with Horizontal(id="save-password-row"):
                yield Label("保存密码:")
                yield Checkbox(
                    "记住密码",
                    id="checkbox-save-password",
                    value=bool(self.connection.password) if self.is_edit else True,
                )

            with Horizontal(classes="form-row"):
                yield Label("密钥文件:")
                yield Input(
                    placeholder="~/.ssh/id_rsa (可选)",
                    id="input-keyfile",
                    value=self.connection.key_file if self.is_edit else "",
                )

            with Horizontal(id="buttons"):
                yield Button("保存 [Ctrl+S]", id="btn-save", variant="primary")
                yield Button("取消 [Esc]", id="btn-cancel")

    def action_cancel(self):
        """取消"""
        self.app.pop_screen()

    def action_save(self):
        """保存连接"""
        name = self.query_one("#input-name", Input).value.strip()
        host = self.query_one("#input-host", Input).value.strip()
        port_str = self.query_one("#input-port", Input).value.strip()
        username = self.query_one("#input-username", Input).value.strip()
        password = self.query_one("#input-password", Input).value
        save_password = self.query_one("#checkbox-save-password", Checkbox).value
        key_file = self.query_one("#input-keyfile", Input).value.strip()

        # 验证
        if not name:
            self.notify("请输入连接名称", severity="error")
            return
        if not host:
            self.notify("请输入主机地址", severity="error")
            return
        if not username:
            self.notify("请输入用户名", severity="error")
            return

        try:
            port = int(port_str) if port_str else 22
        except ValueError:
            self.notify("端口必须是数字", severity="error")
            return

        # 创建或更新连接
        conn = Connection(
            id=self.connection.id if self.is_edit else str(uuid.uuid4()),
            name=name,
            host=host,
            port=port,
            username=username,
            password=password if save_password else "",
            key_file=key_file,
        )

        if self.is_edit:
            storage.update_connection(conn)
            self.notify(f"已更新: {name}")
        else:
            storage.add_connection(conn)
            self.notify(f"已添加: {name}")

        # 刷新列表并返回
        self.app.pop_screen()
        main_screen = self.app.get_screen("main")
        main_screen.refresh_table()

    def on_button_pressed(self, event: Button.Pressed):
        """按钮点击"""
        if event.button.id == "btn-save":
            self.action_save()
        elif event.button.id == "btn-cancel":
            self.action_cancel()
