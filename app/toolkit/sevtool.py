import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class SevPlatformStatus:
    api_major: int
    api_minor: int
    platform_state: int
    owner: int
    config: int
    build: int
    guest_count: int

    @classmethod
    def from_dict(cls, raw_values: Dict[str, str]):
        return cls(
            api_major=int(raw_values["api_major"]),
            api_minor=int(raw_values["api_minor"]),
            platform_state=int(raw_values["platform_state"]),
            owner=int(raw_values["owner"]),
            config=int(raw_values["config"]),
            build=int(raw_values["build"]),
            guest_count=int(raw_values["guest_count"]),
        )


def get_command_status_code(result: subprocess.CompletedProcess) -> int:
    # sevtool does not return error codes, we must parse them from stdout
    command_result_str = result.stdout.split("\n")[-2]
    if command_result_str == "Command Successful":
        return 0

    error_code = command_result_str.split(": ")[1]
    return int(error_code, 16)


def check_command_result(result: subprocess.CompletedProcess):
    # If sevtool does not understand the command-line arguments, it will write
    # the error to stderr
    if result.stderr:
        raise ValueError(f"Invalid sevtool command: {result.stderr}")

    status_code = get_command_status_code(result)
    if status_code != 0:
        raise ValueError(f"sevtool command failed: {result.stdout}")


class SevClient:
    def __init__(self, sev_dir: Path):
        self.sev_dir = sev_dir
        self.certificates_dir = sev_dir / "platform"
        self.certificates_archive = self.certificates_dir / "certs_export.cer"

        self.certificates_dir.mkdir(exist_ok=True, parents=True)

    def sevtool_cmd(
        self, *args, output_dir: Optional[Path] = None
    ) -> subprocess.CompletedProcess:
        ofolder = output_dir if output_dir else self.sev_dir

        result = subprocess.run(
            ["sevctl", *args],
            capture_output=False,
            text=True,
        )

        #check_command_result(result)
        return result

    def get_platform_status(self) -> SevPlatformStatus:
        result = self.sevtool_cmd("--platform_status")

        sev_platform_status = {}
        for line in result.stdout.splitlines():
            if ":" not in line:
                break

            key, value = line.split(":")
            sev_platform_status[key] = value.strip()

        return SevPlatformStatus.from_dict(sev_platform_status)

    def export_certificates(self):
        _ = self.sevtool_cmd("export", "--full", self.certificates_archive)
