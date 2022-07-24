from pathlib import Path

from fastapi import Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.db import get_db_session
from models.platform import FirmwareInfo
from schemas.platform_schemas import FirmwareInfoSchema
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


@router.get("/info", response_model=FirmwareInfoSchema)
async def get_platform_info(session: Session = Depends(get_db_session)):
    """
    Return information about the platform such as the firmware version
    and features supported by the CPU.
    """

    db_firmware_info_result = (await session.execute(select(FirmwareInfo))).one_or_none()

    if db_firmware_info_result is None:
        sev_platform_status = sev_client.get_platform_status()
        firmware_info = FirmwareInfo(
            api_major=sev_platform_status.api_major,
            api_minor=sev_platform_status.api_minor,
            platform_state=sev_platform_status.platform_state,
            owner=sev_platform_status.owner,
            config=sev_platform_status.config,
            build=sev_platform_status.build,
        )
        session.add(firmware_info)

    else:
        firmware_info = db_firmware_info_result[0]

    return firmware_info
