#! /bin/bash
# Installs a version of Qemu compatible with confidential computing.

set -eo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

QEMU_VERSION="7.0.0"
QEMU_PACKAGE="qemu-${QEMU_VERSION}"
QEMU_TARBALL="${QEMU_PACKAGE}.tar.xz"

DOWNLOAD_DIR="${SCRIPT_DIR}/downloads"
QEMU_DOWNLOAD_DIR="${DOWNLOAD_DIR}/${QEMU_PACKAGE}"

mkdir -p "${DOWNLOAD_DIR}"

# Install dependencies
sudo apt-get update && \
  sudo apt-get install -y \
    build-essential zlib1g-dev pkg-config libglib2.0-dev binutils-dev libboost-all-dev autoconf libtool \
    libssl-dev libpixman-1-dev libpython3-dev python3-pip python-capstone virtualenv ninja-build

wget -O "${DOWNLOAD_DIR}/${QEMU_TARBALL}" "https://download.qemu.org/qemu-7.0.0.tar.xz"
tar -xvJf "${DOWNLOAD_DIR}/${QEMU_TARBALL}" --directory "${DOWNLOAD_DIR}"

pushd "${QEMU_DOWNLOAD_DIR}" >/dev/null
./configure
make
sudo make install
popd > /dev/null
