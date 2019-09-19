FROM debian:stable-slim
RUN mkdir -p /usr/share/man/man1/
RUN apt-get update && apt-get install -y \
    curl
    openjfx \
    default-jre \
    firefox-esr \
    python3-pip \
    git \
    vim \
    iproute2 \
    libasound2 \
    libdbus-glib-1-2 \
    libgtk-3-0 \
    libxrender1 \
    libx11-xcb-dev \
    libx11-xcb1 \
    libcanberra-gtk-module \
    --no-install-recommends

ENV HOME /home/user
RUN useradd --shell /bin/bash --create-home --home-dir $HOME user \
    && chown -R user:user $HOME
ENV PATH "$PATH:/apps"

WORKDIR $HOME
USER user
