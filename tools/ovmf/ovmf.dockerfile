FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y build-essential uuid-dev iasl git nasm python-is-python3
RUN nasm --version

WORKDIR /opt/
COPY patches /opt/
COPY download_dependencies.sh/ /opt/
#COPY build_ovmf.sh/ /opt/

RUN bash ./download_dependencies.sh
