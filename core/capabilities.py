"""Safe, composable implementations for Cortex computer, network and web tools."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import os
import platform
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

import aiohttp
from .governance import Governance


def _psutil():
    """Import optional runtime dependency only for actions that need it."""
    try:
        import psutil
        return psutil
    except ImportError as error:
        raise RuntimeError("psutil não está instalado; execute pip install -r requirements.txt") from error


class ComputerControl:
    def __init__(self, governance: Governance):
        self.governance = governance

    def system_info(self) -> Dict[str, Any]:
        psutil = _psutil()
        return {"system": platform.system(), "release": platform.release(), "machine": platform.machine(),
                "hostname": platform.node(), "cpu_count": os.cpu_count(), "boot_time": psutil.boot_time()}

    def list_directory(self, path: str = ".") -> List[Dict[str, Any]]:
        directory = self.governance.ensure_path(path, must_exist=True)
        if not directory.is_dir():
            raise NotADirectoryError(str(directory))
        return [{"name": entry.name, "type": "directory" if entry.is_dir() else "file", "size": entry.stat().st_size if entry.is_file() else None}
                for entry in sorted(directory.iterdir(), key=lambda item: item.name.lower())]

    def read_file(self, path: str, max_bytes: int = 1_000_000) -> str:
        target = self.governance.ensure_path(path, must_exist=True)
        if not target.is_file():
            raise IsADirectoryError(str(target))
        with target.open("rb") as handle:
            data = handle.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"Arquivo excede limite de leitura ({max_bytes} bytes).")
        return data.decode("utf-8", errors="replace")

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        target = self.governance.ensure_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        backup = None
        if target.exists():
            backup = target.with_name(f"{target.name}.cortex-backup")
            backup.write_bytes(target.read_bytes())
        target.write_text(content, encoding="utf-8")
        return {"path": str(target), "backup": str(backup) if backup else None, "bytes": len(content.encode())}

    def run_command(self, command: Iterable[str], timeout: int = 30, cwd: str = ".") -> Dict[str, Any]:
        argv = self.governance.validate_command(command)
        workdir = self.governance.ensure_path(cwd, must_exist=True)
        result = subprocess.run(argv, cwd=workdir, capture_output=True, text=True, timeout=min(timeout, 300), shell=False)
        return {"success": result.returncode == 0, "returncode": result.returncode,
                "stdout": result.stdout[-20_000:], "stderr": result.stderr[-20_000:]}

    def processes(self, limit: int = 100) -> List[Dict[str, Any]]:
        psutil = _psutil()
        result = []
        for proc in psutil.process_iter(["pid", "name", "username", "status", "cpu_percent", "memory_percent"]):
            try:
                result.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return result[:limit]


class NetworkTools:
    """Diagnostics are constrained to local/private targets by default."""
    def __init__(self, config: Dict[str, Any]):
        network = config.get("network", {})
        self.allow_public_targets = network.get("allow_public_targets", False)
        self.max_port_scan = min(int(network.get("max_port_scan", 128)), 1024)

    def _authorize_target(self, host: str) -> str:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        if not self.allow_public_targets and not (ip.is_private or ip.is_loopback or ip.is_link_local):
            raise PermissionError("Alvos públicos não são permitidos; configure network.allow_public_targets para habilitar.")
        return str(ip)

    async def port_scan(self, host: str, ports: Iterable[int]) -> Dict[str, Any]:
        resolved = self._authorize_target(host)
        requested = list(dict.fromkeys(int(port) for port in ports))[:self.max_port_scan]
        if any(port < 1 or port > 65535 for port in requested):
            raise ValueError("Porta fora do intervalo 1..65535.")
        async def probe(port: int):
            try:
                _, writer = await asyncio.wait_for(asyncio.open_connection(resolved, port), timeout=0.4)
                writer.close(); await writer.wait_closed()
                return port
            except (OSError, asyncio.TimeoutError):
                return None
        results = await asyncio.gather(*(probe(port) for port in requested))
        return {"host": host, "resolved": resolved, "ports_scanned": requested, "open_ports": [port for port in results if port]}

    def connections(self) -> List[Dict[str, Any]]:
        psutil = _psutil()
        return [{"local": str(conn.laddr), "remote": str(conn.raddr), "status": conn.status, "pid": conn.pid, "type": conn.type}
                for conn in psutil.net_connections()]

    def traffic_summary(self) -> Dict[str, Any]:
        psutil = _psutil()
        counters = psutil.net_io_counters()
        return {"bytes_sent": counters.bytes_sent, "bytes_received": counters.bytes_recv,
                "packets_sent": counters.packets_sent, "packets_received": counters.packets_recv}

    def discover_local_devices(self) -> List[Dict[str, Any]]:
        """Reads the local neighbour table only; it never probes a network."""
        try:
            result = subprocess.run(["ip", "-j", "neigh", "show"], capture_output=True, text=True, timeout=5, check=True)
            return [{"ip": item.get("dst"), "mac": item.get("lladdr"), "interface": item.get("dev"), "state": item.get("state")}
                    for item in json.loads(result.stdout)]
        except (FileNotFoundError, subprocess.SubprocessError, json.JSONDecodeError):
            return []


class InternetTools:
    def __init__(self, config: Dict[str, Any], governance: Governance):
        internet = config.get("internet", {})
        self.enabled = internet.get("enabled", False)
        self.allowed_hosts = set(internet.get("allowed_hosts", []))
        self.max_download_bytes = int(internet.get("max_download_bytes", 25 * 1024 * 1024))
        self.governance = governance

    def _validate_url(self, url: str) -> None:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not self.enabled:
            raise PermissionError("Acesso à internet está desabilitado na configuração.")
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("URL deve usar HTTP(S) e possuir host.")
        # Default deny: allowed_hosts vazio significa nenhum host permitido
        if parsed.hostname not in self.allowed_hosts:
            raise PermissionError(f"Host '{parsed.hostname}' não está na lista autorizada. Configure internet.allowed_hosts explicitamente.")

    async def request(self, url: str, method: str = "GET") -> Dict[str, Any]:
        self._validate_url(url)
        async with aiohttp.ClientSession() as session:
            async with session.request(method.upper(), url, allow_redirects=False, timeout=aiohttp.ClientTimeout(total=20)) as response:
                body = await response.content.read(1_000_001)
                return {"url": url, "status": response.status, "headers": dict(response.headers), "body": body.decode(errors="replace")[:1_000_000]}

    async def download(self, url: str, destination: str, expected_sha256: str | None = None) -> Dict[str, Any]:
        self._validate_url(url)
        target = self.governance.ensure_path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".part")
        digest = hashlib.sha256(); total = 0
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=False, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status != 200:
                    raise ValueError(f"Download recusado: HTTP {response.status}")
                with temporary.open("wb") as output:
                    async for chunk in response.content.iter_chunked(64 * 1024):
                        total += len(chunk)
                        if total > self.max_download_bytes:
                            raise ValueError("Download excede limite configurado.")
                        digest.update(chunk); output.write(chunk)
        checksum = digest.hexdigest()
        if expected_sha256 and checksum.lower() != expected_sha256.lower():
            temporary.unlink(missing_ok=True)
            raise ValueError("SHA-256 não corresponde ao valor esperado.")
        temporary.replace(target)
        return {"path": str(target), "bytes": total, "sha256": checksum, "executed": False}
