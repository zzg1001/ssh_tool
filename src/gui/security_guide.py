"""安全设置引导界面"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys

# 配置文件路径
CONFIG_DIR = os.path.expanduser("~/.sshtool")
FIRST_RUN_FLAG = os.path.join(CONFIG_DIR, ".first_run_done")


class SecurityGuideDialog:
    """首次运行安全引导对话框"""

    def __init__(self, parent=None):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("zzgShell - 首次使用设置")
        self.root.geometry("480x420")
        self.root.resizable(False, False)

        # 居中显示
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 480) // 2
        y = (self.root.winfo_screenheight() - 420) // 2
        self.root.geometry(f"480x420+{x}+{y}")

        # 设置为模态窗口
        if parent:
            self.root.transient(parent)
            self.root.grab_set()

        self.result = False
        self._create_widgets()

    def _create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="欢迎使用 zzgShell",
            font=("SF Pro Display", 20, "bold")
        )
        title_label.pack(pady=(0, 15))

        # 说明文字
        desc_label = ttk.Label(
            main_frame,
            text="首次运行需要完成安全设置",
            font=("SF Pro Text", 13),
            justify=tk.CENTER,
            foreground="#666666"
        )
        desc_label.pack(pady=(0, 20))

        # 状态标签
        self.status_label = ttk.Label(
            main_frame,
            text="正在设置...",
            font=("SF Pro Text", 14)
        )
        self.status_label.pack(pady=20)

        # 进度提示
        self.hint_label = ttk.Label(
            main_frame,
            text="请在弹出的窗口中输入电脑密码",
            font=("SF Pro Text", 11),
            foreground="#888888"
        )
        self.hint_label.pack(pady=10)

        # 完成按钮（初始隐藏）
        self.done_btn = tk.Button(
            main_frame,
            text="开始使用",
            command=self._on_done,
            font=("SF Pro Text", 14, "bold"),
            bg="#007AFF",
            fg="white",
            width=15,
            height=2,
            relief=tk.FLAT
        )

        # 自动执行设置
        self.root.after(500, self._auto_setup)

    def _auto_setup(self):
        """自动执行安全设置"""
        app_path = self._get_app_path()
        if not app_path:
            self.status_label.config(text="设置失败", foreground="red")
            self.hint_label.config(text="无法确定应用路径")
            self.done_btn.pack(pady=20)
            return

        # 使用 AppleScript 请求管理员权限执行命令
        script = f'''
        do shell script "xattr -cr \\"{app_path}\\"" with administrator privileges
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            self._mark_first_run_done()
            self.status_label.config(text="✓ 设置完成", foreground="green")
            self.hint_label.config(text="")
            self.done_btn.pack(pady=20)
            # 2秒后自动关闭
            self.root.after(2000, self._on_done)
        except subprocess.CalledProcessError:
            self.status_label.config(text="已取消", foreground="orange")
            self.hint_label.config(text="您可以稍后再设置，现在直接使用")
            self.done_btn.config(text="直接使用")
            self.done_btn.pack(pady=20)
        except Exception as e:
            self.status_label.config(text="设置失败", foreground="red")
            self.hint_label.config(text=str(e))
            self.done_btn.pack(pady=20)

    def _open_security_settings(self):
        """打开系统设置的隐私与安全性页面"""
        subprocess.Popen([
            "open",
            "x-apple.systempreferences:com.apple.preference.security?General"
        ])

    def _try_auto_fix(self):
        """尝试自动移除隔离属性"""
        app_path = self._get_app_path()
        if not app_path:
            self.status_label.config(text="无法确定应用路径", foreground="red")
            return

        # 使用 AppleScript 请求管理员权限执行命令
        script = f'''
        do shell script "xattr -cr \\"{app_path}\\"" with administrator privileges
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            # 标记首次运行完成
            self._mark_first_run_done()
            self.status_label.config(text="设置成功！", foreground="green")
            self.root.after(800, self._on_done)  # 0.8秒后自动关闭
        except subprocess.CalledProcessError:
            self.status_label.config(text="已取消或失败，可点击「跳过」继续使用", foreground="orange")
        except Exception as e:
            self.status_label.config(text=f"发生错误: {e}", foreground="red")

    def _mark_first_run_done(self):
        """标记首次运行完成"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(FIRST_RUN_FLAG, 'w') as f:
                f.write("done")
        except:
            pass

    def _get_app_path(self):
        """获取应用路径"""
        # 尝试多种方式获取应用路径
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包的应用
            return os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
        else:
            # 开发环境，尝试找到 .app
            current = os.path.dirname(os.path.abspath(__file__))
            while current != '/':
                if current.endswith('.app'):
                    return current
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent
            # 尝试默认路径
            possible_paths = [
                os.path.join(os.getcwd(), "zzgShell.app"),
                "/Applications/zzgShell.app",
                os.path.expanduser("~/Applications/zzgShell.app"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        return None

    def _show_message(self, message, msg_type="info"):
        """显示消息"""
        # 创建提示标签
        colors = {
            "success": "#28a745",
            "error": "#dc3545",
            "info": "#007AFF"
        }

        # 移除旧的消息标签
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and hasattr(widget, '_is_message'):
                widget.destroy()

        msg_label = tk.Label(
            self.root,
            text=message,
            font=("SF Pro Text", 12),
            fg=colors.get(msg_type, "black"),
            bg=self.root.cget('bg')
        )
        msg_label._is_message = True
        msg_label.place(relx=0.5, rely=0.85, anchor=tk.CENTER)

    def _on_done(self):
        """完成按钮点击"""
        self.result = True
        self.root.destroy()

    def show(self):
        """显示对话框并等待"""
        self.root.mainloop()
        return self.result


def is_first_run():
    """检查是否是首次运行"""
    return not os.path.exists(FIRST_RUN_FLAG)


def check_and_show_guide():
    """检查是否需要显示安全引导"""
    # 如果已经完成过首次设置，直接返回
    if not is_first_run():
        return True

    # 首次运行，直接请求系统认证
    app_path = _get_app_path()
    if app_path:
        script = f'''
        do shell script "xattr -cr \\"{app_path}\\"" with administrator privileges
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True)
        except:
            pass  # 用户取消或失败，继续使用

    # 标记首次运行完成
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(FIRST_RUN_FLAG, 'w') as f:
            f.write("done")
    except:
        pass

    return True


def _get_app_path():
    """获取应用路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
    else:
        current = os.path.dirname(os.path.abspath(__file__))
        while current != '/':
            if current.endswith('.app'):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        possible_paths = [
            os.path.join(os.getcwd(), "zzgShell.app"),
            "/Applications/zzgShell.app",
            os.path.expanduser("~/Applications/zzgShell.app"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    return None


def show_guide_dialog(parent=None):
    """显示安全引导对话框"""
    dialog = SecurityGuideDialog(parent)
    return dialog.show()


if __name__ == "__main__":
    # 测试
    dialog = SecurityGuideDialog()
    result = dialog.show()
    print(f"Result: {result}")
