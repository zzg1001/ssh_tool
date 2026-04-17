"""终端组件 - Windows 优化版"""

import threading
import time
import tkinter as tk
from tkinter import ttk, font

import pyte

from src_win.storage import Connection
from src_win.ssh_client import SSHClient


class TerminalWidget:
    """终端组件 - Windows 风格"""

    # 终端配色
    TERM_BG = '#1e1e1e'
    TERM_FG = '#d4d4d4'
    STATUS_CONNECTED = '#107c10'
    STATUS_CONNECTING = '#0078d4'
    STATUS_ERROR = '#d13438'
    STATUS_DISCONNECTED = '#6e6e6e'

    # 状态栏配色
    SYSBAR_BG = '#f8f8f8'
    SYSBAR_TEXT = '#1a1a1a'
    SYSBAR_LABEL = '#666666'

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

        self.frame = ttk.Frame(parent)
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        # 状态栏
        self.status_var = tk.StringVar(
            value=f"  {self.connection.username}@{self.connection.host}:{self.connection.port}"
        )
        status = tk.Label(
            self.frame,
            textvariable=self.status_var,
            bg=self.STATUS_CONNECTING,
            fg='white',
            anchor=tk.W,
            font=('Segoe UI', 9),
            pady=2
        )
        status.pack(fill=tk.X)
        self.status_label = status

        # 终端容器
        term_container = tk.Frame(self.frame, bg=self.TERM_BG)
        term_container.pack(fill=tk.BOTH, expand=True)

        # 终端文本区
        self.term_font = font.Font(family='Consolas', size=11)

        self.terminal = tk.Text(
            term_container,
            bg=self.TERM_BG,
            fg=self.TERM_FG,
            insertbackground=self.TERM_FG,
            selectbackground='#264f78',
            selectforeground='#ffffff',
            font=self.term_font,
            wrap=tk.NONE,
            padx=8,
            pady=4,
            highlightthickness=0,
            borderwidth=0
        )
        self.terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 配置光标样式
        self.terminal.configure(insertwidth=2, insertbackground='#00ff00')

        # 滚动条
        scrollbar = ttk.Scrollbar(term_container, command=self.terminal.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal.configure(yscrollcommand=scrollbar.set)

        # 底部系统状态栏
        self._setup_system_status()

        # 禁用 Text 组件的默认按键行为，让我们完全控制输入
        # 修改 bindtags 移除 "Text" 类级别的默认绑定
        bindtags = list(self.terminal.bindtags())
        if "Text" in bindtags:
            bindtags.remove("Text")
        self.terminal.bindtags(tuple(bindtags))

        # 绑定键盘事件
        self.terminal.bind('<Key>', self._on_key)
        self.terminal.bind('<Return>', self._on_return)
        self.terminal.bind('<BackSpace>', self._on_backspace)
        self.terminal.bind('<Tab>', self._on_tab)
        self.terminal.bind('<Escape>', self._on_escape)
        self.terminal.bind('<Up>', self._on_arrow)
        self.terminal.bind('<Down>', self._on_arrow)
        self.terminal.bind('<Left>', self._on_arrow)
        self.terminal.bind('<Right>', self._on_arrow)
        self.terminal.bind('<Home>', self._on_home_end)
        self.terminal.bind('<End>', self._on_home_end)

        # Ctrl 快捷键
        self.terminal.bind('<Control-c>', self._on_ctrl_c)
        self.terminal.bind('<Control-d>', self._on_ctrl_d)
        self.terminal.bind('<Control-z>', self._on_ctrl_z)
        self.terminal.bind('<Control-l>', self._on_ctrl_l)
        self.terminal.bind('<Control-a>', self._on_ctrl_a)
        self.terminal.bind('<Control-e>', self._on_ctrl_e)
        self.terminal.bind('<Control-u>', self._on_ctrl_u)
        self.terminal.bind('<Control-k>', self._on_ctrl_k)
        self.terminal.bind('<Control-w>', self._on_ctrl_w)
        self.terminal.bind('<Control-r>', self._on_ctrl_r)

        # Windows 复制粘贴快捷键
        self.terminal.bind('<Control-Shift-c>', self._on_copy)
        self.terminal.bind('<Control-Shift-v>', self._on_paste)
        self.terminal.bind('<Control-Insert>', self._on_copy)
        self.terminal.bind('<Shift-Insert>', self._on_paste)

        # 配置 ANSI 颜色标签
        self._setup_color_tags()

        # 聚焦
        self.terminal.focus_set()

    def _setup_color_tags(self):
        """配置 ANSI 颜色标签"""
        # 标准 ANSI 颜色 (普通)
        self.ansi_colors = {
            'black': '#000000',
            'red': '#cd0000',
            'green': '#00cd00',
            'yellow': '#cdcd00',
            'blue': '#0000ee',
            'magenta': '#cd00cd',
            'cyan': '#00cdcd',
            'white': '#e5e5e5',
            # 亮色版本
            'brightblack': '#7f7f7f',
            'brightred': '#ff0000',
            'brightgreen': '#00ff00',
            'brightyellow': '#ffff00',
            'brightblue': '#5c5cff',
            'brightmagenta': '#ff00ff',
            'brightcyan': '#00ffff',
            'brightwhite': '#ffffff',
        }

        # 创建前景色标签
        for name, color in self.ansi_colors.items():
            self.terminal.tag_configure(f'fg_{name}', foreground=color)

        # 创建背景色标签
        for name, color in self.ansi_colors.items():
            self.terminal.tag_configure(f'bg_{name}', background=color)

        # 粗体标签
        bold_font = font.Font(family='Consolas', size=13, weight='bold')
        self.terminal.tag_configure('bold', font=bold_font)

        # 下划线
        self.terminal.tag_configure('underline', underline=True)

        # 反色
        self.terminal.tag_configure('reverse', foreground='#1e1e1e', background='#d4d4d4')

    def _get_color_name(self, color_value, bright=False):
        """将 pyte 颜色值转换为颜色名称"""
        color_map = {
            'default': None,
            'black': 'black',
            'red': 'red',
            'green': 'green',
            'brown': 'yellow',
            'yellow': 'yellow',
            'blue': 'blue',
            'magenta': 'magenta',
            'cyan': 'cyan',
            'white': 'white',
        }

        if color_value == 'default':
            return None

        if isinstance(color_value, str):
            base_color = color_map.get(color_value)
            if base_color and bright:
                return f'bright{base_color}'
            return base_color

        # 数字颜色 (0-7 标准, 8-15 亮色)
        if isinstance(color_value, int):
            names = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
            if 0 <= color_value <= 7:
                base = names[color_value]
                return f'bright{base}' if bright else base
            elif 8 <= color_value <= 15:
                return f'bright{names[color_value - 8]}'

        return None

    def _setup_system_status(self):
        """设置底部系统状态栏"""
        # 分隔线
        tk.Frame(self.frame, bg='#e1e1e1', height=1).pack(fill=tk.X, side=tk.BOTTOM)

        self.sys_status = tk.Frame(self.frame, bg=self.SYSBAR_BG, height=26)
        self.sys_status.pack(fill=tk.X, side=tk.BOTTOM)
        self.sys_status.pack_propagate(False)

        font_label = ('Segoe UI', 8)
        font_value = ('Segoe UI', 8)

        # 主机名
        self.hostname_label = tk.Label(
            self.sys_status, text="--", bg=self.SYSBAR_BG, fg=self.SYSBAR_TEXT,
            font=font_value, anchor=tk.W
        )
        self.hostname_label.pack(side=tk.LEFT, padx=(8, 12))

        # CPU
        cpu_frame = tk.Frame(self.sys_status, bg=self.SYSBAR_BG)
        cpu_frame.pack(side=tk.LEFT, padx=4)
        tk.Label(cpu_frame, text="CPU", bg=self.SYSBAR_BG, fg=self.SYSBAR_LABEL, font=font_label).pack(side=tk.LEFT)
        self.cpu_label = tk.Label(cpu_frame, text="0%", bg=self.SYSBAR_BG, fg=self.SYSBAR_TEXT, font=font_value, width=4)
        self.cpu_label.pack(side=tk.LEFT, padx=(2, 0))
        self.cpu_bar = tk.Canvas(cpu_frame, width=36, height=10, bg='#e0e0e0', highlightthickness=0)
        self.cpu_bar.pack(side=tk.LEFT, padx=(4, 0))

        # 内存
        mem_frame = tk.Frame(self.sys_status, bg=self.SYSBAR_BG)
        mem_frame.pack(side=tk.LEFT, padx=8)
        tk.Label(mem_frame, text="MEM", bg=self.SYSBAR_BG, fg=self.SYSBAR_LABEL, font=font_label).pack(side=tk.LEFT)
        self.mem_label = tk.Label(mem_frame, text="0/0G", bg=self.SYSBAR_BG, fg=self.SYSBAR_TEXT, font=font_value)
        self.mem_label.pack(side=tk.LEFT, padx=(2, 0))

        # 上传
        up_frame = tk.Frame(self.sys_status, bg=self.SYSBAR_BG)
        up_frame.pack(side=tk.LEFT, padx=8)
        tk.Label(up_frame, text="↑", bg=self.SYSBAR_BG, fg='#0078d4', font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        self.upload_label = tk.Label(up_frame, text="0K/s", bg=self.SYSBAR_BG, fg=self.SYSBAR_TEXT, font=font_value)
        self.upload_label.pack(side=tk.LEFT, padx=(2, 0))

        # 下载
        down_frame = tk.Frame(self.sys_status, bg=self.SYSBAR_BG)
        down_frame.pack(side=tk.LEFT, padx=8)
        tk.Label(down_frame, text="↓", bg=self.SYSBAR_BG, fg='#107c10', font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        self.download_label = tk.Label(down_frame, text="0K/s", bg=self.SYSBAR_BG, fg=self.SYSBAR_TEXT, font=font_value)
        self.download_label.pack(side=tk.LEFT, padx=(2, 0))

        # 运行时间
        uptime_frame = tk.Frame(self.sys_status, bg=self.SYSBAR_BG)
        uptime_frame.pack(side=tk.LEFT, padx=8)
        tk.Label(uptime_frame, text="UP", bg=self.SYSBAR_BG, fg=self.SYSBAR_LABEL, font=font_label).pack(side=tk.LEFT)
        self.uptime_label = tk.Label(uptime_frame, text="--", bg=self.SYSBAR_BG, fg=self.SYSBAR_TEXT, font=font_value)
        self.uptime_label.pack(side=tk.LEFT, padx=(2, 0))

        # 用户数
        user_frame = tk.Frame(self.sys_status, bg=self.SYSBAR_BG)
        user_frame.pack(side=tk.LEFT, padx=8)
        tk.Label(user_frame, text="USR", bg=self.SYSBAR_BG, fg=self.SYSBAR_LABEL, font=font_label).pack(side=tk.LEFT)
        self.user_label = tk.Label(user_frame, text="--", bg=self.SYSBAR_BG, fg=self.SYSBAR_TEXT, font=font_value)
        self.user_label.pack(side=tk.LEFT, padx=(2, 0))

        # 磁盘
        disk_frame = tk.Frame(self.sys_status, bg=self.SYSBAR_BG)
        disk_frame.pack(side=tk.LEFT, padx=8)
        tk.Label(disk_frame, text="DISK", bg=self.SYSBAR_BG, fg=self.SYSBAR_LABEL, font=font_label).pack(side=tk.LEFT)
        self.disk_label = tk.Label(disk_frame, text="--%", bg=self.SYSBAR_BG, fg=self.SYSBAR_TEXT, font=font_value)
        self.disk_label.pack(side=tk.LEFT, padx=(2, 0))

    def _start_stats_monitor(self):
        """启动系统状态监控"""
        self._stats_running = True

        def monitor():
            while self._stats_running and self.ssh_client:
                try:
                    stats = self._fetch_system_stats()
                    if stats:
                        self._safe_after(lambda s=stats: self._update_stats_display(s))
                except:
                    pass
                time.sleep(5)  # 每5秒更新一次

        threading.Thread(target=monitor, daemon=True).start()

    def _fetch_system_stats(self):
        """获取系统状态"""
        if not self.ssh_client:
            return None

        try:
            # 一次性获取所有信息
            cmd = """
hostname;
cat /proc/loadavg | awk '{print $1}';
cat /proc/meminfo | grep -E 'MemTotal|MemAvailable' | awk '{print $2}';
cat /proc/net/dev | grep -E 'eth0|ens|enp' | head -1 | awk '{print $2, $10}';
cat /proc/uptime | awk '{print int($1/86400)}';
who | wc -l;
df / | tail -1 | awk '{print $5}'
"""
            result = self.ssh_client.exec_command(cmd.strip())
            lines = result.strip().split('\n')

            if len(lines) >= 7:
                hostname = lines[0]
                load = float(lines[1])
                mem_total = int(lines[2]) / 1024 / 1024  # GB
                mem_avail = int(lines[3]) / 1024 / 1024  # GB
                mem_used = mem_total - mem_avail

                # 网络流量
                net_parts = lines[4].split()
                rx_bytes = int(net_parts[0]) if len(net_parts) >= 2 else 0
                tx_bytes = int(net_parts[1]) if len(net_parts) >= 2 else 0

                now = time.time()
                rx_speed = 0
                tx_speed = 0
                if self._last_net_time > 0:
                    dt = now - self._last_net_time
                    if dt > 0:
                        rx_speed = (rx_bytes - self._last_net_rx) / dt / 1024  # KB/s
                        tx_speed = (tx_bytes - self._last_net_tx) / dt / 1024  # KB/s
                self._last_net_rx = rx_bytes
                self._last_net_tx = tx_bytes
                self._last_net_time = now

                uptime_days = int(lines[5])
                users = lines[6]
                disk_usage = lines[7].replace('%', '')

                # CPU 使用率近似 (load / cpu_count * 100)
                cpu_count = int(self.ssh_client.exec_command("nproc").strip())
                cpu_pct = min(100, int(load / cpu_count * 100))

                return {
                    'hostname': hostname,
                    'cpu': cpu_pct,
                    'mem_used': mem_used,
                    'mem_total': mem_total,
                    'rx_speed': max(0, rx_speed),
                    'tx_speed': max(0, tx_speed),
                    'uptime': uptime_days,
                    'users': users,
                    'disk': disk_usage
                }
        except:
            pass
        return None

    def _update_stats_display(self, stats):
        """更新状态显示"""
        if not stats:
            return

        try:
            if not self.hostname_label.winfo_exists():
                return
        except:
            return

        try:
            self.hostname_label.config(text=stats['hostname'])
            self.cpu_label.config(text=f"{stats['cpu']}%")

            # 更新 CPU 进度条
            self.cpu_bar.delete('all')
            bar_width = int(36 * stats['cpu'] / 100)
            color = '#107c10' if stats['cpu'] < 70 else '#ff8c00' if stats['cpu'] < 90 else '#d13438'
            self.cpu_bar.create_rectangle(0, 0, bar_width, 10, fill=color, outline='')

            self.mem_label.config(text=f"{stats['mem_used']:.1f}/{stats['mem_total']:.0f}G")

            # 格式化网速
            def fmt_speed(kb):
                if kb >= 1024:
                    return f"{kb/1024:.1f}M/s"
                return f"{kb:.0f}K/s"

            self.upload_label.config(text=fmt_speed(stats['tx_speed']))
            self.download_label.config(text=fmt_speed(stats['rx_speed']))

            uptime = stats['uptime']
            self.uptime_label.config(text=f"{uptime}d")
            self.user_label.config(text=stats['users'])
            self.disk_label.config(text=f"{stats['disk']}%")
        except:
            pass

    def connect(self):
        """连接"""
        self._update_display("正在连接...\r\n")

        def do_connect():
            try:
                self.ssh_client = SSHClient(self.connection)
                self.ssh_client.connect()
                self.ssh_client.open_shell(cols=self.cols, rows=self.rows)
                self._running = True

                self.frame.after(0, lambda: self._set_status("已连接", self.STATUS_CONNECTED))

                # 通知连接成功
                if self.on_connected:
                    self.frame.after(0, lambda: self.on_connected(self.ssh_client))

                # 启动系统状态监控
                self._start_stats_monitor()

                self._read_loop()

            except Exception as e:
                self.frame.after(0, lambda: self._update_display(f"\r\n连接失败: {e}\r\n"))
                self.frame.after(0, lambda: self._set_status("连接失败", self.STATUS_ERROR))

        threading.Thread(target=do_connect, daemon=True).start()

    def disconnect(self):
        """断开连接"""
        self._running = False
        self._stats_running = False
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def _read_loop(self):
        """读取循环"""
        self._pending_refresh = False
        self._last_refresh = 0
        refresh_interval = 0.03  # 最小刷新间隔 30ms

        while self._running and self.ssh_client and self.ssh_client.channel:
            try:
                if self.ssh_client.channel.recv_ready():
                    data = self.ssh_client.channel.recv(8192)
                    if data:
                        text = data.decode('utf-8', errors='replace')
                        self.stream.feed(text)

                        # 限制刷新频率
                        now = time.time()
                        if now - self._last_refresh >= refresh_interval:
                            self._last_refresh = now
                            self._safe_after(self._refresh_display)
                        elif not self._pending_refresh:
                            self._pending_refresh = True
                            delay = int((refresh_interval - (now - self._last_refresh)) * 1000)
                            self._safe_after(self._delayed_refresh, max(10, delay))
                    else:
                        break
                elif self.ssh_client.channel.closed:
                    break
                else:
                    time.sleep(0.01)  # 避免 CPU 空转
            except Exception as ex:
                err_msg = str(ex)
                self._safe_after(lambda m=err_msg: self._update_display(f"\r\n[错误: {m}]\r\n"))
                break

        self._safe_after(lambda: self._update_display("\r\n[连接已关闭]\r\n"))
        self._safe_after(lambda: self._set_status("已断开", self.STATUS_DISCONNECTED))

    def _safe_after(self, func, delay=0):
        """安全的 after 调用"""
        try:
            if self.frame.winfo_exists():
                self.frame.after(delay, func)
        except:
            pass

    def _delayed_refresh(self):
        """延迟刷新"""
        self._pending_refresh = False
        self._last_refresh = time.time()
        try:
            if self.terminal.winfo_exists():
                self._refresh_display()
        except:
            pass

    def _refresh_display(self):
        """从 pyte screen 刷新显示（优化版）"""
        try:
            if not self.terminal.winfo_exists():
                return
        except:
            return

        self.terminal.configure(state=tk.NORMAL)
        self.terminal.delete('1.0', tk.END)

        cursor_y = self.screen.cursor.y
        cursor_x = self.screen.cursor.x
        buffer = self.screen.buffer
        lines = []

        # 先收集所有文本（不带颜色的快速模式）
        for y in range(self.screen.lines):
            line = buffer[y]
            # 找到行尾
            if y == cursor_y:
                line_end = max(cursor_x + 1, self._get_line_end(y))
            else:
                line_end = self._get_line_end(y)

            # 快速构建行文本
            row_text = ''.join(
                line[x].data if line[x].data else ' '
                for x in range(line_end)
            )
            lines.append(row_text)

        # 一次性插入所有文本
        self.terminal.insert('1.0', '\n'.join(lines))

        # 移除末尾空行但保留光标所在行
        # (已在渲染时处理)

        # 移动光标到正确位置
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

    def _get_char_tags(self, char):
        """获取字符的样式标签"""
        tags = []

        # 前景色
        fg = getattr(char, 'fg', 'default')
        bold = getattr(char, 'bold', False)
        fg_name = self._get_color_name(fg, bright=bold)
        if fg_name:
            tags.append(f'fg_{fg_name}')

        # 背景色
        bg = getattr(char, 'bg', 'default')
        bg_name = self._get_color_name(bg)
        if bg_name:
            tags.append(f'bg_{bg_name}')

        # 粗体（如果没有用于亮色）
        if bold and not fg_name:
            tags.append('bold')

        # 下划线
        if getattr(char, 'underscore', False):
            tags.append('underline')

        # 反色
        if getattr(char, 'reverse', False):
            tags.append('reverse')

        return tuple(tags)

    def _update_display(self, text: str):
        """直接更新显示"""
        try:
            if not self.terminal.winfo_exists():
                return
            self.stream.feed(text)
            self._refresh_display()
        except:
            pass

    def _set_status(self, text: str, color: str):
        """设置状态"""
        try:
            if not self.status_label.winfo_exists():
                return
            self.status_var.set(f"  {text}: {self.connection.username}@{self.connection.host}")
            self.status_label.configure(bg=color)
        except:
            pass

    def _send(self, data: str):
        """发送数据"""
        if self.ssh_client and self.ssh_client.channel:
            self.ssh_client.send(data)

    def _send_bytes(self, data: bytes):
        """发送字节"""
        if self.ssh_client and self.ssh_client.channel:
            self.ssh_client.send_bytes(data)

    # ===== 复制粘贴 =====
    def _on_copy(self, event):
        """复制选中文本"""
        try:
            selected = self.terminal.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.terminal.clipboard_clear()
            self.terminal.clipboard_append(selected)
        except tk.TclError:
            pass  # 没有选中文本
        return "break"

    def _on_paste(self, event):
        """粘贴文本"""
        try:
            text = self.terminal.clipboard_get()
            if text:
                self._send(text)
        except tk.TclError:
            pass  # 剪贴板为空
        return "break"

    # ===== 按键处理 =====
    def _on_key(self, event):
        """按键事件"""
        # 忽略修饰键
        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                           'Alt_L', 'Alt_R', 'Meta_L', 'Meta_R', 'Super_L', 'Super_R',
                           'Caps_Lock', 'Num_Lock', 'Scroll_Lock'):
            return "break"

        # 如果有 Ctrl 修饰键，跳过（由专门的绑定处理）
        # Windows: Control = 0x4, Alt = 0x20000 or 0x8
        if event.state & 0x4:  # Control held
            return "break"

        # 优先使用 event.char
        if event.char:
            code = ord(event.char)
            # 可打印字符 (32-126)
            if 32 <= code <= 126:
                self._send(event.char)
                return "break"

        # 备用：单字符 keysym (a-z, 0-9 等)
        if event.keysym and len(event.keysym) == 1:
            char = event.keysym
            # 检查是否按住 Shift
            if event.state & 0x1:  # Shift held
                char = char.upper()
            else:
                char = char.lower()
            self._send(char)

        return "break"

    def _on_return(self, event):
        self._send('\r')
        return "break"

    def _on_backspace(self, event):
        self._send_bytes(b'\x7f')
        return "break"

    def _on_tab(self, event):
        self._send('\t')
        return "break"

    def _on_escape(self, event):
        self._send_bytes(b'\x1b')
        return "break"

    def _on_ctrl_c(self, event):
        # 确保 Control 键确实被按下
        if not (event.state & 0x4):
            return  # 让事件继续传播到 _on_key

        # 如果有选中文本，执行复制；否则发送 Ctrl+C
        try:
            self.terminal.get(tk.SEL_FIRST, tk.SEL_LAST)
            return self._on_copy(event)
        except tk.TclError:
            self._send_bytes(b'\x03')
        return "break"

    def _on_ctrl_d(self, event):
        self._send_bytes(b'\x04')
        return "break"

    def _on_ctrl_z(self, event):
        self._send_bytes(b'\x1a')
        return "break"

    def _on_ctrl_l(self, event):
        self._send_bytes(b'\x0c')
        return "break"

    def _on_ctrl_a(self, event):
        self._send_bytes(b'\x01')
        return "break"

    def _on_ctrl_e(self, event):
        self._send_bytes(b'\x05')
        return "break"

    def _on_ctrl_u(self, event):
        self._send_bytes(b'\x15')
        return "break"

    def _on_ctrl_k(self, event):
        self._send_bytes(b'\x0b')
        return "break"

    def _on_ctrl_w(self, event):
        self._send_bytes(b'\x17')
        return "break"

    def _on_ctrl_r(self, event):
        self._send_bytes(b'\x12')
        return "break"

    def _on_arrow(self, event):
        key_map = {
            'Up': b'\x1b[A',
            'Down': b'\x1b[B',
            'Right': b'\x1b[C',
            'Left': b'\x1b[D',
        }
        if event.keysym in key_map:
            self._send_bytes(key_map[event.keysym])
        return "break"

    def _on_home_end(self, event):
        key_map = {
            'Home': b'\x1b[H',
            'End': b'\x1b[F',
        }
        if event.keysym in key_map:
            self._send_bytes(key_map[event.keysym])
        return "break"

    def focus(self):
        """聚焦到终端"""
        self.terminal.focus_set()
