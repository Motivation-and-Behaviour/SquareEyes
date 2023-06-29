# %%
import csv
import fnmatch
import glob
import multiprocessing
import os
from multiprocessing.pool import ThreadPool

import cv2
import pytesseract
from tqdm import tqdm


# %%
def find_folders(pattern, path):
    result = []
    for root, dirs, files in tqdm(os.walk(path)):
        for name in dirs:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def get_timestamps(images):
    def process_image(image):
        x, y, w, h = 760, 1080 - 32, 1920 - 760, 32
        im = cv2.imread(image)
        # Just get the timestamp section of image
        ROI = im[y : y + h, x : x + w]
        # Invert colours
        ROI = cv2.bitwise_not(ROI)
        # Add whitespace around text (improves accuracy)
        ROI = cv2.copyMakeBorder(
            ROI, 15, 15, 0, 0, cv2.BORDER_CONSTANT, value=[255, 255, 255]
        )
        unclean_timestamp = pytesseract.image_to_string(ROI, lang="eng")
        clean_timestamp = unclean_timestamp.replace("TLC130 ", "").strip()

        return (os.path.basename(image), clean_timestamp)

    with ThreadPool(multiprocessing.cpu_count()) as p:
        data = list(tqdm(p.imap(process_image, images), total=len(images)))

    return data


# %%
starting_folder = "/mnt/z/Square_Eyes_DP20_Data/Validation Study/Participant Data"

# image_folders = find_folders("*images*", starting_folder)
image_folders = [
    "/mnt/z/Square_Eyes_DP20_Data/Validation Study/Participant Data/4005/Images/Visit 1/images",
    "/mnt/z/Square_Eyes_DP20_Data/Validation Study/Participant Data/4005/Images/Visit 2/images",
    "/mnt/z/Square_Eyes_DP20_Data/Validation Study/Participant Data/4006/Images/Visit 1/images",
    "/mnt/z/Square_Eyes_DP20_Data/Validation Study/Participant Data/4006/Images/Visit 2/images",
]

# %%
for image_folder in tqdm(image_folders, desc="Folders"):
    images = glob.glob(image_folder + "/*.jpg")
    data = get_timestamps(images)
    with open(
        os.path.join(os.path.dirname(image_folder), "timestamps.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Timestamp"])
        writer.writerows(data)
