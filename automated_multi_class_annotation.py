import cv2
import dlib
import argparse
import os
import sys
import numpy as np
from dialogue_box import *

# command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input_video", help="The relative path of the video", required=True)
parser.add_argument("-s", "--save_path", help="The path to save the images and annotations", required=True)
parser.add_argument("-n", "--save_every", type=int, default=10,
                    help="Only every n-th frame is saved as an annotation", required=False)
parser.add_argument("-o", "--start_number", type=int, default=0,
                    help="Starting number of the annotations naming sequence", required=False)
parser.add_argument("-c", "--classes", required=True, default="object", help="the class names separataed by ','")
parser.add_argument("-w", "--width", type=int, required=False, default=800, help="the width of the window")
parser.add_argument("--small_object", type=float, default=0.1,
                    help="threshold for small object, the lower the value, the smaller the object")
parser.add_argument("--frame_delay", type=int, default=1,
                    help="delay between two consecutive frames in ms")
args = parser.parse_args()

print("Note: Please try to set the number of object trackers as per your system configuration")

# initialize some global variables
frame = None
dragging = False
temp_start_point = []
tracking = False
window_name = "Automated Labelling"

# current rectangles
all_bounding_boxes = {}
all_current_position = {}
# create a dictionary to store the dlib trackers with keys as class names and a list that containes dlib tracker objects
idx_trackers = {}

# save colors as a dictionary to use later in algorithms
color = {"track": (0, 255, 0),
         "text": (0, 0, 0),
         "line": (150, 255, 180)}

# parse and save the command line arguments
save_counter = args.start_number
save_every = args.save_every
input_vid = args.input_video
save_path = args.save_path
opencv_window_width = args.width
small_thresh = args.small_object
time_delay = args.frame_delay

# create the number of classes from command line arguments
classes = args.classes.split(',')
classes = [w.strip() for w in classes]
set_classes(classes)
# check that at least one class is present
if len(classes) == 0:
    raise AssertionError("The classes should not be empty!")

# check if the path already exists
if os.path.exists(save_path):
    raise AssertionError("The save path already exists please enter a new path")
    # print("okay fix this in prod")
else:
    # make sure the path does not include a / at the end
    if save_path.endswith("/"):
        save_path = save_path[:-1]
    # create the required directories
    os.mkdir(save_path)
    os.mkdir(os.path.join(save_path, "images"))
    os.mkdir(os.path.join(save_path, "annotations"))

# this is used to save the yolo format class id
class_idx = {k: i for i, k in enumerate(classes)}

# save the classes in classes.txt
with open(save_path + "/annotations/classes.txt", 'w') as f:
    f.write("\n".join(classes))


# this is used to prevent single click being detected as an object
def area_of(points, shape):
    global small_thresh
    h, w, _ = shape
    x1, y1, x2, y2 = points
    return (y2 - y1) * (x2 - x1) > (w * h) * small_thresh / 100


# the call back function of cv2 window
def draw_annotation(event, x, y, flags, params):
    global dragging, temp_start_point, frame, tracking, save_counter, classes
    # this temporary frame is used for drawing rectangles so that the main frame is not effected
    temp_frame = frame.copy()
    # draw all the bounding boxes and corresponding class labels
    for key, val in all_bounding_boxes.items():
        for v in val:
            x1, y1, x2, y2 = v
            temp_box = temp_frame[y1:y2, x1:x2]
            # print(temp_frame[y1:y2, x1:x2][:, :, 0].shape)
            cv2.rectangle(temp_frame, (x1, y1), (x2, y2), (0, 255, 0))
            cv2.putText(temp_frame, key, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color["text"], thickness=2)
            if x1 < x < x2 and y1 < y < y2:
                temp_frame[y1:y2, x1:x2, 0] = np.array([[190] * temp_box.shape[1]] * temp_box.shape[0])
    if not tracking:
        h, w, _ = temp_frame.shape
        cv2.line(temp_frame, (x, 0), (x, h), color["line"])
        cv2.line(temp_frame, (0, y), (w, y), color["line"])
    cv2.imshow(window_name, temp_frame)
    # if a rectangle is double clicked, the bounding box is deleted
    if event == cv2.EVENT_RBUTTONDBLCLK:
        delete_this = {}
        # iterate over bounding boxes to identify the box selected
        for key, val in all_bounding_boxes.items():
            for i, v in enumerate(val):
                x1, y1, x2, y2 = v
                # check click condition
                if x1 < x < x2 and y1 < y < y2:
                    if key not in delete_this:
                        delete_this[key] = []
                    delete_this[key].append(i)
                    break
        # delete from dictionary separately as dictionary cannot be altered during a loop
        for key, val in delete_this.items():
            for i in val:
                del all_bounding_boxes[key][i]
    # the dragging feature is enabled and the top xy coords of the image are added to a local variable
    if event == cv2.EVENT_LBUTTONDOWN:
        print("recog lbutton down")
        dragging = True
        temp_start_point = [x, y]
    # check if drawing the bounding box is done
    elif event == cv2.EVENT_LBUTTONUP:
        # disable drawing
        dragging = False
        # store the points in a variable
        points = [temp_start_point[0], temp_start_point[1], x, y]
        # check if the small object thresh condition is satisfied
        if not area_of(points, temp_frame.shape):
            pass
        else:
            temp_start_point = []
            # enable tracking
            # tracking = True
            # get class from a dialog box dropdown
            cls = select_class_name(classes)
            # append bounding box to all bounding boxes
            if cls not in all_bounding_boxes:
                all_bounding_boxes[cls] = []
            all_bounding_boxes[cls].append(points)
    else:
        # here we continuously update the frame with the bounding box
        if dragging:
            if len(temp_start_point) > 0:
                cv2.rectangle(temp_frame, tuple(temp_start_point), (x, y), (255, 0, 0))
            cv2.imshow(window_name, temp_frame)


