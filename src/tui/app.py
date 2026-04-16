"""TUI 主应用"""

from textual.app import App

from .connection_list import ConnectionList
from .connection_form import ConnectionForm
from .terminal import TerminalScreen
from ..storage import Connection


class SSHToolApp(App):
    """SSH Tool TUI 应用"""

    TITLE = "SSH Tool"
    CSS = """
    Screen {
        background: $surface;
    }
    """

    SCREENS = {
        "main": ConnectionList,
    }

    def on_mount(self):
        """启动时显示主界面"""
        self.push_screen("main")

    def push_screen(self, screen_name: str, data=None):
        """推送屏幕，支持传递数据"""
        if screen_name == "connection_form":
            screen = ConnectionForm(connection=data)
            super().push_screen(screen)
        elif screen_name == "terminal":
            if isinstance(data, Connection):
                screen = TerminalScreen(connection=data)
                super().push_screen(screen)
        else:
            super().push_screen(screen_name)


def run():
    """运行应用"""
    app = SSHToolApp()
    app.run()
