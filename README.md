# AutomatedAnnotations
Create annotations automatically from videos and save them in YOLO object detection format

# Description

**This python script works only when:**

**1. There is only one class**

**2. There is only one object of the class in the video**

The output format of annotations is in YOLO object detection Format

```
class_id center_x center_y width height
```

Each bounding box is represented in the above format. All coordinates are in normalized representation (divided by width and height of the image)

Each image contains each bounding box in the above format in a new line


The project is created using the correlation tracker of [dlib](http://dlib.net/)


I used opencv to both interact with and display the bounding boxes of the object in the video

# Requirements

1. opencv
2. dlib

# Usage

## Usage Video

The demo video used contains an Elephant walking around.

The original video can be found at https://www.videezy.com/abstract/41648-elephant-walking-in-cage-at-zoo-4k

![demo gif](elephant_annotation_demo.gif)

## Command Prompt Commands

```
python3 automated_annotation.py -i input_video.mp4 -s annotations_newer -n 10 -o 5
```
The arguments are:

-i -> input video name

-s -> the annotations folder where two folders called images/ and annotations/ are created to store the annotations

-n -> every n-th frame of the video is saved in the annotations folder

-o -> the starting of the sequence number so that mixing the datasets become easier

## Steps:

1. The first frame is paused, simply click on the image displayed in the window titled "Automated Labelling", click and drag on the object to annotate.

2. Now click on the key 'p' on keyboard, the tracked object is displayed in green rectangle

3. When the tracking becomes inaccurate, click on the key 'p' on the keyboard again

4. Draw the updated bounding box

5. Press the key 'p' on keyboard to continue tracking

# Next Steps

1. Enable multiple objects tracking feature

2. Enable usage of multiple classes