# the main function
def main():
    # create a window which will display the UI
    cv2.namedWindow(window_name)
    # add the callback function
    cv2.setMouseCallback(window_name, draw_annotation)
    # define the global variables
    global frame, tracking, idx_trackers, save_counter, input_vid, save_every, save_path, opencv_window_width, time_delay
    # initialize video capture
    cap = cv2.VideoCapture(input_vid)
    print(input_vid)
    # read the first frame
    ret, frame = cap.read()
    H, W, _ = frame.shape
    # define resize ratio so that the width is frame_width
    resize_ratio = opencv_window_width / W
    timer = 0
    paused = True
    # start the main loop
    while ret:
        current_points = []
        # resize the frame so that the width = frame_width px
        frame = cv2.resize(frame, None, fx=resize_ratio, fy=resize_ratio)
        h, w, _ = frame.shape
        # this is used for drawing the rectangle so the original frame is not effected
        temp_frame = frame.copy()
        assigned = False
        # update object positions with tracking
        if not paused and tracking:
            # track the object initialized in the call back function
            tracker_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # iterate over the trackers to get the updated positions
            for key, dlib_trackers in idx_trackers.items():
                for ind, dlib_tracker in enumerate(dlib_trackers):
                    dlib_tracker.update(tracker_rgb)
                    # get the position of the tracking object in the updated frame
                    pos = dlib_tracker.get_position()
                    x1 = int(pos.left())
                    y1 = int(pos.top())
                    x2 = int(pos.right())
                    y2 = int(pos.bottom())
                    # update all bounding box positions which are used in call back function
                    all_bounding_boxes[key][ind] = [x1, y1, x2, y2]
                    # draw the bounding box on the frame
                    cv2.rectangle(temp_frame, (x1, y1), (x2, y2), color["track"])
                    # draw the class name
                    cv2.putText(temp_frame, key, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                color["text"], thickness=2)
                    assigned = True
                    # add the annotations and class name to current_points list
                    current_points.append([x1, y1, x2, y2, key])
        # update the frame with the new tracked object frame
        cv2.imshow(window_name, temp_frame)
        key_press = cv2.waitKey(timer) & 0xFF
        if key_press == ord('q'):
            break
        # pause the next frame or play from the next frame
        elif key_press == ord('p'):
            if not paused:
                timer = 0
                paused = True
                print("paused at: ", save_counter)
                cv2.imshow(window_name, frame)
                assigned = False
                tracking = False
            else:
                timer = time_delay
                paused = False
                tracking = True
                # delete all trackers and will be reinitialized with object positions
                delete_trackers = [w for w in idx_trackers.keys()]
                for tracker in delete_trackers:
                    del idx_trackers[tracker]
                tracker_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # initialize trackers for all bounding boxes
                for key, val in all_bounding_boxes.items():
                    idx_trackers[key] = []
                    for x1, y1, x2, y2 in val:
                        rect = dlib.rectangle(x1, y1, x2, y2)
                        idx_trackers[key].append(dlib.correlation_tracker())
                        idx_trackers[key][-1].start_track(tracker_rgb, rect)
        # check if it is not paused and it the object is being tracked
        if not paused and tracking:
            # check if the object is in fact tracked
            if assigned:
                # check if the counter satisfies the skip condition
                if save_counter % save_every == 0:
                    if len(current_points) > 0:
                        lines = []
                        cv2.imwrite(save_path + "/images/" + str(save_counter) + ".jpg", frame)
                        # iterate over the frames to save the annotations in txt files
                        for x1, y1, x2, y2, cls in current_points:
                            aw = x2 - x1
                            ah = y2 - y1
                            cx = (x1 + x2) / 2
                            cy = (y1 + y2) / 2
                            ax = cx / w
                            ay = cy / h
                            aw /= w
                            ah /= h
                            lines.append(str(class_idx[cls]) + " %0.6f %0.6f %0.6f %0.6f" % (ax, ay, aw, ah))
                        with open(save_path + "/annotations/" + str(save_counter) + ".txt", 'w') as f:
                            f.write("\n".join(lines))
                # increment the save counter
                save_counter += 1
        # read the next frame
        ret, frame = cap.read()


if __name__ == "__main__":
    main()
