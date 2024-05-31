# OVMF build

The files in this directory aim to build a version of OVMF able to store SEV secrets
in a physical memory region that will then be accessible by Grub. The final OVMF image
will also include Grub in order to measure OVMF+Grub before loading secrets inside
the VM.

This process relies on the patch sets produced by James Bottomley:
https://listman.redhat.com/archives/edk2-devel-archive/2020-November/msg01247.html

## Build instructions

As this requires a patched version of Grub, we build both tools inside a Docker image.

Step:
1. Outside of docker, download patched dep by running: `bash download_dependencies.sh`
2. Launch docker container : `sudo docker run -it -v .:/opt ubuntu 22:04`
3. Inside the docker, build the patched grub and OVMF with: `cd /opt; bash build_ovmf.sh`
4. The OVMF.fd file will be in `downloads/edk2/Build/AmdSev/RELEASE_GCC5/FV/OVMF.fd`