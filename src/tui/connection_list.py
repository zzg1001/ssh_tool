"""连接列表界面"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Button, DataTable
from textual.screen import Screen
from textual.binding import Binding

from ..storage import storage, Connection


class ConnectionList(Screen):
    """连接列表界面"""

    BINDINGS = [
        Binding("a", "add", "添加"),
        Binding("e", "edit", "编辑"),
        Binding("d", "delete", "删除"),
        Binding("enter", "connect", "连接"),
        Binding("q", "quit", "退出"),
    ]

    CSS = """
    ConnectionList {
        layout: vertical;
    }

    #title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $primary;
        color: $text;
        text-style: bold;
    }

    #table-container {
        height: 1fr;
        padding: 1;
    }

    #buttons {
        dock: bottom;
        height: 3;
        layout: horizontal;
        align: center middle;
        padding: 0 1;
    }

    #buttons Button {
        margin: 0 1;
    }

    #help {
        dock: bottom;
        height: 1;
        content-align: center middle;
        background: $surface;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("zzgShell - 连接管理", id="title")
        with Container(id="table-container"):
            yield DataTable(id="conn-table")
        with Container(id="buttons"):
            yield Button("添加 [A]", id="btn-add", variant="primary")
            yield Button("编辑 [E]", id="btn-edit")
            yield Button("删除 [D]", id="btn-delete", variant="error")
            yield Button("连接 [Enter]", id="btn-connect", variant="success")
        yield Static("快捷键: A-添加 E-编辑 D-删除 Enter-连接 Q-退出", id="help")

    def on_mount(self):
        """挂载时初始化表格"""
        table = self.query_one("#conn-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("名称", "主机", "端口", "用户名")
        self.refresh_table()

    def refresh_table(self):
        """刷新连接列表"""
        table = self.query_one("#conn-table", DataTable)
        table.clear()
        connections = storage.list_connections()
        for conn in connections:
            table.add_row(
                conn.name,
                conn.host,
                str(conn.port),
                conn.username,
                key=conn.id,
            )

    def get_selected_connection(self) -> Connection | None:
        """获取选中的连接"""
        table = self.query_one("#conn-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.get_row_at(table.cursor_row)
        if row_key:
            conn_id = table.get_row_key(table.cursor_row)
            return storage.get_connection(str(conn_id.value))
        return None

    def action_add(self):
        """添加连接"""
        self.app.push_screen("connection_form")

    def action_edit(self):
        """编辑连接"""
        conn = self.get_selected_connection()
        if conn:
            self.app.push_screen("connection_form", conn)

    def action_delete(self):
        """删除连接"""
        conn = self.get_selected_connection()
        if conn:
            storage.delete_connection(conn.id)
            self.refresh_table()
            self.notify(f"已删除: {conn.name}")

    def action_connect(self):
        """连接到服务器"""
        conn = self.get_selected_connection()
        if conn:
            self.app.push_screen("terminal", conn)

    def action_quit(self):
        """退出应用"""
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed):
        """按钮点击事件"""
        button_id = event.button.id
        if button_id == "btn-add":
            self.action_add()
        elif button_id == "btn-edit":
            self.action_edit()
        elif button_id == "btn-delete":
            self.action_delete()
        elif button_id == "btn-connect":
            self.action_connect()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """双击行连接"""
        conn_id = str(event.row_key.value)
        conn = storage.get_connection(conn_id)
        if conn:
            self.app.push_screen("terminal", conn)
