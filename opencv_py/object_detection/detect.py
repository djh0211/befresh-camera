# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Main script to run the object detection routine."""
import argparse
import sys
import time

import cv2
from object_detector import ObjectDetector
from object_detector import ObjectDetectorOptions
import utils

from picamera2 import Picamera2, Preview, MappedArray
from libcamera import controls

normalSize = (640, 480)
lowresSize = (320, 240)

def run(model: str, camera_id: int, width: int, height: int, num_threads: int,
        enable_edgetpu: bool) -> None:
    """Continuously run inference on images acquired from the camera.

    Args:
        model: Name of the TFLite object detection model.
        camera_id: The camera id to be passed to OpenCV.
        width: The width of the frame captured from the camera.
        height: The height of the frame captured from the camera.
        num_threads: The number of CPU threads to run the model.
        enable_edgetpu: True/False whether the model is a EdgeTPU model.
    """

    # Start the camera
    picam2 = Picamera2()
    picam2.start_preview(Preview.QTGL)
    preview_config = picam2.create_preview_configuration(buffer_count=3,
                                                         main={"size": normalSize},
                                                         lores={"size": lowresSize, "format": "YUV420"})
    capture_config = picam2.create_still_configuration(buffer_count=3)
    
    picam2.configure(preview_config)
    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

    stride = picam2.stream_configuration("lores")["stride"]


    # picam2.post_callback = DrawRectangles

    picam2.start()

    # Start capturing video input from the camera
    # while True:
    buffer = picam2.capture_buffer("lores")
    grey = buffer[:stride*lowresSize[1]].reshape((lowresSize[1], stride))
    cv2.imgread



def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--model',
        help='Path of the object detection model.',
        required=False,
        default='efficientdet_lite0.tflite')
    #   parser.add_argument(
    #       '--cameraId', help='Id of camera.', required=False, type=int, default=0)
    #   parser.add_argument(
    #       '--frameWidth',
    #       help='Width of frame to capture from camera.',
    #       required=False,
    #       type=int,
    #       default=640)
    #   parser.add_argument(
    #       '--frameHeight',
    #       help='Height of frame to capture from camera.',
    #       required=False,
    #       type=int,
    #       default=480)
    parser.add_argument(
        '--numThreads',
        help='Number of CPU threads to run the model.',
        required=False,
        type=int,
        default=4)
    #   parser.add_argument(
    #       '--enableEdgeTPU',
    #       help='Whether to run the model on EdgeTPU.',
    #       action='store_true',
    #       required=False,
    #       default=False)
    args = parser.parse_args()

    run(args.model, int(args.cameraId), args.frameWidth, args.frameHeight,
        int(args.numThreads), bool(args.enableEdgeTPU))


if __name__ == '__main__':
    main()