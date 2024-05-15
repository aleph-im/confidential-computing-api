import subprocess
from dataclasses import dataclass
from pathlib import Path

import qmp
from cpuid.features import secure_encryption_info

from models.vm import Vm, VmState
from toolkit.network import find_available_port


@dataclass
class VmSevInfo:
    enabled: bool
    api_major: int
    api_minor: int
    build_id: int
    policy: int
    state: str
    handle: int


class QemuVmClient:
    def __init__(self, vm: Vm):
        self.vm = vm

        if vm.qmp_port is None:
            raise ValueError(
                "VM does not have a QMP port specified. Is the VM started?"
            )

        qmp_client = qmp.QEMUMonitorProtocol(address=("localhost", vm.qmp_port))
        qmp_client.connect()
        self.qmp_client = qmp_client

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        self.qmp_client.close()

    def query_sev_info(self) -> VmSevInfo:
        caps = self.qmp_client.command("query-sev")
        return VmSevInfo(
            enabled=caps["enabled"],
            api_major=caps["api-major"],
            api_minor=caps["api-minor"],
            handle=caps["handle"],
            state=caps["state"],
            build_id=caps["build-id"],
            policy=caps["policy"],
        )

    def query_launch_measure(self) -> str:
        measure = self.qmp_client.command("query-sev-launch-measure")
        return measure["data"]

    def inject_secret(self, packet_header: str, secret: str) -> None:
        """
        Injects the secret in the SEV secret area.

        :param packet_header: The packet header, as a base64 string.
        :param secret: The encoded secret, as a base64 string.
        """

        self.qmp_client.command(
            "sev-inject-launch-secret",
            **{"packet-header": packet_header, "secret": secret},
        )

    def continue_execution(self) -> None:
        """
        Resumes the execution of the VM.
        """
        self.qmp_client.command("cont")


def qemu_create_vm(vm: Vm, working_dir: Path, ovmf_path: Path):
    """
    Starts the Qemu VM process in wait mode. This creates the VM and allocates the resources
    but waits for user interaction with QMP to start the guest.
    :param vm: The VM to start.
    :param working_dir: Working directory for the Qemu process.
    :param ovmf_path: Path to the OVMF binary.
    """
    ssh_port = find_available_port()
    qmp_port = find_available_port()

    godh = Path(working_dir) / "vm_godh.b64"
    launch_blob = Path(working_dir) / "vm_session.b64"


    if not (godh.is_file() and launch_blob.is_file()):
        raise FileNotFoundError("Missing guest owner certificates, cannot start the VM.")

    # TODO: this should be called only once, and we should have a generic abstraction
    #       to support SEV + TDX. This will do for now.
    sev_info = secure_encryption_info()
    if sev_info is None:
        raise ValueError("Not running on an AMD SEV platform?")

    p = subprocess.Popen(
        [
            "qemu-system-x86_64",
            "-enable-kvm",
            "-m",
            f"{vm.memory}",
            "-smp",
            f"{vm.number_of_cores}",
            "-drive",
            f"if=pflash,format=raw,unit=0,file={ovmf_path},readonly=on",
            "-drive",
            f"format=raw,file={vm.image.filename}",
            "-nographic",
            "-chardev",
            "file,id=char0,path=serial.log",
            "-serial",
            "chardev:char0",
            "-netdev",
            f"user,id=net0,hostfwd=tcp::{ssh_port}-:22",
            "-device",
            "virtio-net-pci,netdev=net0",
            "-object",
            f"sev-guest,id=sev0,policy={vm.sev_policy},cbitpos={sev_info.c_bit_position},"
            f"reduced-phys-bits={sev_info.phys_addr_reduction},"
            "dh-cert-file=vm_godh.b64,session-file=vm_session.b64",
            "-machine",
            "confidential-guest-support=sev0",
            "-qmp",
            f"tcp:localhost:{qmp_port},server=on,wait=off",
            "--no-reboot",  # Rebooting from inside the VM shuts down the machine
            "-S",
        ],
        cwd=working_dir,
    )

    vm.ssh_port = ssh_port
    vm.qmp_port = qmp_port
    vm.pid = p.pid
    vm.state = VmState.STARTED
