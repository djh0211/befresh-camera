FROM debian:bullseye

RUN apt update && apt install -y --no-install-recommends gnupg

RUN echo "deb http://archive.raspberrypi.org/debian/ bullseye main" > /etc/apt/sources.list.d/raspi.list \
  && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 82B129927FA3303E

RUN apt update && apt -y upgrade

RUN apt-get update

RUN apt update && apt install -y --no-install-recommends \
         python3-pip \
         python3-picamera2 \
     && apt-get clean \
     && apt-get autoremove \
     && rm -rf /var/cache/apt/archives/* \
     && rm -rf /var/lib/apt/lists/*
     
RUN apt-get install -y python3-pip python3-dev portaudio19-dev libasound2-dev python3-venv gcc-aarch64-linux-gnu 

RUN python3 -m venv --system-site-packages befresh-env

RUN source ./befresh-env/bin/activate

pip install -r requirements.txt



# ------------------------------------------------------------------------------------------------
# Build and run application
# ------------------------------------------------------------------------------------------------
# Set the working directory
WORKDIR /app

# Copy the Python files
COPY ./ /app/
