import os
from pathlib import Path

import ultralytics as ul
from tqdm import tqdm

from .classes import load_coco_classes, load_main_classes


def download_coco(path="src/squareeyes/datasets"):
    # Get the labels
    url = "https://github.com/ultralytics/yolov5/releases/download/v1.0/coco2017labels.zip"
    dir = Path(path)
    ul.download([url], dir=dir)

    # Download data
    urls = [
        "http://images.cocodataset.org/zips/train2017.zip",  # 19G, 118k images
        "http://images.cocodataset.org/zips/val2017.zip",  # 1G, 5k images
    ]
    ul.download(urls, dir=dir / "coco" / "images", threads=2)


def convert_coco(path="src/squareeyes/datasets/coco"):
    coco_classes = load_coco_classes()
    folders = ["train2017", "val2017"]

    for folder in (pbar := tqdm(folders, position=0)):
        pbar.set_description(f"Converting {folder}")

        folder_path = Path(path) / "labels" / folder

        # Get all the txt files
        txt_files = list(folder_path.glob("*.txt"))

        # Convert all the txt files
        for txt_file in tqdm(txt_files, position=1, leave=False):
            filepath = convert_single_coco(txt_file, coco_classes)

            # If the file was deleted, remove the associated image
            if filepath is not None:
                os.remove(
                    str(filepath).replace("labels", "images").replace(".txt", ".jpg")
                )


def convert_single_coco(filepath, mappings):
    with open(filepath, "r") as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        line_parts = line.split()
        if line_parts[0] in mappings.keys():
            # Replace the class number
            line_parts[0] = str(mappings[line_parts[0]])
            new_lines.append(" ".join(line_parts) + "\n")

    # If there are no usable classes, delete the file and return the filepath
    if not new_lines:
        os.remove(filepath)
        return filepath
    else:
        with open(filepath, "w") as file:
            file.writelines(new_lines)
        return None
