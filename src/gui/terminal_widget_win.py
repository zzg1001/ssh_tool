"""终端组件 - Windows 优化版本"""

import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, font

import pyte

from ..storage import Connection
from ..ssh_client import SSHClient


class TerminalWidgetWin:
    """终端组件 - Windows 优化版"""

    # 刷新间隔（毫秒）
    REFRESH_INTERVAL = 50

    def __init__(self, parent, connection: Connection, on_connected=None):
        self.connection = connection
        self.ssh_client: SSHClient | None = None
        self._running = False
        self.on_connected = on_connected
        self._stats_running = False
        self._last_net_rx = 0
        self._last_net_tx = 0
        self._last_net_time = 0

        # 终端大小
        self.cols = 120
        self.rows = 40

        # pyte 虚拟终端
        self.screen = pyte.Screen(self.cols, self.rows)
        self.stream = pyte.Stream(self.screen)

        # 脏标记 - 优化刷新
        self._dirty = False
        self._refresh_scheduled = False

        self.frame = ttk.Frame(parent)
        self._setup_ui()
        self._setup_colors()

    def _setup_ui(self):
        """设置界面"""
        # 状态栏
        self.status_var = tk.StringVar(
            value=f"  {self.connection.username}@{self.connection.host}:{self.connection.port}"
        )
        status = tk.Label(
            self.frame,
            textvariable=self.status_var,
            bg='#007acc',
            fg='white',
            anchor=tk.W,
            font=('', 9),
            pady=1
        )
        status.pack(fill=tk.X)
        self.status_label = status

        # 终端容器
        term_container = tk.Frame(self.frame, bg='#1e1e1e')
        term_container.pack(fill=tk.BOTH, expand=True)

        # Windows 使用 Consolas 字体
        font_family = 'Consolas' if sys.platform == 'win32' else 'Menlo'
        self.term_font = font.Font(family=font_family, size=12)

        self.terminal = tk.Text(
            term_container,
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#d4d4d4',
            selectbackground='#264f78',
            selectforeground='#ffffff',
            font=self.term_font,
            wrap=tk.NONE,
            padx=6,
            pady=2,
            highlightthickness=0,
            borderwidth=0,
            undo=False,  # 禁用 undo 提升性能
        )
        self.terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.terminal.configure(insertwidth=2, insertbackground='#00ff00')

        # 滚动条
        scrollbar = ttk.Scrollbar(term_container, command=self.terminal.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal.configure(yscrollcommand=scrollbar.set)

        # 底部系统状态栏
        self._setup_system_status()

        # 禁用默认按键行为
        bindtags = list(self.terminal.bindtags())
        if "Text" in bindtags:
            bindtags.remove("Text")
        self.terminal.bindtags(tuple(bindtags))

        # 绑定键盘事件
        self.terminal.bind('<Key>', self._on_key)
        self.terminal.bind('<Return>', self._on_return)
        self.terminal.bind('<BackSpace>', self._on_backspace)
        self.terminal.bind('<Up>', self._on_arrow)
        self.terminal.bind('<Down>', self._on_arrow)
        self.terminal.bind('<Left>', self._on_arrow)
        self.terminal.bind('<Right>', self._on_arrow)
        self.terminal.bind('<Tab>', self._on_tab)
        self.terminal.bind('<Control-c>', self._on_ctrl_c)
        self.terminal.bind('<Control-d>', self._on_ctrl_d)
        self.terminal.bind('<Control-l>', self._on_ctrl_l)
        self.terminal.bind('<Control-z>', self._on_ctrl_z)
        self.terminal.bind('<Control-v>', self._on_paste)
        self.terminal.bind('<Escape>', self._on_escape)
        self.terminal.bind('<Home>', self._on_home)
        self.terminal.bind('<End>', self._on_end)
        self.terminal.bind('<Delete>', self._on_delete)
        self.terminal.bind('<Prior>', self._on_page)
        self.terminal.bind('<Next>', self._on_page)

        self.terminal.focus_set()

    def _setup_system_status(self):
        """设置系统状态栏"""
        self.sys_status_frame = tk.Frame(self.frame, bg='#252526', height=22)
        self.sys_status_frame.pack(fill=tk.X)
        self.sys_status_frame.pack_propagate(False)

        self.cpu_var = tk.StringVar(value="CPU: --%")
        self.mem_var = tk.StringVar(value="MEM: --%")
        self.net_var = tk.StringVar(value="NET: ↑0 ↓0")

        label_style = {'bg': '#252526', 'fg': '#858585', 'font': ('', 9)}

        tk.Label(self.sys_status_frame, textvariable=self.cpu_var, **label_style).pack(side=tk.LEFT, padx=10)
        tk.Label(self.sys_status_frame, textvariable=self.mem_var, **label_style).pack(side=tk.LEFT, padx=10)
        tk.Label(self.sys_status_frame, textvariable=self.net_var, **label_style).pack(side=tk.LEFT, padx=10)

    def _setup_colors(self):
        """配置颜色标签"""
        colors = {
            'black': '#000000', 'red': '#cd0000', 'green': '#00cd00',
            'yellow': '#cdcd00', 'blue': '#0000ee', 'magenta': '#cd00cd',
            'cyan': '#00cdcd', 'white': '#e5e5e5',
            'bright_black': '#7f7f7f', 'bright_red': '#ff0000',
            'bright_green': '#00ff00', 'bright_yellow': '#ffff00',
            'bright_blue': '#5c5cff', 'bright_magenta': '#ff00ff',
            'bright_cyan': '#00ffff', 'bright_white': '#ffffff',
        }

        for name, color in colors.items():
            self.terminal.tag_configure(f'fg_{name}', foreground=color)
            self.terminal.tag_configure(f'bg_{name}', background=color)

        bold_font = font.Font(family=self.term_font.cget('family'),
                              size=self.term_font.cget('size'),
                              weight='bold')
        self.terminal.tag_configure('bold', font=bold_font)
        self.terminal.tag_configure('underline', underline=True)
        self.terminal.tag_configure('reverse', foreground='#1e1e1e', background='#d4d4d4')

    def focus(self):
        """聚焦终端"""
        self.terminal.focus_set()

    def connect(self):
        """连接服务器"""
        self._running = True
        self._update_display("正在连接...\r\n")
        self._set_status("正在连接...", "#ffc107")

        def do_connect():
            try:
                self.ssh_client = SSHClient()
                self.ssh_client.connect(
                    host=self.connection.host,
                    port=self.connection.port,
                    username=self.connection.username,
                    password=self.connection.password,
                    key_file=self.connection.key_file,
                )
                self.ssh_client.start_shell(cols=self.cols, rows=self.rows)
                self.frame.after(0, lambda: self._set_status("已连接", "#28a745"))

                if self.on_connected:
                    self.frame.after(0, lambda: self.on_connected(self.ssh_client))

                self._start_stats_monitor()
                self._read_loop()

            except Exception as e:
                self.frame.after(0, lambda: self._update_display(f"\r\n连接失败: {e}\r\n"))
                self.frame.after(0, lambda: self._set_status("连接失败", "#dc3545"))

        threading.Thread(target=do_connect, daemon=True).start()

    def disconnect(self):
        """断开连接"""
        self._running = False
        self._stats_running = False
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def _read_loop(self):
        """读取循环 - 优化版"""
        buffer = ""
        last_refresh = time.time()

        while self._running and self.ssh_client and self.ssh_client.channel:
            try:
                if self.ssh_client.channel.recv_ready():
                    data = self.ssh_client.channel.recv(8192)  # 增大缓冲区
                    if data:
                        text = data.decode('utf-8', errors='replace')
                        self.stream.feed(text)
                        self._dirty = True

                        # 限制刷新频率
                        now = time.time()
                        if now - last_refresh > 0.03:  # 30ms
                            self._schedule_refresh()
                            last_refresh = now
                    else:
                        break
                elif self.ssh_client.channel.closed:
                    break
                else:
                    # 如果有脏数据，刷新
                    if self._dirty:
                        self._schedule_refresh()
                    time.sleep(0.01)

            except Exception as e:
                self.frame.after(0, lambda: self._update_display(f"\r\n[错误: {e}]\r\n"))
                break

        self.frame.after(0, lambda: self._update_display("\r\n[连接已关闭]\r\n"))
        self.frame.after(0, lambda: self._set_status("已断开", "#6c757d"))

    def _schedule_refresh(self):
        """调度刷新"""
        if not self._refresh_scheduled:
            self._refresh_scheduled = True
            self.frame.after(self.REFRESH_INTERVAL, self._do_refresh)

    def _do_refresh(self):
        """执行刷新"""
        self._refresh_scheduled = False
        if self._dirty:
            self._dirty = False
            self._refresh_display()

    def _refresh_display(self):
        """刷新显示 - 优化版"""
        self.terminal.configure(state=tk.NORMAL)
        self.terminal.delete('1.0', tk.END)

        cursor_y = self.screen.cursor.y
        cursor_x = self.screen.cursor.x

        # 批量构建文本
        lines = []
        for y in range(self.screen.lines):
            line_text = ""
            line_end = self._get_line_end(y)
            if y == cursor_y:
                line_end = max(cursor_x + 1, line_end)

            for x in range(line_end):
                char = self.screen.buffer[y][x]
                line_text += char.data if char.data else " "

            lines.append(line_text)

        # 一次性插入所有文本
        full_text = '\n'.join(lines)
        self.terminal.insert('1.0', full_text)

        # 移动光标
        try:
            cursor_pos = f"{cursor_y + 1}.{cursor_x}"
            self.terminal.mark_set(tk.INSERT, cursor_pos)
            self.terminal.see(cursor_pos)
        except:
            pass

    def _get_line_end(self, y):
        """获取行的有效结束位置"""
        for x in range(self.screen.columns - 1, -1, -1):
            char = self.screen.buffer[y][x]
            if char.data and char.data != ' ':
                return x + 1
        return 0

    def _update_display(self, text: str):
        """直接更新显示"""
        self.stream.feed(text)
        self._refresh_display()

    def _set_status(self, text: str, color: str):
        """设置状态"""
        full_text = f"  {self.connection.username}@{self.connection.host}:{self.connection.port} - {text}"
        self.status_var.set(full_text)
        self.status_label.configure(bg=color)

    def _send(self, data: str):
        """发送数据"""
        if self.ssh_client and self.ssh_client.channel:
            try:
                self.ssh_client.channel.send(data.encode('utf-8'))
            except:
                pass

    def _on_key(self, event):
        """处理按键"""
        if event.char and ord(event.char) >= 32:
            self._send(event.char)
        return "break"

    def _on_return(self, event):
        self._send('\r')
        return "break"

    def _on_backspace(self, event):
        self._send('\x7f')
        return "break"

    def _on_arrow(self, event):
        arrows = {'Up': '\x1b[A', 'Down': '\x1b[B', 'Right': '\x1b[C', 'Left': '\x1b[D'}
        self._send(arrows.get(event.keysym, ''))
        return "break"

    def _on_tab(self, event):
        self._send('\t')
        return "break"

    def _on_ctrl_c(self, event):
        self._send('\x03')
        return "break"

    def _on_ctrl_d(self, event):
        self._send('\x04')
        return "break"

    def _on_ctrl_l(self, event):
        self._send('\x0c')
        return "break"

    def _on_ctrl_z(self, event):
        self._send('\x1a')
        return "break"

    def _on_paste(self, event):
        try:
            text = self.terminal.clipboard_get()
            self._send(text)
        except:
            pass
        return "break"

    def _on_escape(self, event):
        self._send('\x1b')
        return "break"

    def _on_home(self, event):
        self._send('\x1b[H')
        return "break"

    def _on_end(self, event):
        self._send('\x1b[F')
        return "break"

    def _on_delete(self, event):
        self._send('\x1b[3~')
        return "break"

    def _on_page(self, event):
        if event.keysym == 'Prior':
            self._send('\x1b[5~')
        else:
            self._send('\x1b[6~')
        return "break"

    def _start_stats_monitor(self):
        """启动系统状态监控"""
        self._stats_running = True

        def monitor():
            while self._stats_running and self.ssh_client and self.ssh_client.channel:
                try:
                    stdin, stdout, stderr = self.ssh_client.client.exec_command(
                        "cat /proc/stat /proc/meminfo /proc/net/dev 2>/dev/null | head -50",
                        timeout=2
                    )
                    output = stdout.read().decode('utf-8', errors='replace')
                    self.frame.after(0, lambda o=output: self._parse_stats(o))
                except:
                    pass
                time.sleep(2)

        threading.Thread(target=monitor, daemon=True).start()

    def _parse_stats(self, output: str):
        """解析系统状态"""
        try:
            lines = output.split('\n')

            # CPU
            for line in lines:
                if line.startswith('cpu '):
                    parts = line.split()[1:5]
                    total = sum(int(p) for p in parts)
                    idle = int(parts[3])
                    usage = 100 - (idle * 100 // total) if total > 0 else 0
                    self.cpu_var.set(f"CPU: {usage}%")
                    break

            # Memory
            mem_total = mem_free = mem_buffers = mem_cached = 0
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1])
                elif line.startswith('MemFree:'):
                    mem_free = int(line.split()[1])
                elif line.startswith('Buffers:'):
                    mem_buffers = int(line.split()[1])
                elif line.startswith('Cached:'):
                    mem_cached = int(line.split()[1])
                    break

            if mem_total > 0:
                used = mem_total - mem_free - mem_buffers - mem_cached
                usage = used * 100 // mem_total
                self.mem_var.set(f"MEM: {usage}%")

        except:
            pass
