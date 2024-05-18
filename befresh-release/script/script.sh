#!/bin/sh

# sudo apt update && sudo apt install -y --no-install-recommends gnupg

# sudo apt update && sudo apt -y upgrade

# sudo apt-get update

# sudo apt install -y --no-install-recommends python3-pip

# sudo apt-get install -y python3-pip python3-dev portaudio19-dev libasound2-dev python3-venv gcc-aarch64-linux-gnu 

sleep 30

pip install -r /home/pi/dev/befresh-release/src/requirements.txt

python3 /home/pi/dev/befresh-release/src/wakeword.py &

python3 /home/pi/dev/befresh-release/src/main.py &


