#! /bin/bash

set -eo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOWNLOAD_DIR="${SCRIPT_DIR}/downloads"
PATCH_DIR="${SCRIPT_DIR}/patches"

GRUB_GIT_REPOSITORY="https://git.savannah.gnu.org/git/grub.git"
GRUB_COMMIT="cf3a3acff057f61e6562fe07f7370a01bc634240"
GRUB_DIR="${DOWNLOAD_DIR}/grub"

EDK2_GIT_REPOSITORY="https://github.com/tianocore/edk2.git"
EDK2_COMMIT="edk2-stable202205"
EDK2_DIR="${DOWNLOAD_DIR}/edk2"

# Download Grub
git clone ${GRUB_GIT_REPOSITORY} "${GRUB_DIR}"

# Apply patches
GRUB_PATCH_DIR="${PATCH_DIR}/grub"
pushd "${GRUB_DIR}" > /dev/null
git checkout "${GRUB_COMMIT}"
git am "${GRUB_PATCH_DIR}"/*.eml "${GRUB_PATCH_DIR}/0001-Add-linuxefi-module.patch" "${GRUB_PATCH_DIR}/0002-Use-Debian-version-of-linuxefi-patches.patch"
popd > /dev/null

# Download EDK2 (=OVMF)
git clone --recurse-submodules "${EDK2_GIT_REPOSITORY}" "${EDK2_DIR}"

# Apply patches to EDK2
EDK2_PATCH_DIR="${PATCH_DIR}/edk2"
pushd "${EDK2_DIR}" > /dev/null
git checkout "${EDK2_COMMIT}"
git submodule update
git am --ignore-space-change --ignore-whitespace "${EDK2_PATCH_DIR}/0001-Fix-invokation-of-cryptomount-s-for-AMD-SEV.patch"
popd > /dev/null
