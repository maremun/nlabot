FROM base/archlinux:latest

COPY etc/ /etc/

ENV TZ=Europe/Moscow

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

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

COPY packages.txt .

RUN pip install -r packages.txt

COPY . .

RUN pip install -e .
