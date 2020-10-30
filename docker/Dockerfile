FROM ubuntu:20.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        language-pack-ja-base \
        language-pack-ja \
        build-essential \
        pkg-config \
        less \
        nano \
        git \
        wget \
        curl \
        python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir -U poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -
ENV PATH /$HOME/.poetry/bin:$PATH
RUN echo 'alias popy="poetry run python"' >> $HOME/.bashrc

# japanese
RUN update-locale LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja
ENV LANG ja_JP.UTF-8
ENV LC_ALL ja_JP.UTF-8
ENV LC_CTYPE ja_JP.UTF-8
