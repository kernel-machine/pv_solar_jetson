FROM ubuntu:noble

RUN apt update && apt install -y --no-install-recommends \
  sudo \
  ca-certificates \
  findutils \
  gnupg \
  dirmngr \
  inetutils-ping \
  netbase \
  curl \
  udev \
  kmod \
  nano

# Prevent apt-get prompting for input
ENV DEBIAN_FRONTEND noninteractive

RUN echo "deb https://repo.download.nvidia.com/jetson/common r36.4 main" >  /etc/apt/sources.list.d/nvidia.list \
       && echo "deb https://repo.download.nvidia.com/jetson/t234 r36.4 main" >>  /etc/apt/sources.list.d/nvidia.list \
       && apt-key adv --fetch-key http://repo.download.nvidia.com/jetson/jetson-ota-public.asc \
       && mkdir -p /opt/nvidia/l4t-packages/ && touch /opt/nvidia/l4t-packages/.nv-l4t-disable-boot-fw-update-in-preinstall

RUN \
    apt update && apt-get install -y wget tar lbzip2 binutils xz-utils zstd qemu-user-static cpio git && \
    cd /tmp/ && wget https://developer.nvidia.com/downloads/embedded/l4t/r36_release_v4.3/release/Jetson_Linux_r36.4.3_aarch64.tbz2 && \
    tar xf Jetson_Linux_r36.4.3_aarch64.tbz2 && \
    cd Linux_for_Tegra && \
    mkdir -p /tmp/Linux_for_Tegra/rootfs/boot/ && \
    mkdir -p /tmp/Linux_for_Tegra/rootfs/usr/bin && \
    mkdir -p /tmp/Linux_for_Tegra/rootfs/etc && touch /tmp/Linux_for_Tegra/rootfs/etc/resolv.conf && \
    sed -i 's/config.tbz2\"/config.tbz2\" --exclude=etc\/hosts --exclude=etc\/hostname/g' apply_binaries.sh && \
    sed -i 's/CheckPackage qemu-user-static/#CheckPackage qemu-user-static/g' tools/l4t_update_initrd.sh && \
    sed -i 's/trap CleanupVirEnv/#trap CleanupVirEnv/g' tools/l4t_update_initrd.sh&& \
    sed -i 's|cp /usr/bin/qemu-aarch64-static|#cp /usr/bin/qemu-aarch64-static|g' tools/l4t_update_initrd.sh && \
    sed -i 's|^UpdateInitrd|#UpdateInitrd|g' tools/l4t_update_initrd.sh && \
    sed -i 's|^UpdateBackToBaseInitrd|#UpdateBackToBaseInitrd|g' tools/l4t_update_initrd.sh && \
    sed -i 's|cp /etc/resolv.conf|#cp /etc/resolv.conf|g' tools/l4t_update_initrd.sh && \
    sed -i 's|mv "${LDK_ROOTFS_DIR}/etc/resolv.conf"|cp "${LDK_ROOTFS_DIR}/etc/resolv.conf"|g' tools/l4t_update_initrd.sh && \
    sed -i 's|	PrepareVirEnv|#PrepareVirEnv|g' tools/l4t_update_initrd.sh && \
    sed -i 's/install --owner=root --group=root \"${QEMU_BIN}\" \"${L4T_ROOTFS_DIR}\/usr\/bin\/\"/#install --owner=root --group=root \"${QEMU_BIN}\" \"${L4T_ROOTFS_DIR}\/usr\/bin\/\"/g' nv_tegra/nv-apply-debs.sh && \
    sed -i 's/chroot . \//  /g' nv_tegra/nv-apply-debs.sh && \
    cd /tmp/Linux_for_Tegra/ && ./apply_binaries.sh -r / --target-overlay && cd .. && \
    rm -rf Linux_for_Tegra && \
    echo "/usr/lib/aarch64-linux-gnu/tegra" > /etc/ld.so.conf.d/nvidia-tegra.conf && ldconfig

RUN apt update && apt install -y python3 python3-venv python3-pip nvtop wget

ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/tegra
COPY setup/postscript.sh /tmp/postscript.sh
RUN chmod +x /tmp/postscript.sh
RUN /tmp/postscript.sh

RUN curl -fsSL https://code-server.dev/install.sh | sh

EXPOSE 8000

ARG USER_UID=1001
ARG USER_GID=1001
ARG USER_NAME=alcor

RUN groupadd --gid $USER_GID $USER_NAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USER_NAME -s /bin/bash \
    && apt-get update && apt-get install -y --no-install-recommends \
        bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY src /home/alcor/app
RUN chown -R $USER_NAME:$USER_NAME /home/alcor/app
USER ${USER_NAME}
WORKDIR /home/alcor/app

CMD ["code-server","--bind-addr","0.0.0.0:8000"]