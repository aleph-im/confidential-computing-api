import subprocess
from pathlib import Path
from typing import List, Optional


class SevClient:
    def __init__(self, sev_dir: Path):
        self.sev_dir = sev_dir
        self.certificates_dir = sev_dir / "platform"
        self.certificates_archive = self.certificates_dir / "certs_export.zip"

        self.certificates_dir.mkdir(exist_ok=True, parents=True)

    def run_sev(self, options: List[str], output_dir: Optional[Path] = None):
        ofolder = output_dir if output_dir else self.sev_dir

        result = subprocess.run(
            ["sevtool", "--ofolder", ofolder, *options], capture_output=True
        )
        result.check_returncode()

        return result.stdout

    def export_certificates(self):
        self.run_sev(options=["--export_cert_chain"], output_dir=self.certificates_dir)
