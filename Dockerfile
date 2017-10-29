FROM base/archlinux:latest

COPY etc/ /etc/

ENV LANG=ru_RU.UTF-8 LANGUAGE=en_US.UTF-8

RUN locale-gen && \
    source /etc/profile.d/locale.sh; /bin/true && \
    pacman -Sy && \
    pacman -S --noconfirm docker docker-compose python python-pip python-docker

RUN mkdir /nlabot

WORKDIR /nlabot

ENTRYPOINT ["nlabot"]

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN pip install -e .
