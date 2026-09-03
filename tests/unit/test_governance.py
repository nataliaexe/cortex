"""Testes críticos para Governance"""
import pytest
from core.governance import Governance


def test_governance_validates_network_parameters():
    """Testa que Governance valida parâmetros de rede"""
    config = {"governance": {"allowed_paths": ["/tmp"]}}
    governance = Governance(config)

    # Testa ping sem host - deve falhar
    decision = governance.authorize("ping_host", {}, {})
    assert not decision.allowed
    assert "host deve ser especificado" in decision.reason

    # Testa ping com host válido - deve passar (se não estiver em confirmation_actions)
    decision = governance.authorize("ping_host", {"host": "127.0.0.1"}, {})
    assert decision.allowed


def test_governance_validates_dns_parameters():
    """Testa que Governance valida parâmetros DNS"""
    config = {"governance": {"allowed_paths": ["/tmp"]}}
    governance = Governance(config)

    # Testa DNS sem domain - deve falhar
    decision = governance.authorize("dns_lookup", {}, {})
    assert not decision.allowed
    assert "domain deve ser especificado" in decision.reason

    # Testa DNS com domain válido - deve passar
    decision = governance.authorize("dns_lookup", {"domain": "localhost"}, {})
    assert decision.allowed


def test_governance_validates_url_parameters():
    """Testa que Governance valida parâmetros de URL"""
    config = {"governance": {"allowed_paths": ["/tmp"], "require_confirmation": False}}
    governance = Governance(config)

    # Testa download sem URL - deve falhar
    decision = governance.authorize("download_file", {}, {})
    assert not decision.allowed
    assert "url deve ser especificada" in decision.reason

    # Testa download com URL válida - deve passar (sem confirmação obrigatória)
    decision = governance.authorize("download_file", {"url": "http://example.com/file"}, {})
    assert decision.allowed


def test_governance_blocks_dangerous_commands():
    """Testa que Governance bloqueia comandos perigosos"""
    config = {"governance": {"allowed_paths": ["/tmp"]}}
    governance = Governance(config)

    # Testa comando bloqueado
    with pytest.raises(PermissionError, match="Comando bloqueado"):
        governance.validate_command(["rm", "-rf", "/"])

    # Testa comando seguro
    argv = governance.validate_command(["ls", "-la"])
    assert argv == ["ls", "-la"]


def test_governance_path_validation():
    """Testa validação de caminhos"""
    config = {"governance": {"allowed_paths": ["/tmp"]}}
    governance = Governance(config)

    # Caminho permitido
    path = governance.ensure_path("/tmp/test.txt")
    assert str(path) == "/tmp/test.txt"

    # Caminho fora das áreas autorizadas
    with pytest.raises(PermissionError, match="Caminho fora das áreas autorizadas"):
        governance.ensure_path("/etc/passwd")


def test_governance_audit_log():
    """Testa que audit log funciona"""
    import tempfile
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            "governance": {
                "allowed_paths": [tmpdir],
                "audit_log": f"{tmpdir}/audit.jsonl"
            }
        }
        governance = Governance(config)

        # Executa uma ação
        decision = governance.authorize("write_file", {"path": f"{tmpdir}/test.txt"}, {})
        governance.audit("write_file", decision, params={"path": f"{tmpdir}/test.txt"})

        # Verifica que log foi criado
        with open(f"{tmpdir}/audit.jsonl", "r") as f:
            log_entry = json.loads(f.read())
            assert log_entry["action"] == "write_file"
            assert "timestamp" in log_entry
            assert "authorization" in log_entry