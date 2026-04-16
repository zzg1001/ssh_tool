"""连接配置存储管理"""

import json
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from .crypto import crypto


@dataclass
class Connection:
    """SSH 连接配置"""
    id: str
    name: str
    host: str
    port: int
    username: str
    password: str  # 加密存储
    key_file: str  # SSH 私钥路径

    def to_dict(self) -> dict:
        """转换为字典，密码加密"""
        data = asdict(self)
        if self.password:
            data["password"] = crypto.encrypt(self.password)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Connection":
        """从字典创建，密码解密"""
        password = data.get("password", "")
        if password:
            password = crypto.decrypt(password)
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            host=data.get("host", ""),
            port=data.get("port", 22),
            username=data.get("username", ""),
            password=password,
            key_file=data.get("key_file", ""),
        )


class ConnectionStorage:
    """连接配置存储"""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".ssh_tool"
        self.config_dir = config_dir
        self.config_file = self.config_dir / "connections.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(mode=0o700)

    def _load_raw(self) -> list[dict]:
        """加载原始配置数据"""
        if not self.config_file.exists():
            return []
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_raw(self, data: list[dict]):
        """保存原始配置数据"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_connections(self) -> list[Connection]:
        """获取所有连接配置"""
        raw_data = self._load_raw()
        return [Connection.from_dict(item) for item in raw_data]

    def get_connection(self, conn_id: str) -> Optional[Connection]:
        """根据 ID 获取连接配置"""
        for conn in self.list_connections():
            if conn.id == conn_id:
                return conn
        return None

    def add_connection(self, conn: Connection) -> Connection:
        """添加新连接"""
        if not conn.id:
            conn.id = str(uuid.uuid4())
        raw_data = self._load_raw()
        raw_data.append(conn.to_dict())
        self._save_raw(raw_data)
        return conn

    def update_connection(self, conn: Connection) -> bool:
        """更新连接配置"""
        raw_data = self._load_raw()
        for i, item in enumerate(raw_data):
            if item.get("id") == conn.id:
                raw_data[i] = conn.to_dict()
                self._save_raw(raw_data)
                return True
        return False

    def delete_connection(self, conn_id: str) -> bool:
        """删除连接配置"""
        raw_data = self._load_raw()
        original_len = len(raw_data)
        raw_data = [item for item in raw_data if item.get("id") != conn_id]
        if len(raw_data) < original_len:
            self._save_raw(raw_data)
            return True
        return False


# 全局实例
storage = ConnectionStorage()
