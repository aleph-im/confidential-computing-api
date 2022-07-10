# OVMF build

The files in this directory aim to build a version of OVMF able to store SEV secrets
in a physical memory region that will then be accessible by Grub. The final OVMF image
will also include Grub in order to measure OVMF+Grub before loading secrets inside
the VM.

This process relies on the patch sets produced by James Bottomley:
https://listman.redhat.com/archives/edk2-devel-archive/2020-November/msg01247.html

As this requires a patched version of Grub, we build both tools inside a Docker image.
