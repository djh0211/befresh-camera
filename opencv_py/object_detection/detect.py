"""Main script to run the object detection routine."""

import argparse

import sys

import time



import cv2

from tflite_support.task import core

from tflite_support.task import processor

from tflite_support.task import vision

import utils

import numpy as np



from picamera2 import Picamera2, Preview

from libcamera import controls





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



    # Variables to calculate FPS

    counter, fps = 0, 0

    start_time = time.time()



    # Start the camera

    picam2 = Picamera2()

    picam2.start_preview(Preview.QTGL)

    preview_config = picam2.create_preview_configuration(buffer_count=3)

    capture_config = picam2.create_still_configuration(buffer_count=3)

    

    picam2.configure(preview_config)

    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})



    picam2.start()



    # Visualization parameters

    row_size = 20  # pixels

    left_margin = 24  # pixels

    text_color = (0, 0, 255)  # red

    font_size = 1

    font_thickness = 1

    fps_avg_frame_count = 10



    # Initialize the object detection model

    base_options = core.BaseOptions(

        file_name=model, use_coral=enable_edgetpu, num_threads=num_threads)

    detection_options = processor.DetectionOptions(

        max_results=3, score_threshold=0.3)

    options = vision.ObjectDetectorOptions(

        base_options=base_options, detection_options=detection_options)

    detector = vision.ObjectDetector.create_from_options(options)



    # Start capturing video input from the camera

    while True:

        image = picam2.capture_array()

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)



        counter += 1



        # Convert the image from BGR to RGB as required by the TFLite model.

        # rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)



        # Create a TensorImage object from the RGB image.

        input_tensor = vision.TensorImage.create_from_array(image)



        # Run object detection estimation using the model.

        detection_result = detector.detect(input_tensor)



        # Draw keypoints and edges on input image

        image = utils.visualize(image, detection_result)



        # Calculate the FPS

        if counter % fps_avg_frame_count == 0:

            end_time = time.time()

            fps = fps_avg_frame_count / (end_time - start_time)

            start_time = time.time()



        # Show the FPS

        fps_text = 'FPS = {:.1f}'.format(fps)

        text_location = (left_margin, row_size)

        cv2.putText(image, fps_text, text_location, cv2.FONT_HERSHEY_PLAIN,

                    font_size, text_color, font_thickness)

        if (len(detection_result.detections)>0):

            i=0

            for detection in detection_result.detections:

                bounding_box = detection.bounding_box

                start_x = bounding_box.origin_x

                dx = bounding_box.width

                start_y = bounding_box.origin_y

                dy = bounding_box.height

                cv2.imwrite(f"./crop{i}.jpg", image[start_y:start_y+dy, start_x:start_x+dx])

            break





        # Stop the program if the ESC key is pressed.

        # if cv2.waitKey(1) == 27:

        #     break

        # cv2.imshow('object_detector', image)

        # print(fps)



    cv2.destroyAllWindows()



def main():

    parser = argparse.ArgumentParser(

        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(

        '--model',

        help='Path of the object detection model.',

        required=False,

        default='efficientdet_lite0.tflite')

    parser.add_argument(

        '--cameraId', help='Id of camera.', required=False, type=int, default=0)

    parser.add_argument(

        '--frameWidth',

        help='Width of frame to capture from camera.',

        required=False,

        type=int,

        default=640)

    parser.add_argument(

        '--frameHeight',

        help='Height of frame to capture from camera.',

        required=False,

        type=int,

        default=480)

    parser.add_argument(

        '--numThreads',

        help='Number of CPU threads to run the model.',

        required=False,

        type=int,

        default=4)

    parser.add_argument(

        '--enableEdgeTPU',

        help='Whether to run the model on EdgeTPU.',

        action='store_true',

        required=False,

        default=False)

    args = parser.parse_args()



    run(args.model, int(args.cameraId), args.frameWidth, args.frameHeight,

        int(args.numThreads), bool(args.enableEdgeTPU))





if __name__ == '__main__':

    main()

