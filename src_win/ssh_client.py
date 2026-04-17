"""SSH 客户端模块，基于 paramiko"""

import socket
import threading
import stat
from typing import Optional, Callable
from dataclasses import dataclass

import paramiko

from .storage import Connection


@dataclass
class RemoteFile:
    """远程文件信息"""
    name: str
    path: str
    is_dir: bool
    size: int
    mtime: int


class SSHClient:
    """SSH 客户端封装"""

    def __init__(self, connection: Connection):
        self.connection = connection
        self.client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.Channel] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self._running = False

    def connect(self) -> bool:
        """建立 SSH 连接"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs = {
                "hostname": self.connection.host,
                "port": self.connection.port,
                "username": self.connection.username,
                "timeout": 10,
            }

            # 优先使用密钥认证
            if self.connection.key_file:
                connect_kwargs["key_filename"] = self.connection.key_file
            elif self.connection.password:
                connect_kwargs["password"] = self.connection.password

            self.client.connect(**connect_kwargs)
            return True

        except (paramiko.AuthenticationException,
                paramiko.SSHException,
                socket.error) as e:
            self.client = None
            raise ConnectionError(f"连接失败: {e}")

    def open_shell(self, cols: int = 80, rows: int = 24) -> paramiko.Channel:
        """打开交互式 shell"""
        if not self.client:
            raise RuntimeError("未连接")

        self.channel = self.client.get_transport().open_session()
        self.channel.get_pty(term="xterm-256color", width=cols, height=rows)
        self.channel.invoke_shell()
        self._running = True
        return self.channel

    def resize_pty(self, cols: int, rows: int):
        """调整终端大小"""
        if self.channel:
            self.channel.resize_pty(width=cols, height=rows)

    def send(self, data: str):
        """发送数据到远程"""
        if self.channel:
            self.channel.send(data)

    def send_bytes(self, data: bytes):
        """发送字节数据到远程"""
        if self.channel:
            self.channel.send(data)

    def start_read_thread(self, on_data: Callable[[bytes], None]):
        """启动读取线程"""
        def read_loop():
            while self._running and self.channel:
                if self.channel.recv_ready():
                    data = self.channel.recv(4096)
                    if data:
                        on_data(data)
                    else:
                        break

        thread = threading.Thread(target=read_loop, daemon=True)
        thread.start()
        return thread

    def exec_command(self, command: str, timeout: float = 5.0) -> str:
        """执行命令并返回输出"""
        if not self.client:
            raise RuntimeError("未连接")
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        return stdout.read().decode('utf-8', errors='replace')

    def close(self):
        """关闭连接"""
        self._running = False
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.channel:
            self.channel.close()
            self.channel = None
        if self.client:
            self.client.close()
            self.client = None

    # ===== SFTP 功能 =====
    def open_sftp(self) -> paramiko.SFTPClient:
        """打开 SFTP 会话"""
        if not self.client:
            raise RuntimeError("未连接")
        self.sftp = self.client.open_sftp()
        return self.sftp

    def list_dir(self, path: str = ".") -> list[RemoteFile]:
        """列出目录内容"""
        if not self.sftp:
            self.open_sftp()

        files = []
        try:
            for attr in self.sftp.listdir_attr(path):
                is_dir = stat.S_ISDIR(attr.st_mode)
                full_path = f"{path}/{attr.filename}" if path != "/" else f"/{attr.filename}"
                files.append(RemoteFile(
                    name=attr.filename,
                    path=full_path,
                    is_dir=is_dir,
                    size=attr.st_size or 0,
                    mtime=attr.st_mtime or 0,
                ))
        except Exception as e:
            pass

        # 排序：目录在前，文件在后
        files.sort(key=lambda f: (not f.is_dir, f.name.lower()))
        return files

    def get_home_dir(self) -> str:
        """获取用户主目录"""
        if not self.sftp:
            self.open_sftp()
        try:
            return self.sftp.normalize(".")
        except:
            return "/"

    def upload_file(self, local_path: str, remote_path: str, callback: Callable[[int, int], None] | None = None):
        """上传文件

        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            callback: 进度回调函数 (已传输字节, 总字节)
        """
        if not self.sftp:
            self.open_sftp()
        self.sftp.put(local_path, remote_path, callback=callback)

    def download_file(self, remote_path: str, local_path: str, callback: Callable[[int, int], None] | None = None):
        """下载文件

        Args:
            remote_path: 远程文件路径
            local_path: 本地文件路径
            callback: 进度回调函数 (已传输字节, 总字节)
        """
        if not self.sftp:
            self.open_sftp()
        self.sftp.get(remote_path, local_path, callback=callback)

    def mkdir(self, path: str):
        """创建远程目录"""
        if not self.sftp:
            self.open_sftp()
        self.sftp.mkdir(path)

    def remove(self, path: str):
        """删除远程文件"""
        if not self.sftp:
            self.open_sftp()
        self.sftp.remove(path)

    def rmdir(self, path: str):
        """删除远程目录"""
        if not self.sftp:
            self.open_sftp()
        self.sftp.rmdir(path)

    def stat(self, path: str):
        """获取文件信息"""
        if not self.sftp:
            self.open_sftp()
        return self.sftp.stat(path)

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.client is not None and self.client.get_transport() is not None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
