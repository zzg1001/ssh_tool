"""SFTP 文件浏览器面板 - Windows 优化版"""

import os
import stat
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src_win.ssh_client import SSHClient


class SFTPPanel:
    """SFTP 文件浏览器 - Windows 风格"""

    # Windows 风格配色
    BG_COLOR = '#ffffff'
    HEADER_BG = '#f3f3f3'
    TEXT_COLOR = '#1a1a1a'
    LABEL_COLOR = '#666666'
    ACCENT_COLOR = '#0078d4'
    BORDER_COLOR = '#e1e1e1'
    SELECT_BG = '#cce4f7'
    TOOLBAR_BG = '#fafafa'

    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=self.BG_COLOR)
        self.ssh_client: SSHClient | None = None
        self.current_path = "/"
        self._follow_terminal = tk.BooleanVar(value=False)
        self._follow_running = False
        self._last_terminal_path = None
        self._transferring = False

        self._create_icons()
        self._setup_ui()

    def _create_icons(self):
        """创建文件图标"""
        # 文件夹图标 - 黄色
        self.folder_icon = tk.PhotoImage(width=16, height=14)
        for y in range(14):
            for x in range(16):
                if y < 4 and x < 6:
                    self.folder_icon.put('#d4a000', (x, y))
                elif y >= 3:
                    self.folder_icon.put('#e8b800', (x, y))

        # 隐藏文件夹图标 - 淡黄色
        self.hidden_folder_icon = tk.PhotoImage(width=16, height=14)
        for y in range(14):
            for x in range(16):
                if y < 4 and x < 6:
                    self.hidden_folder_icon.put('#e8d080', (x, y))
                elif y >= 3:
                    self.hidden_folder_icon.put('#f0e0a0', (x, y))

        # 文件图标 - 白色带边框
        self.file_icon = tk.PhotoImage(width=14, height=16)
        for y in range(16):
            for x in range(14):
                if x == 0 or x == 13 or y == 0 or y == 15:
                    self.file_icon.put('#999999', (x, y))
                elif x < 10 and y < 4 and x + y > 8:
                    self.file_icon.put('#cccccc', (x, y))
                else:
                    self.file_icon.put('#ffffff', (x, y))

        # 隐藏文件图标 - 灰色
        self.hidden_file_icon = tk.PhotoImage(width=14, height=16)
        for y in range(16):
            for x in range(14):
                if x == 0 or x == 13 or y == 0 or y == 15:
                    self.hidden_file_icon.put('#cccccc', (x, y))
                else:
                    self.hidden_file_icon.put('#f5f5f5', (x, y))

    def _setup_ui(self):
        """设置界面"""
        # 标题栏
        header = tk.Frame(self.frame, bg=self.HEADER_BG, height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="  Files",
            bg=self.HEADER_BG,
            fg=self.TEXT_COLOR,
            font=('Segoe UI Semibold', 10),
            anchor=tk.W
        )
        title.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 分隔线
        tk.Frame(self.frame, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X)

        # 工具栏
        toolbar = tk.Frame(self.frame, bg=self.TOOLBAR_BG, height=32)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # 工具栏按钮样式
        btn_style = {
            'bg': self.TOOLBAR_BG,
            'fg': self.TEXT_COLOR,
            'activebackground': self.SELECT_BG,
            'activeforeground': self.TEXT_COLOR,
            'relief': tk.FLAT,
            'font': ('Segoe UI', 10),
            'width': 3,
            'bd': 0
        }

        # 上传按钮
        self.upload_btn = tk.Button(toolbar, text="↑", command=self._on_upload, **btn_style)
        self.upload_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._add_tooltip(self.upload_btn, "上传文件")

        # 下载按钮
        self.download_btn = tk.Button(toolbar, text="↓", command=self._on_download, **btn_style)
        self.download_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._add_tooltip(self.download_btn, "下载文件")

        # 分隔线
        tk.Frame(toolbar, width=1, bg=self.BORDER_COLOR).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)

        # 刷新按钮
        self.refresh_btn = tk.Button(toolbar, text="↻", command=self._on_refresh, **btn_style)
        self.refresh_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._add_tooltip(self.refresh_btn, "刷新")

        # 新建文件夹按钮
        self.mkdir_btn = tk.Button(toolbar, text="+", command=self._on_mkdir, **btn_style)
        self.mkdir_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._add_tooltip(self.mkdir_btn, "新建文件夹")

        # 删除按钮
        self.delete_btn = tk.Button(toolbar, text="×", command=self._on_delete, **btn_style)
        self.delete_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._add_tooltip(self.delete_btn, "删除")

        # 分隔线
        tk.Frame(self.frame, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X)

        # 路径栏
        path_frame = tk.Frame(self.frame, bg=self.BG_COLOR, height=28)
        path_frame.pack(fill=tk.X)
        path_frame.pack_propagate(False)

        self.path_var = tk.StringVar(value="/")
        self.path_entry = tk.Entry(
            path_frame,
            textvariable=self.path_var,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            insertbackground=self.TEXT_COLOR,
            relief=tk.FLAT,
            font=('Segoe UI', 9),
            bd=0
        )
        self.path_entry.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.path_entry.bind('<Return>', self._on_path_enter)

        # 分隔线
        tk.Frame(self.frame, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X)

        # 文件列表
        list_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 配置 Treeview 样式
        style = ttk.Style()
        style.configure('Files.Treeview',
                       background=self.BG_COLOR,
                       foreground=self.TEXT_COLOR,
                       fieldbackground=self.BG_COLOR,
                       font=('Segoe UI', 9),
                       rowheight=22)
        style.map('Files.Treeview',
                 background=[('selected', self.SELECT_BG)],
                 foreground=[('selected', self.ACCENT_COLOR)])

        self.file_tree = ttk.Treeview(
            list_frame,
            style='Files.Treeview',
            show='tree',
            selectmode='extended'
        )
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, command=self.file_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.configure(yscrollcommand=scrollbar.set)

        # 绑定事件
        self.file_tree.bind('<Double-1>', self._on_double_click)
        self.file_tree.bind('<Button-3>', self._on_right_click)

        # 拖放支持
        self._setup_drag_drop()

        # 保存文件信息
        self._files = {}

        # 进度条区域
        progress_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        progress_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.progress_label = tk.Label(
            progress_frame,
            text="",
            bg=self.BG_COLOR,
            fg=self.LABEL_COLOR,
            font=('Segoe UI', 8),
            anchor=tk.W
        )
        self.progress_label.pack(fill=tk.X, padx=8, pady=(4, 0))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=100
        )
        self.progress_bar.pack(fill=tk.X, padx=8, pady=(2, 4))
        self.progress_bar.pack_forget()

        # 底部选项
        options_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        options_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.follow_check = tk.Checkbutton(
            options_frame,
            text="跟随终端目录",
            variable=self._follow_terminal,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            activebackground=self.BG_COLOR,
            activeforeground=self.TEXT_COLOR,
            selectcolor=self.BG_COLOR,
            font=('Segoe UI', 9),
            command=self._on_follow_toggle
        )
        self.follow_check.pack(side=tk.LEFT, padx=8, pady=4)

        # 显示未连接提示
        self._show_disconnected()

    def _add_tooltip(self, widget, text):
        """添加工具提示"""
        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = tk.Label(tooltip, text=text, bg='#2d2d2d', fg='white',
                           font=('Segoe UI', 9), padx=6, pady=3)
            label.pack()
            widget._tooltip = tooltip
            widget.after(1500, lambda: tooltip.destroy() if hasattr(widget, '_tooltip') else None)

        def hide_tooltip(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                delattr(widget, '_tooltip')

        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def _setup_drag_drop(self):
        """设置拖放支持"""
        self.drop_label = tk.Label(
            self.file_tree,
            text="拖放文件到此处上传",
            bg=self.SELECT_BG,
            fg=self.ACCENT_COLOR,
            font=('Segoe UI', 10),
            pady=20
        )

        try:
            from tkinterdnd2 import DND_FILES
            self.file_tree.drop_target_register(DND_FILES)
            self.file_tree.dnd_bind('<<Drop>>', self._on_drop)
            self.file_tree.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.file_tree.dnd_bind('<<DragLeave>>', self._on_drag_leave)
        except ImportError:
            pass

    def _on_drag_enter(self, event):
        self.drop_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        return event.action

    def _on_drag_leave(self, event):
        self.drop_label.place_forget()

    def _on_drop(self, event):
        self.drop_label.place_forget()
        if not self.ssh_client:
            return

        files = self._parse_drop_data(event.data)
        if files:
            self._upload_files(files)

    def _parse_drop_data(self, data):
        files = []
        if data.startswith('{'):
            import re
            files = re.findall(r'\{([^}]+)\}', data)
        else:
            files = data.split()
        return [f for f in files if os.path.exists(f)]

    def _on_upload(self):
        if not self.ssh_client:
            messagebox.showwarning("提示", "未连接到服务器")
            return

        files = filedialog.askopenfilenames(title="选择要上传的文件")
        if files:
            self._upload_files(list(files))

    def _upload_files(self, local_files):
        if self._transferring:
            messagebox.showwarning("提示", "正在传输中，请稍候")
            return

        self._transferring = True
        self.progress_bar.pack(fill=tk.X, padx=8, pady=(2, 4))
        self.progress_bar['value'] = 0

        def upload():
            for i, local_path in enumerate(local_files):
                filename = os.path.basename(local_path)
                remote_path = f"{self.current_path}/{filename}"

                self.frame.after(0, lambda f=filename: self.progress_label.config(text=f"上传: {f}"))

                def progress_callback(transferred, total):
                    pct = int(transferred / total * 100) if total > 0 else 0
                    self.frame.after(0, lambda p=pct: self.progress_bar.config(value=p))

                try:
                    self.ssh_client.upload_file(local_path, remote_path, progress_callback)
                except Exception as e:
                    self.frame.after(0, lambda err=str(e): messagebox.showerror("上传失败", err))

            self.frame.after(0, self._upload_complete)

        threading.Thread(target=upload, daemon=True).start()

    def _upload_complete(self):
        self._transferring = False
        self.progress_label.config(text="上传完成")
        self.progress_bar['value'] = 100
        self.frame.after(2000, lambda: (
            self.progress_bar.pack_forget(),
            self.progress_label.config(text="")
        ))
        self._on_refresh()

    def _on_download(self):
        if not self.ssh_client:
            messagebox.showwarning("提示", "未连接到服务器")
            return

        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要下载的文件")
            return

        files_to_download = []
        for item_id in selection:
            if item_id in self._files:
                file_info = self._files[item_id]
                if file_info["path"] != "__parent__" and not file_info["is_dir"]:
                    files_to_download.append(file_info)

        if not files_to_download:
            messagebox.showwarning("提示", "请选择文件（非文件夹）")
            return

        save_dir = filedialog.askdirectory(title="选择保存位置")
        if not save_dir:
            return

        self._download_files(files_to_download, save_dir)

    def _download_files(self, files, save_dir):
        if self._transferring:
            messagebox.showwarning("提示", "正在传输中，请稍候")
            return

        self._transferring = True
        self.progress_bar.pack(fill=tk.X, padx=8, pady=(2, 4))
        self.progress_bar['value'] = 0

        def download():
            for file_info in files:
                filename = file_info["name"]
                remote_path = file_info["path"]
                local_path = os.path.join(save_dir, filename)

                self.frame.after(0, lambda f=filename: self.progress_label.config(text=f"下载: {f}"))

                def progress_callback(transferred, total):
                    pct = int(transferred / total * 100) if total > 0 else 0
                    self.frame.after(0, lambda p=pct: self.progress_bar.config(value=p))

                try:
                    self.ssh_client.download_file(remote_path, local_path, progress_callback)
                except Exception as e:
                    self.frame.after(0, lambda err=str(e): messagebox.showerror("下载失败", err))

            self.frame.after(0, self._download_complete)

        threading.Thread(target=download, daemon=True).start()

    def _download_complete(self):
        self._transferring = False
        self.progress_label.config(text="下载完成")
        self.progress_bar['value'] = 100
        self.frame.after(2000, lambda: (
            self.progress_bar.pack_forget(),
            self.progress_label.config(text="")
        ))

    def _on_refresh(self):
        if self.ssh_client:
            self._load_directory(self.current_path)

    def _on_mkdir(self):
        if not self.ssh_client:
            messagebox.showwarning("提示", "未连接到服务器")
            return

        dialog = tk.Toplevel(self.frame)
        dialog.title("新建文件夹")
        dialog.geometry("280x100")
        dialog.transient(self.frame)
        dialog.grab_set()
        dialog.configure(bg=self.BG_COLOR)

        tk.Label(dialog, text="文件夹名称:", bg=self.BG_COLOR, fg=self.TEXT_COLOR,
                font=('Segoe UI', 10)).pack(pady=(16, 6))
        entry = tk.Entry(dialog, width=30, font=('Segoe UI', 10))
        entry.pack(pady=4)
        entry.focus_set()

        def create():
            name = entry.get().strip()
            if name:
                try:
                    path = f"{self.current_path}/{name}"
                    self.ssh_client.mkdir(path)
                    dialog.destroy()
                    self._on_refresh()
                except Exception as e:
                    messagebox.showerror("错误", str(e))

        entry.bind('<Return>', lambda e: create())
        tk.Button(dialog, text="创建", command=create, font=('Segoe UI', 9),
                 bg=self.ACCENT_COLOR, fg='white', relief=tk.FLAT, padx=16).pack(pady=8)

    def _on_delete(self):
        if not self.ssh_client:
            return

        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的文件")
            return

        files_to_delete = []
        for item_id in selection:
            if item_id in self._files:
                file_info = self._files[item_id]
                if file_info["path"] != "__parent__":
                    files_to_delete.append(file_info)

        if not files_to_delete:
            return

        names = [f["name"] for f in files_to_delete]
        if not messagebox.askyesno("确认删除", f"确定要删除以下项目吗？\n{', '.join(names)}"):
            return

        def delete():
            for file_info in files_to_delete:
                try:
                    if file_info["is_dir"]:
                        self.ssh_client.rmdir(file_info["path"])
                    else:
                        self.ssh_client.remove(file_info["path"])
                except Exception as e:
                    self.frame.after(0, lambda err=str(e), n=file_info["name"]:
                        messagebox.showerror("删除失败", f"{n}: {err}"))

            self.frame.after(0, self._on_refresh)

        threading.Thread(target=delete, daemon=True).start()

    def _on_right_click(self, event):
        if not self.ssh_client:
            return

        item_id = self.file_tree.identify_row(event.y)
        if item_id:
            self.file_tree.selection_set(item_id)

        menu = tk.Menu(self.frame, tearoff=0, font=('Segoe UI', 9),
                      bg=self.BG_COLOR, fg=self.TEXT_COLOR,
                      activebackground=self.SELECT_BG, activeforeground=self.TEXT_COLOR)
        menu.add_command(label="上传文件", command=self._on_upload)
        menu.add_command(label="下载", command=self._on_download)
        menu.add_separator()
        menu.add_command(label="刷新", command=self._on_refresh)
        menu.add_command(label="新建文件夹", command=self._on_mkdir)
        menu.add_separator()
        menu.add_command(label="删除", command=self._on_delete)
        menu.tk_popup(event.x_root, event.y_root)

    def _show_disconnected(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.file_tree.insert('', 'end', text="  未连接")
        self.path_var.set("")
        self._files = {}

    def set_client(self, ssh_client: SSHClient):
        self.ssh_client = ssh_client

        def load():
            try:
                home = self.ssh_client.get_home_dir()
                self.current_path = home
                self.frame.after(0, lambda: self.path_var.set(home))
                self.frame.after(0, lambda: self._load_directory(home))
            except Exception as e:
                self.frame.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=load, daemon=True).start()

    def _load_directory(self, path: str):
        if not self.ssh_client:
            return

        def load():
            try:
                files = self.ssh_client.list_dir(path)
                self.current_path = path
                self.frame.after(0, lambda: self._display_files(files))
            except Exception as e:
                self.frame.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=load, daemon=True).start()

    def _display_files(self, files):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self._files = {}

        if self.current_path != "/":
            item_id = self.file_tree.insert('', 'end', text="  ..", image=self.folder_icon)
            self._files[item_id] = {"name": "..", "is_dir": True, "path": "__parent__"}

        for f in files:
            is_hidden = f.name.startswith('.')

            if f.is_dir:
                icon = self.hidden_folder_icon if is_hidden else self.folder_icon
            else:
                icon = self.hidden_file_icon if is_hidden else self.file_icon

            item_id = self.file_tree.insert('', 'end', text=f"  {f.name}", image=icon)
            self._files[item_id] = {"name": f.name, "is_dir": f.is_dir, "path": f.path}

        self.path_var.set(self.current_path)

    def _show_error(self, msg: str):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.file_tree.insert('', 'end', text=f"  错误: {msg}")
        self._files = {}

    def _on_double_click(self, event):
        selection = self.file_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        if item_id not in self._files:
            return

        file_info = self._files[item_id]

        if file_info["path"] == "__parent__":
            parent = os.path.dirname(self.current_path.rstrip('/'))
            if not parent:
                parent = "/"
            self._load_directory(parent)
        elif file_info["is_dir"]:
            self._load_directory(file_info["path"])

    def _on_path_enter(self, event):
        path = self.path_var.get().strip()
        if path:
            self._load_directory(path)

    def disconnect(self):
        self._stop_follow_monitor()
        self.ssh_client = None
        self._show_disconnected()

    def _on_follow_toggle(self):
        if self._follow_terminal.get():
            self._start_follow_monitor()
        else:
            self._stop_follow_monitor()

    def _start_follow_monitor(self):
        if self._follow_running or not self.ssh_client:
            return

        self._follow_running = True
        self._last_terminal_path = None
        self._shell_pid = None

        def find_shell_pid():
            try:
                cmd = '''
for pid in $(pgrep -u $USER bash 2>/dev/null; pgrep -u $USER zsh 2>/dev/null; pgrep -u $USER sh 2>/dev/null); do
    if [ -r "/proc/$pid/environ" ]; then
        conn=$(tr '\\0' '\\n' < /proc/$pid/environ 2>/dev/null | grep "^SSH_CONNECTION=" | cut -d= -f2-)
        if [ -n "$conn" ] && [ "$conn" = "$SSH_CONNECTION" ]; then
            ppid=$(ps -o ppid= -p $pid 2>/dev/null | tr -d ' ')
            pname=$(ps -o comm= -p $ppid 2>/dev/null)
            if [ "$pname" = "sshd" ]; then
                echo $pid
                exit 0
            fi
        fi
    fi
done
'''
                pid = self.ssh_client.exec_command(cmd).strip()
                return pid if pid else None
            except:
                return None

        def monitor():
            import time
            self._shell_pid = find_shell_pid()

            while self._follow_running and self.ssh_client:
                try:
                    if self._shell_pid:
                        pwd = self.ssh_client.exec_command(
                            f"readlink /proc/{self._shell_pid}/cwd 2>/dev/null"
                        ).strip()
                        if pwd and pwd != self._last_terminal_path:
                            self._last_terminal_path = pwd
                            self.frame.after(0, lambda p=pwd: self._navigate_to_path(p))
                    else:
                        self._shell_pid = find_shell_pid()
                except:
                    pass
                time.sleep(1)

        threading.Thread(target=monitor, daemon=True).start()

    def _stop_follow_monitor(self):
        self._follow_running = False

    def _navigate_to_path(self, path: str):
        if path and path != self.current_path:
            self._load_directory(path)

    def navigate_to(self, path: str):
        if self._follow_terminal.get() and path:
            self._navigate_to_path(path)
