import concurrent.futures
import glob
import multiprocessing
import os

import cv2
import numpy as np
import tqdm

multiprocessing.set_start_method("spawn", True)


class ImageProcessor:
    def __init__(
        self,
        labels_path,
        config_path,
        weights_path,
        useful_labels,
        image_folder,
        training_out,
        annotimage_out,
        yolo_version
    ):
        # Setup variables
        self.LABELS = open(labels_path).read().strip().split("\n")
        self.configpath = config_path
        self.weightspath = weights_path
        self.useful_labels = useful_labels
        self.imagefolder = image_folder
        self.training_out = training_out
        self.annotimage_out = annotimage_out
        self.conf_thresh = 0.2
        self.yolo_version = yolo_version

#         # Init
#         self.net = cv2.dnn.readNet(self.configpath, self.weightspath)

#         # Determine the output layer names
#         self.ln = self.net.getLayerNames()
#         self.ln = [self.ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

    def refined_box(self, left, top, width, height):
        right = left + width
        bottom = top + height

        original_vert_height = bottom - top
        top = int(top + original_vert_height * 0.15)
        bottom = int(bottom - original_vert_height * 0.05)

        margin = ((bottom - top) - (right - left)) // 2
        left = (
            left - margin
            if (bottom - top - right + left) % 2 == 0
            else left - margin - 1
        )

        right = right + margin

        return left, top, right, bottom

    def draw_box(self, frame, conf, label, left, top, right, bottom):
        # Draw a bounding box.
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        text = f"{label}: {conf:.1%} "

        # Display the label at the top of the bounding box
        label_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

        top = max(top, label_size[1])
        cv2.putText(
            frame,
            text,
            (left, top - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 255, 255),
            1,
        )

    def process_frame(self, file, conf_thresh, nms_thresh=0.2):
        im = cv2.imread(file)
        (H, W) = im.shape[:2]

        # Init
        if self.yolo_version == "3":
            net = cv2.dnn.readNetFromDarknet(self.configpath, self.weightspath)
        elif self.yolo_version == "4":
            net = cv2.dnn.readNet(self.configpath, self.weightspath)
            

        # Determine the output layer names
        ln = net.getLayerNames()
        ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        # Create the blob
        blob = cv2.dnn.blobFromImage(im, 1 / 255.0, (416, 416), swapRB=True, crop=False)
        net.setInput(blob)
        layerOutputs = net.forward(ln)

        # Translate the predictions
        boxes = []
        confidences = []
        classIDs = []

        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]

                if confidence > conf_thresh:
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    # update our list of bounding box coordinates, confidences, and class IDs
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    classIDs.append(classID)

        # apply non-maxima suppression to suppress weak, overlapping bounding boxes
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, conf_thresh, nms_thresh)

        final_boxes = []
        training_info = []

        if len(idxs):
            for i in idxs.flatten():
                # Limit to useful
                if self.LABELS[classIDs[i]] in self.useful_labels:
                    box = boxes[i]
                    left = box[0]
                    top = box[1]
                    width = box[2]
                    height = box[3]
                    final_boxes.append(box)

                    # Create the box
#                     left, top, right, bottom = self.refined_box(
#                         left, top, width, height
#                     )
                    right = left + width
                    bottom = top + height
                    self.draw_box(
                        im,
                        confidences[i],
                        self.LABELS[classIDs[i]],
                        left,
                        top,
                        right,
                        bottom,
                    )

                    # Get the training info
                    center_x = (left + (width / 2)) / W
                    center_y = (top + (height / 2)) / H
                    width_norm = width / W
                    height_norm = height / H
                    training_info.append(
                        [
                            self.useful_labels.index(self.LABELS[classIDs[i]]),
                            center_x,
                            center_y,
                            width_norm,
                            height_norm,
                        ]
                    )

        return im.astype(np.uint8), training_info

    def process_file(self, file):
        out_frame, training_info = self.process_frame(
            file, conf_thresh=self.conf_thresh
        )
        file_base = os.path.basename(file).split(".jpg")[0]
        # Save image
        cv2.imwrite(
            os.path.join(self.annotimage_out, file_base + "_annot.jpg"), out_frame
        )

        # Save text file
        if len(training_info):
            np.savetxt(
                os.path.join(self.training_out, file_base + ".txt"),
                training_info,
                delimiter=" ",
                fmt="%d %1.4f %1.4f %1.4f %1.4f",
            )
        else:
            np.savetxt(
                os.path.join(self.training_out, file_base + ".txt"),
                training_info,
                delimiter=" ",
            )

    def run_folder(self, conf_thresh=0.2, parallel=True):
        self.conf_thresh = conf_thresh
        files = glob.glob(os.path.join(self.imagefolder, "*.jpg"))

        # if parallel:
        #     with concurrent.futures.ThreadPoolExecutor() as executor:
        #         list(
        #             tqdm.tqdm(
        #                 executor.map(self.process_file, files, chunksize=16 * 50),
        #                 total=len(files),
        #             )
        #         )
        #         # executor.map(self.process_file, files)
        if parallel:
            with concurrent.futures.ProcessPoolExecutor() as executor:
                # list(
                #     tqdm.tqdm(
                #         executor.map(self.process_file, files, chunksize=16 * 50),
                #         total=len(files),
                #     )
                # )
#                 executor.map(self.process_file, files, chunksize=16 * 50)
                executor.map(self.process_file, files)

        else:
            t = tqdm.tqdm(files)
            for file in t:
                t.set_description(f"Working on file: {os.path.basename(file)}")
                t.refresh
                self.process_file(file)
