from pathlib import Path

from fastapi.responses import FileResponse

from toolkit.sevtool import SevClient
from .router import router

SEV_DIR = Path.cwd().absolute() / "sev_files"


sev_client = SevClient(SEV_DIR)


@router.get("/certificates")
def get_sev_certificates():
    """
    Download the platform certificates as a ZIP file.
    """
    if not sev_client.certificates_archive.is_file():
        sev_client.export_certificates()

    return FileResponse(sev_client.certificates_archive)
