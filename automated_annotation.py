import cv2
import dlib
import argparse
import os

# command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input_video", help="The relative path of the video", required=True)
parser.add_argument("-s", "--save_path", help="The path to save the images and annotations", required=True)
parser.add_argument("-n", "--save_every", type=int, default=1,
                    help="Only every n-th frame is saved as an annotation", required=False)
parser.add_argument("-o", "--start_number", type=int, default=0,
                    help="Starting number of the annotations naming sequence", required=False)
args = parser.parse_args()

# store command line arguments to global variables
frame = None
dragging = False
temp_start_point = []
tracking = False

# initialize the dlib tracker as a global variable
dlib_tracker = dlib.correlation_tracker()

# parse and save the command line arguments
save_counter = args.start_number
save_every = args.save_every
input_vid = args.input_video
save_path = args.save_path

# check if the path already exists
if os.path.exists(save_path):
    raise AssertionError("The save path already exists please enter a new path")

# make sure the path does not include a / at the end
if save_path.endswith("/"):
    save_path = save_path[:-1]

# create the required directories
os.mkdir(save_path)
os.mkdir(os.path.join(save_path, "images"))
os.mkdir(os.path.join(save_path, "annotations"))


# the call back function of cv2 window
def draw_annotation(event, x, y, flags, params):
    global dragging, temp_start_point, frame, tracking, dlib_tracker, save_counter
    # this temporary frame is used for drawing rectangles so that the main frame is not effected
    temp_frame = frame.copy()
    # the dragging feature is enabled and the top xy coords of the image are added to a local variables
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
        # make temp_start_point list empty
        temp_start_point = []
        # enable tracking
        tracking = True
        # dlib requires the image format in rgb so cvt the BGR frame to RGB
        tracker_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # define an rectangle in the format x_left, y_top, x_right, y_bottom
        rect = dlib.rectangle(*points)
        # initialize the tracker to start tracking
        dlib_tracker.start_track(tracker_rgb, rect)
        # check if it is the n-th frame defined by user
        if save_counter % save_every == 0:
            # save the image to the save path
            cv2.imwrite(save_path + "/images/" + str(save_counter) + ".jpg", frame)
            # the yolo format requires the annotations in Class_id, Center-X, center-Y, Width, Height format in the ratios of W and H
            h, w, _ = frame.shape
            with open(save_path + "/annotations/" + str(save_counter) + ".txt", 'w') as f:
                x1, y1, x2, y2 = points
                aw = x2 - x1
                ah = y2 - y1
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                ax = cx / w
                ay = cy / h
                aw /= w
                ah /= h
                f.write("0 " + " %0.6f %0.6f %0.6f %0.6f" % (ax, ay, aw, ah))
        # increment counter by one
        save_counter += 1
    else:
        # here we continuously update the frame with the bounding box
        if dragging:
            if len(temp_start_point) > 0:
                cv2.rectangle(temp_frame, tuple(temp_start_point), (x, y), (255, 0, 0))
                cv2.imshow("Automated Labelling", temp_frame)


# the main function
def main():
    # create a window which will display the UI
    cv2.namedWindow("Automated Labelling")
    # add the callback function
    cv2.setMouseCallback("Automated Labelling", draw_annotation)
    # define the global variables
    global frame, tracking, dlib_tracker, save_counter, input_vid, save_every, save_path
    # initialize video capture
    cap = cv2.VideoCapture(input_vid)
    # read the first frame
    ret, frame = cap.read()
    # resize ratio is used so that the frame doesn't get too big
    resize_ratio = 1.0
    H, W, _ = frame.shape
    if W > 1000:
        # define resize ratio so that the width is frame_width
        resize_ratio = 600 / W
    timer = 0
    paused = True
    # start the main loop
    while ret:
        # resize the frame so that the width = frame_width px
        frame = cv2.resize(frame, None, fx=resize_ratio, fy=resize_ratio)
        h, w, _ = frame.shape
        # this is used for drawing the rectangle so the original frame is not effected
        temp_frame = frame.copy()
        assigned = False
        # we have an option to pause the stream to redefine the annotation
        if not paused and tracking:
            # track the object initialized in the call back function
            tracker_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # update the frame in dlib tracker
            dlib_tracker.update(tracker_rgb)
            # get the position of the tracking object in the updated frame
            pos = dlib_tracker.get_position()
            x1 = int(pos.left())
            y1 = int(pos.top())
            x2 = int(pos.right())
            y2 = int(pos.bottom())
            # draw the bounding box on the frame
            cv2.rectangle(temp_frame, (x1, y1), (x2, y2), (0, 255, 0))
            assigned = True
        # update the frame with the new tracked object frame
        cv2.imshow("Automated Labelling", temp_frame)
        key_press = cv2.waitKey(timer) & 0xFF
        if key_press == ord('q'):
            break
        # pause the next frame or play from the next frame
        elif key_press == ord('p'):
            if not paused:
                timer = 0
                paused = True
                print("paused at: ", save_counter)
                dlib_tracker = dlib.correlation_tracker()
                cv2.imshow("Automated Labelling", frame)
                assigned = False
            else:
                timer = 1
                paused = False
        # check if it is not paused and it the object is being tracked
        if not paused and tracking:
            # check if the object is in fact tracked
            if assigned:
                # check if the counter satisfies the skip condition
                if save_counter % save_every == 0:
                    cv2.imwrite(save_path + "/images/" + str(save_counter) + ".jpg", frame)
                    with open(save_path + "/annotations/" + str(save_counter) + ".txt", 'w') as f:
                        aw = x2 - x1
                        ah = y2 - y1
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        ax = cx / w
                        ay = cy / h
                        aw /= w
                        ah /= h
                        f.write("0 " + " %0.6f %0.6f %0.6f %0.6f" % (ax, ay, aw, ah))
                # increment the save counter
                save_counter += 1
        # read the next frame
        ret, frame = cap.read()


if __name__ == "__main__":
    main()
