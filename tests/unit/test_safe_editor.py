"""Testes críticos para SafeEditor corrigido"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from core.self_modification.safe_editor import SafeEditor


def test_safe_editor_aborts_on_content_mismatch():
    """Testa que SafeEditor aborta se conteúdo original não corresponde"""
    config = {"self_modification": {"backup_before_changes": True}}
    editor = SafeEditor(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("conteúdo original")

        # Tenta editar com old_content incorreto
        result = asyncio.run(editor.edit_file(
            str(test_file),
            "conteúdo errado",  # old_content incorreto
            "novo conteúdo",
            "teste"
        ))

        # Deve falhar
        assert result is False

        # Arquivo não deve ter sido modificado
        assert test_file.read_text() == "conteúdo original"


def test_safe_editor_succeeds_with_correct_content():
    """Testa que SafeEditor funciona com conteúdo correto"""
    config = {"self_modification": {"backup_before_changes": True}}
    editor = SafeEditor(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("conteúdo original")

        # Edita com old_content correto
        result = asyncio.run(editor.edit_file(
            str(test_file),
            "conteúdo original",  # old_content correto
            "novo conteúdo",
            "teste"
        ))

        # Deve ter sucesso
        assert result is True

        # Arquivo deve ter sido modificado
        assert test_file.read_text() == "novo conteúdo"


def test_safe_editor_creates_backup():
    """Testa que SafeEditor cria backup antes de editar"""
    config = {"self_modification": {"backup_before_changes": True}}
    editor = SafeEditor(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("conteúdo original")

        # Edita arquivo
        asyncio.run(editor.edit_file(
            str(test_file),
            "conteúdo original",
            "novo conteúdo",
            "teste"
        ))

        # Verifica que backup foi criado
        backups = asyncio.run(editor.list_backups(str(test_file)))
        assert len(backups) > 0


def test_safe_editor_rollback():
    """Testa rollback para backup"""
    config = {"self_modification": {"backup_before_changes": True}}
    editor = SafeEditor(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("conteúdo original")

        # Edita arquivo
        asyncio.run(editor.edit_file(
            str(test_file),
            "conteúdo original",
            "novo conteúdo",
            "teste"
        ))

        # Lista backups
        backups = asyncio.run(editor.list_backups(str(test_file)))
        assert len(backups) >= 1

        # Rollback para o backup
        backup_timestamp = backups[0]["timestamp"]
        result = asyncio.run(editor.rollback(str(test_file), backup_timestamp))

        assert result is True
        assert test_file.read_text() == "conteúdo original"


def test_safe_editor_integrity_verification():
    """Testa verificação de integridade"""
    config = {"self_modification": {"backup_before_changes": True}}
    editor = SafeEditor(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("conteúdo de teste")

        # Calcula hash
        expected_hash = editor._calculate_hash(test_file)

        # Verifica integridade
        result = asyncio.run(editor.verify_integrity(str(test_file), expected_hash))
        assert result is True

        # Modifica arquivo
        test_file.write_text("conteúdo modificado")

        # Verifica integridade novamente
        result = asyncio.run(editor.verify_integrity(str(test_file), expected_hash))
        assert result is False