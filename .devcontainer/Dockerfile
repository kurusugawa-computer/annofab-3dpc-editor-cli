FROM ubuntu:22.04

# Install prerequisites
RUN set -x \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        gnupg2 \
        software-properties-common \
        language-pack-ja \
        tzdata \
        curl \
        lsb-release \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

# Set locale & timezone
RUN update-locale LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja \
    && ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && echo "Asia/Tokyo" > /etc/timezone

ENV LANG=ja_JP.UTF-8
ENV LC_ALL=ja_JP.UTF-8
ENV LC_CTYPE=ja_JP.UTF-8

RUN set -x \
    && sed -i.bak -r 's!(deb|deb-src) \S+!\1 http://jp.archive.ubuntu.com/ubuntu/!' /etc/apt/sources.list

# Install Ubuntu packages
RUN set -x \
    # Python3.12をインストールするために、deadsnakes PPAを追加
    && add-apt-repository ppa:deadsnakes/ppa \
    # Install packages
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        # python
        python3.12-dev \
        # common tools
        bash-completion \
        build-essential \
        git \
        iputils-ping \
        jq \
        less \
        net-tools \
        openssh-client \
        sudo \
        tar \
        time \
        unzip \
        vim \
        wget \
        xz-utils \
        zip \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*


# Add user / Grant sudo privileges
RUN useradd -m -s /bin/bash -u 5000 -U vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/ALL

USER vscode

RUN set -x \
    && curl -LsSf https://astral.sh/uv/install.sh | sh 

