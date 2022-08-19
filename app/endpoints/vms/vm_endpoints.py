import base64
import shutil
import tarfile
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import aiofile
from fastapi import Depends, File, HTTPException, UploadFile, status, Query
from sqlalchemy.orm import Session

from authentication import get_current_username
from models.db import get_db_session
from models.vm import Vm, VmImage, VmState, fetch_vm
from schemas.vm_schemas import VmSchema, VmImagePostSchema, VmStartResponseSchema
from settings import settings
from toolkit.qemu import qemu_create_vm, QemuVmClient
from .router import router

DOWNLOAD_DIR = Path(__file__).absolute().parent / "downloads"
GUEST_OWNER_CERTIFICATE_FILES = "godh.cert", "launch_blob.bin"


def get_vm_dir(vm: Vm) -> Path:
    return DOWNLOAD_DIR / vm.id


async def write_uploaded_file(download_dir: Path, file: UploadFile) -> Path:
    # Ensure that the output directory exists
    download_dir.mkdir(parents=True, exist_ok=True)
    file_path = download_dir / file.filename

    async with aiofile.async_open(file_path, "wb") as f:
        while content := await file.read(1024):
            await f.write(content)

    return file_path


async def fetch_vm_and_check_ownership(
    session: Session, vm_id: str, username: str
) -> Vm:
    vm = await fetch_vm(session, vm_id)
    if vm is None or vm.owner != username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VM not found"
        )

    return vm


@router.post("/vm", response_model=VmSchema)
async def create_vm(
    memory: int = Query(
        default=settings.vm_default_memory,
        title="RAM allocated to the VM, in MB",
        gt=settings.vm_min_memory,
        lt=settings.vm_max_memory,
    ),
    number_of_cores: int = Query(
        default=settings.vm_default_number_of_cores,
        title="Number of cores for the VM",
        gt=0,
        lt=settings.vm_max_number_of_cores,
    ),
    session: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    vm = Vm(
        id=uuid4().hex,
        state=VmState.STOPPED,
        memory=memory,
        number_of_cores=number_of_cores,
        owner=username,
    )
    session.add(vm)
    # Let the DB set the creation datetime field
    await session.flush()
    return vm


@router.get("/vm/{vm_id}", response_model=VmSchema)
async def get_vm(
    vm_id: str,
    session: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    vm = await fetch_vm_and_check_ownership(session, vm_id, username)
    if vm is None or vm.owner != username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VM not found"
        )
    return vm


@router.post("/vm/{vm_id}/upload-image", response_model=VmImagePostSchema)
async def upload_vm_image(
    vm_id: str,
    image_name: str,
    vm_image_tarball: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    vm = await fetch_vm_and_check_ownership(session, vm_id, username)
    if vm is None or vm.owner != username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VM not found"
        )

    vm_download_dir = get_vm_dir(vm)
    vm_download_dir.mkdir(parents=True, exist_ok=True)

    tarball_path = await write_uploaded_file(vm_download_dir, vm_image_tarball)

    # TODO: determine when to extract the tarball (maybe at VM init?)
    with tarfile.open(tarball_path) as tf:
        tf.extract(image_name, path=vm_download_dir)

    vm.image = VmImage(id=uuid4().hex, filename=image_name)
    session.add(vm.image)
    await session.flush()

    return VmImagePostSchema(
        vm_id=vm.id,
        filename=vm.image.filename,
        upload_datetime=vm.image.upload_datetime,
    )


@router.post("/vm/{vm_id}/upload-guest-owner-certificates")
async def upload_guest_owner_certificates(
    vm_id: str,
    guest_owner_certificates: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    vm = await fetch_vm_and_check_ownership(session, vm_id, username)

    if vm.state != VmState.STOPPED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"VM is already started. Current state: '{vm.state}'.",
        )

    vm_download_dir = get_vm_dir(vm)
    vm_download_dir.mkdir(parents=True, exist_ok=True)

    archive_path = await write_uploaded_file(vm_download_dir, guest_owner_certificates)

    with ZipFile(archive_path) as zip_file:
        zip_file.extractall(path=vm_download_dir, members=GUEST_OWNER_CERTIFICATE_FILES)

    # Convert to base64 for later use with Qemu
    for filename in GUEST_OWNER_CERTIFICATE_FILES:
        bin_file = vm_download_dir / filename
        b64_filename = bin_file.stem + "-b64.txt"
        b64_file = vm_download_dir / b64_filename
        with bin_file.open("rb") as bin_fh, b64_file.open("wb") as b64_fh:
            base64_content = base64.b64encode(bin_fh.read())
            b64_fh.write(base64_content)


def validate_sev_policy(sev_policy_str: str) -> None:
    try:
        _policy = int(sev_policy_str, base=16)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid SEV policy: policy is not a hexadecimal number",
        )


@router.post("/vm/{vm_id}/start", response_model=VmSchema)
async def start_vm(
    vm_id: str,
    sev_policy: str = Query(..., title="SEV policy (hexadecimal format)"),
    session: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    vm = await fetch_vm_and_check_ownership(session, vm_id, username)

    if vm.state != VmState.STOPPED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"VM is already started. Current state: '{vm.state}'.",
        )

    validate_sev_policy(sev_policy)
    vm.sev_policy = sev_policy

    vm_dir = get_vm_dir(vm)

    # For demo purposes: if the user did not upload an image, copy the default image
    if vm.image is None:
        default_image = settings.default_image_path
        shutil.copy2(default_image, vm_dir / default_image.name)
        vm.image = VmImage(id=uuid4().hex, filename=default_image.name)

    qemu_create_vm(
        vm=vm,
        working_dir=vm_dir,
        ovmf_path=settings.ovmf_path,
    )

    return vm


@router.get("/vm/{vm_id}/sev/measure", response_model=VmStartResponseSchema)
async def get_vm_measure(
    vm_id: str,
    session: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    vm = await fetch_vm_and_check_ownership(session, vm_id, username)
    if vm.state != VmState.STARTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"VM must be started and waiting for launch. Current state: '{vm.state}'.",
        )

    with QemuVmClient(vm) as vm_client:
        vm_sev_info = vm_client.query_sev_info()
        launch_measure = vm_client.query_launch_measure()

    return {"vm": vm, "sev_info": vm_sev_info, "launch_measure": launch_measure}


@router.post("/vm/{vm_id}/sev/inject-secret", response_model=VmSchema)
async def inject_vm_secrets(
    vm_id: str,
    packet_header: str,
    secret: str,
    session: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    vm = await fetch_vm_and_check_ownership(session, vm_id, username)

    if vm.state != VmState.STARTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot inject secret in a VM in state '{vm.state}'.",
        )

    with QemuVmClient(vm) as vm_client:
        vm_client.inject_secret(packet_header, secret)
        vm_client.continue_execution()

    vm.state = VmState.RUNNING
    return vm
