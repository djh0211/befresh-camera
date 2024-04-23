#!/usr/bin/python3

# Capture a full resolution image to memory rather than to a file.

import time

from picamera2 import Picamera2, Preview
from libcamera import controls
import numpy as np

picam2 = Picamera2()
picam2.start_preview(Preview.QTGL)
preview_config = picam2.create_preview_configuration(buffer_count=3)
capture_config = picam2.create_still_configuration(buffer_count=3)

picam2.configure(preview_config)
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
picam2.start()
time.sleep(2)

picam2.switch_mode(capture_config)
array = picam2.capture_array() 
np.save('./qr', array)
# image = picam2.switch_mode_and_capture_image(capture_config)
# image.show()


time.sleep(5)

picam2.close()