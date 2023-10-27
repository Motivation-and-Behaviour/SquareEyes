import csv
import datetime
import json
import multiprocessing
import os
import shutil
from datetime import datetime
from multiprocessing.pool import ThreadPool
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from tqdm import tqdm

from src.data.classes import load_main_classes, load_timelapse_mappings
from src.models.predict import Predictor


def process_folders(folders, n_back=5, overwrite=False):
    # The folder path should be e.g., ...\1173\Baseline\Images where there is
    # another folder `images` underneath.

    if not isinstance(folders, list):
        folders = [folders]

    # Initialize the predictor
    predictor = Predictor()

    for folder in tqdm(folders, desc="Processing folders", position=0, leave=True):
        marker_file = Path(folder) / ".converted"
        if marker_file.exists() and not overwrite:
            print(f"{folder} has already been processed")
            continue

        # TODO: Check that folder structure meets requirements
        # Copy the template file into the folder
        shutil.copy("data/SquareEyes Template.tdb", folder)

        # Call the predictor on the whole folder to get generator of predictions
        images_folder = os.path.join(folder, "images")
        images = [
            os.path.join(images_folder, f)
            for f in os.listdir(images_folder)
            if f.endswith(".jpg")
        ]

        predictions = predictor.predict(images_folder)

        csv_rows = []
        json_data = create_json_data()

        for prediction in tqdm(
            predictions,
            desc="Processing predictions",
            position=1,
            leave=False,
            total=len(images),
        ):
            # Save the prediction info to the importable csv file
            csv_rows.append(convert_prediction_csv(prediction))
            json_data["images"].append(convert_prediction_json(prediction))

        # Get the timestamps
        timestamps = extract_timestamps(images)

        # Add the timestamps to the csv rows
        for row in csv_rows:
            row_filename = row["File"]
            row["DateTime"] = timestamps.get(row_filename, "")

        csv_rows = calculate_n_back(csv_rows, n=n_back)

        print("Writing CSV File")
        with open(Path(folder) / "Image Data Import.csv", "w", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "RootFolder",
                    "File",
                    "RelativePath",
                    "DateTime",
                    "Device1",
                    "Device2",
                    "Device3",
                    "DeviceNum",
                    "RequiresScreening",
                    "NonScreenIndicators",
                ],
            )
            writer.writeheader()
            writer.writerows(csv_rows)

        print("Writing JSON File")
        with open(Path(folder) / "Square Eyes Detections.json", "w") as json_file:
            json.dump(json_data, json_file, indent=4)

        # Create a marker file to indicate that the processing has been done
        with open(marker_file, "w"):
            pass


def extract_timestamps(images):
    def process_image(image):
        x, y, w, h = 760, 1048, 1048, 32
        im = cv2.imread(image)
        # Just get the timestamp section of image
        roi = im[y : y + h, x : x + w]
        # Invert colours
        roi = cv2.bitwise_not(roi)
        # Add whitespace around text (improves accuracy)
        roi = cv2.copyMakeBorder(
            roi, 15, 15, 0, 0, cv2.BORDER_CONSTANT, value=[255, 255, 255]
        )
        unclean_timestamp = pytesseract.image_to_string(roi, lang="eng")
        if not unclean_timestamp.startswith("TLC130"):
            return os.path.basename(image), ""
        clean_timestamp = unclean_timestamp.replace("TLC130 ", "").strip()
        formatted_timestamp = datetime.strptime(
            clean_timestamp, "%Y/%m/%d %H:%M:%S"
        ).strftime("%Y-%m-%d %H:%M:%S")

        return os.path.basename(image), formatted_timestamp

    with ThreadPool(multiprocessing.cpu_count()) as p:
        data = list(
            tqdm(
                p.imap(process_image, images),
                desc="Extracting timestamps",
                position=1,
                leave=False,
                total=len(images),
            )
        )

    return dict(data)


def convert_prediction_csv(prediction):
    # Get the image file path and run timestamp extractor
    image_path = prediction.path

    mappings = load_timelapse_mappings()

    out_row = {
        "RootFolder": "Images",
        "File": os.path.basename(image_path),
        "RelativePath": "images",
        "Device1": "",
        "Device2": "",
        "Device3": "",
        "DeviceNum": "",
        "RequiresScreening": "FALSE",
        "NonScreenIndicators": "FALSE",
    }

    device_n = 1
    for box in prediction.boxes:
        label = mappings[int(box.cls)]
        if label.startswith("Device Indicator"):
            out_row["NonScreenIndicators"] = "TRUE"
        else:
            out_row[f"Device{device_n}"] = label
            out_row["DeviceNum"] = device_n
            device_n += 1

        out_row["RequiresScreening"] = "TRUE"

        if device_n > 3:
            break

    return out_row


def convert_prediction_json(prediction):
    full_image_path = prediction.path
    image_path = "images/" + os.path.basename(full_image_path)
    mappings = load_timelapse_mappings()

    new_data = {
        "file": image_path,
        "max_detection_confidence": 0.0,
        "detections": [],
    }

    for i, box in enumerate(prediction.boxes):
        if i == 0:
            # First detection should have max confidence
            new_data["max_detection_confidence"] = float(box.conf)

        label = mappings[int(box.cls)]
        det_type = "2" if label.startswith("Device Indicator") else "1"
        x_c, y_c, w, h = box.xywhn[0]
        x = float(x_c - w / 2)
        y = float(y_c - h / 2)

        new_data["detections"].append(
            {
                "category": det_type,
                "conf": float(box.conf),
                "bbox": [x, y, float(w), float(h)],
                "classifications": [[str(int(box.cls)), float(box.conf)]],
            }
        )

    return new_data


def create_json_data():
    return {
        "info": {
            "detector": "SquareEyes_V0.1",
            "detection_completion_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "format_version": "1.0",
        },
        "detection_categories": {"1": "screen", "2": "non-screen indicator"},
        "classification_categories": {
            str(key): value for key, value in load_timelapse_mappings().items()
        },
        "images": [],  # This will be populated dynamically
    }


def calculate_n_back(data: list[dict], n=5):
    for i in range(len(data)):
        start_index = max(0, i - n)
        end_index = min(len(data), i + n + 1)
        for j in range(start_index, end_index):
            data[j]["RequiresScreening"] = "TRUE"

    return data
