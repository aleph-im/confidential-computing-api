FROM ubuntu:22.04

ARG GRUB_PACKAGE
ARG EDK2_PACKAGE

# Install dependencies
RUN apt-get update && apt-get install -y build-essential uuid-dev iasl git nasm python-is-python3
RUN nasm --version

COPY downloads/ /opt/
COPY patches/grub-sev.patch .

WORKDIR /opt/${GRUB_PACKAGE}
