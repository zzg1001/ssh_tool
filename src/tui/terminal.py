"""SSH 终端界面"""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, RichLog
from textual.screen import Screen
from textual.binding import Binding
from textual import events

from ..storage import Connection
from ..ssh_client import SSHClient


class TerminalScreen(Screen):
    """SSH 终端界面"""

    BINDINGS = [
        Binding("ctrl+d", "disconnect", "断开连接", priority=True),
    ]

    CSS = """
    TerminalScreen {
        layout: vertical;
    }

    #status-bar {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }

    #terminal {
        height: 1fr;
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 0;
    }

    #help-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, connection: Connection):
        super().__init__()
        self.connection = connection
        self.ssh_client: SSHClient | None = None
        self._read_task = None

    def compose(self) -> ComposeResult:
        yield Static(
            f"连接到: {self.connection.username}@{self.connection.host}:{self.connection.port}",
            id="status-bar"
        )
        yield RichLog(id="terminal", wrap=True, highlight=False, markup=False)
        yield Static("Ctrl+D 断开连接", id="help-bar")

    async def on_mount(self):
        """挂载时建立连接"""
        terminal = self.query_one("#terminal", RichLog)
        terminal.focus()
        await self._connect()

    async def _connect(self):
        """建立 SSH 连接"""
        terminal = self.query_one("#terminal", RichLog)
        terminal.write(f"正在连接 {self.connection.host}...")

        try:
            self.ssh_client = SSHClient(self.connection)
            self.ssh_client.connect()

            # 获取终端大小
            size = self.app.size
            cols = size.width
            rows = size.height - 2  # 减去状态栏

            self.ssh_client.open_shell(cols=cols, rows=rows)
            terminal.write("连接成功!\n")

            # 启动读取循环
            self._read_task = asyncio.create_task(self._read_loop())

        except Exception as e:
            terminal.write(f"\n连接失败: {e}")
            self.notify(f"连接失败: {e}", severity="error")

    async def _read_loop(self):
        """异步读取远程输出"""
        terminal = self.query_one("#terminal", RichLog)

        while self.ssh_client and self.ssh_client.channel:
            try:
                if self.ssh_client.channel.recv_ready():
                    data = self.ssh_client.channel.recv(4096)
                    if data:
                        # 解码并写入终端
                        text = data.decode("utf-8", errors="replace")
                        terminal.write(text)
                    else:
                        break
                else:
                    await asyncio.sleep(0.01)

                # 检查连接状态
                if self.ssh_client.channel.closed:
                    break

            except Exception as e:
                terminal.write(f"\n连接断开: {e}")
                break

        terminal.write("\n[连接已关闭]")

    async def on_key(self, event: events.Key):
        """处理键盘输入"""
        if not self.ssh_client or not self.ssh_client.channel:
            return

        # 处理特殊按键
        key_map = {
            "enter": "\r",
            "tab": "\t",
            "backspace": "\x7f",
            "delete": "\x1b[3~",
            "up": "\x1b[A",
            "down": "\x1b[B",
            "right": "\x1b[C",
            "left": "\x1b[D",
            "home": "\x1b[H",
            "end": "\x1b[F",
            "pageup": "\x1b[5~",
            "pagedown": "\x1b[6~",
            "escape": "\x1b",
        }

        # Ctrl 组合键
        if event.key.startswith("ctrl+") and event.key != "ctrl+d":
            char = event.key[-1]
            if char.isalpha():
                # Ctrl+A = 0x01, Ctrl+B = 0x02, etc.
                code = ord(char.lower()) - ord('a') + 1
                self.ssh_client.send_bytes(bytes([code]))
                event.prevent_default()
                return

        if event.key in key_map:
            self.ssh_client.send(key_map[event.key])
            event.prevent_default()
        elif event.character and len(event.character) == 1:
            self.ssh_client.send(event.character)
            event.prevent_default()

    def on_resize(self, event: events.Resize):
        """处理终端大小变化"""
        if self.ssh_client:
            cols = event.size.width
            rows = event.size.height - 2
            self.ssh_client.resize_pty(cols, rows)

    def action_disconnect(self):
        """断开连接"""
        self._cleanup()
        self.app.pop_screen()

    def _cleanup(self):
        """清理资源"""
        if self._read_task:
            self._read_task.cancel()
            self._read_task = None
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def on_unmount(self):
        """卸载时清理"""
        self._cleanup()
