from fastapi import APIRouter, HTTPException

from core.governance import Governance
from database.repositories.scan_repository import ScanRepository


def router(config: dict, scans: ScanRepository) -> APIRouter:
    api = APIRouter(prefix="/api/security", tags=["security"])

    @api.get("/scan")
    def scan(path: str = "."):
        from security.universal_scanner import UniversalScanner
        try:
            target = Governance(config).ensure_path(path, must_exist=True)
            result = UniversalScanner(config).scan_directory(str(target)) if target.is_dir() else UniversalScanner(config).scan_file(str(target))
            return {"scan_id": scans.record(str(target), "source", result), "result": result}
        except (PermissionError, FileNotFoundError) as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @api.get("/dependencies")
    def dependencies(path: str = "."):
        from security.dependency_checker import DependencyChecker
        try:
            target = Governance(config).ensure_path(path, must_exist=True)
            result = DependencyChecker(config).check_directory(str(target))
            return {"scan_id": scans.record(str(target), "dependencies", result), "result": result}
        except (PermissionError, FileNotFoundError) as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    return api
