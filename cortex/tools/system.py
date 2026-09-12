"""Tools de sistema. Volume, brilho, notificacao, clipboard, screenshot, open.

Todas usam binarios do sistema. X11 + PulseAudio + XFCE (ambiente alvo).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from cortex.governance.dry_run import DryRunPreview
from cortex.tools.base import BaseTool, ToolContext, ToolResult


def _run(argv: list[str], timeout: int = 10) -> tuple[int, str, str]:
    """Roda comando, retorna (rc, stdout, stderr)."""
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", f"comando nao encontrado: {argv[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout de {timeout}s"
    except OSError as e:
        return 1, "", f"erro: {e}"


def _which(name: str) -> str | None:
    return shutil.which(name)


# ------------------------------------------------------------------
# Volume (pactl)
# ------------------------------------------------------------------

class VolumeTool(BaseTool):
    name = "system.volume"
    description = (
        "Controla o volume do sistema. Acoes: get, set, up, down, mute, unmute, toggle_mute. "
        "Para set, use o parametro level (0-100). Para up/down, use step (padrao 5)."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get", "set", "up", "down", "mute", "unmute", "toggle_mute"],
            },
            "level": {"type": "integer", "minimum": 0, "maximum": 150},
            "step": {"type": "integer", "default": 5},
        },
        "required": ["action"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        action = args.get("action")
        if _which("pactl") is None:
            return ToolResult(ok=False, error="pactl nao instalado")

        if action == "get":
            rc, out, err = _run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
            if rc != 0:
                return ToolResult(ok=False, error=err)
            # pega o primeiro percentual
            import re
            m = re.search(r"(\d+)%", out)
            vol = m.group(1) if m else "?"
            return ToolResult(ok=True, output=f"volume atual: {vol}%")

        if action == "set":
            lvl = args.get("level")
            if lvl is None:
                return ToolResult(ok=False, error="parametro 'level' obrigatorio para action=set")
            rc, _, err = _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{lvl}%"])
            if rc != 0:
                return ToolResult(ok=False, error=err)
            return ToolResult(ok=True, output=f"volume definido para {lvl}%")

        if action in ("up", "down"):
            step = args.get("step", 5)
            sign = "+" if action == "up" else "-"
            rc, _, err = _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{sign}{step}%"])
            if rc != 0:
                return ToolResult(ok=False, error=err)
            return ToolResult(ok=True, output=f"volume {action} em {step}%")

        if action == "mute":
            rc, _, err = _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"])
            return ToolResult(ok=(rc == 0), output="mudo" if rc == 0 else "", error=err if rc != 0 else None)

        if action == "unmute":
            rc, _, err = _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"])
            return ToolResult(ok=(rc == 0), output="som ativo" if rc == 0 else "", error=err if rc != 0 else None)

        if action == "toggle_mute":
            rc, _, err = _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
            return ToolResult(ok=(rc == 0), output="mute alternado" if rc == 0 else "", error=err if rc != 0 else None)

        return ToolResult(ok=False, error=f"action desconhecida: {action}")


# ------------------------------------------------------------------
# Brilho (brightnessctl)
# ------------------------------------------------------------------

class BrightnessTool(BaseTool):
    name = "system.brightness"
    description = (
        "Controla o brilho da tela. Acoes: get, set, up, down. "
        "Para set, use level (0-100). Para up/down, use step (padrao 10)."
    )
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["get", "set", "up", "down"]},
            "level": {"type": "integer", "minimum": 1, "maximum": 100},
            "step": {"type": "integer", "default": 10},
        },
        "required": ["action"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        action = args.get("action")

        if _which("brightnessctl") is None:
            return ToolResult(ok=False, error="brightnessctl nao instalado")

        if action == "get":
            rc, out, err = _run(["brightnessctl", "get"])
            rc2, out2, _ = _run(["brightnessctl", "max"])
            if rc != 0:
                return ToolResult(ok=False, error=err)
            try:
                cur = int(out.strip())
                mx = int(out2.strip())
                pct = round(cur / mx * 100)
                return ToolResult(ok=True, output=f"brilho atual: {pct}%")
            except Exception:
                return ToolResult(ok=True, output=f"brilho atual: {out.strip()}")

        if action == "set":
            lvl = args.get("level")
            if lvl is None:
                return ToolResult(ok=False, error="parametro 'level' obrigatorio")
            rc, _, err = _run(["brightnessctl", "set", f"{lvl}%"])
            if rc != 0:
                return ToolResult(ok=False, error=err or "falha ao definir brilho (precisa de permissao?)")
            return ToolResult(ok=True, output=f"brilho definido para {lvl}%")

        if action in ("up", "down"):
            step = args.get("step", 10)
            op = "+" if action == "up" else "-"
            rc, _, err = _run(["brightnessctl", "set", f"{step}%{op}"])
            if rc != 0:
                return ToolResult(ok=False, error=err)
            return ToolResult(ok=True, output=f"brilho {action} em {step}%")

        return ToolResult(ok=False, error=f"action desconhecida: {action}")


# ------------------------------------------------------------------
# Notificacao (notify-send)
# ------------------------------------------------------------------

class NotifyTool(BaseTool):
    name = "system.notify"
    description = "Envia uma notificacao desktop. Parametros: title (obrigatorio), body (opcional), urgency (low|normal|critical)."
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "body": {"type": "string"},
            "urgency": {"type": "string", "enum": ["low", "normal", "critical"]},
        },
        "required": ["title"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        if _which("notify-send") is None:
            return ToolResult(ok=False, error="notify-send nao instalado (apt install libnotify-bin)")
        title = args.get("title", "Cortex")
        body = args.get("body", "")
        urgency = args.get("urgency", "normal")

        argv = ["notify-send", "-u", urgency, "-a", "Cortex", title]
        if body:
            argv.append(body)

        rc, _, err = _run(argv)
        if rc != 0:
            return ToolResult(ok=False, error=err)
        return ToolResult(ok=True, output=f"notificacao enviada: {title}")


# ------------------------------------------------------------------
# Abrir arquivo/URL (xdg-open)
# ------------------------------------------------------------------

class OpenTool(BaseTool):
    name = "system.open"
    description = "Abre uma URL ou arquivo com o aplicativo padrao do sistema. Parametro: target (URL ou path)."
    destructive = False
    schema = {
        "type": "object",
        "properties": {"target": {"type": "string"}},
        "required": ["target"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        if _which("xdg-open") is None:
            return ToolResult(ok=False, error="xdg-open nao instalado")
        target = args.get("target", "").strip()
        if not target:
            return ToolResult(ok=False, error="target obrigatorio")

        # precisa de DISPLAY para funcionar
        if not os.environ.get("DISPLAY"):
            return ToolResult(ok=False, error="DISPLAY nao definido (ambiente sem GUI?)")

        rc, _, err = _run(["xdg-open", target], timeout=5)
        # xdg-open retorna rapido, o app abre em background
        return ToolResult(ok=(rc == 0), output=f"abrindo: {target}", error=err if rc != 0 else None)


# ------------------------------------------------------------------
# Clipboard (xclip)
# ------------------------------------------------------------------

class ClipboardTool(BaseTool):
    name = "system.clipboard"
    description = "Le ou escreve na area de transferencia. Acoes: get, set. Para set, use text."
    destructive = False
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["get", "set"]},
            "text": {"type": "string"},
        },
        "required": ["action"],
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        if _which("xclip") is None:
            return ToolResult(ok=False, error="xclip nao instalado")
        action = args.get("action")

        if action == "get":
            rc, out, err = _run(["xclip", "-selection", "clipboard", "-o"])
            if rc != 0:
                return ToolResult(ok=False, error=err or "clipboard vazio")
            return ToolResult(ok=True, output=out.strip())

        if action == "set":
            text = args.get("text", "")
            try:
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text, text=True, timeout=5, check=False
                )
                if proc.returncode != 0:
                    return ToolResult(ok=False, error="falha ao escrever no clipboard")
                return ToolResult(ok=True, output=f"clipboard atualizado ({len(text)} chars)")
            except Exception as e:
                return ToolResult(ok=False, error=str(e))

        return ToolResult(ok=False, error=f"action desconhecida: {action}")


# ------------------------------------------------------------------
# Screenshot (scrot)
# ------------------------------------------------------------------

class ScreenshotTool(BaseTool):
    name = "system.screenshot"
    description = "Tira um screenshot da tela inteira e salva em ~/cortex/data/screenshots/. Opcional: nome customizado."
    destructive = False
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        if _which("scrot") is None:
            return ToolResult(ok=False, error="scrot nao instalado (apt install scrot)")

        outdir = Path.home() / "cortex" / "data" / "screenshots"
        outdir.mkdir(parents=True, exist_ok=True)

        name = args.get("name") or datetime.now().strftime("shot_%Y%m%d_%H%M%S")
        outfile = outdir / f"{name}.png"

        rc, _, err = _run(["scrot", "-z", str(outfile)])
        if rc != 0:
            return ToolResult(ok=False, error=err or "falha ao tirar screenshot")
        return ToolResult(ok=True, output=f"screenshot salvo: {outfile}", meta={"path": str(outfile)})
