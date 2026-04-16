"""密码加密/解密模块，使用 Fernet 对称加密"""

import os
from pathlib import Path
from cryptography.fernet import Fernet


class CryptoManager:
    """管理密码的加密和解密"""

    def __init__(self):
        self.key_dir = Path.home() / ".ssh_tool"
        self.key_file = self.key_dir / "key"
        self._fernet = None

    def _ensure_key(self) -> bytes:
        """确保密钥存在，不存在则生成"""
        if not self.key_dir.exists():
            self.key_dir.mkdir(mode=0o700)

        if self.key_file.exists():
            return self.key_file.read_bytes()

        key = Fernet.generate_key()
        self.key_file.write_bytes(key)
        os.chmod(self.key_file, 0o600)
        return key

    @property
    def fernet(self) -> Fernet:
        """获取 Fernet 实例"""
        if self._fernet is None:
            key = self._ensure_key()
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        """加密明文密码，返回 base64 编码的密文"""
        if not plaintext:
            return ""
        encrypted = self.fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密密文，返回明文密码"""
        if not ciphertext:
            return ""
        decrypted = self.fernet.decrypt(ciphertext.encode())
        return decrypted.decode()


# 全局实例
crypto = CryptoManager()
