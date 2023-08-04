import os
from pathlib import Path

import ultralytics as ul
from tqdm import tqdm

from .classes import load_coco_classes


def download_and_convert_coco(dir="data/datasets/coco", reset=False):
    """Download and convert the COCO dataset to SquareEyes format

    Parameters
    ----------
    dir : str, optional
        Name of the dataset folder, by default "data/datasets/coco"
    reset : bool, optional
        whether to redo the conversion, by default False
    """

    # Check if the conversion has already been done
    dir = Path(dir)

    marker_file = Path(dir) / ".converted"
    if marker_file.exists() and not reset:
        print(f"COCO has already been converted")
        return

    # Get the labels
    url = "https://github.com/ultralytics/yolov5/releases/download/v1.0/coco2017labels.zip"
    dir = Path(dir)
    ul.download([url], dir=dir.parent)

    # Download data
    urls = [
        "http://images.cocodataset.org/zips/train2017.zip",  # 19G, 118k images
        "http://images.cocodataset.org/zips/val2017.zip",  # 1G, 5k images
    ]
    ul.download(urls, dir=dir / "images", threads=2)

    starting_n = len(list((dir / "images").glob("*/*.jpg")))
    classes_dict = load_coco_classes()

    for folder in (pbar := tqdm(["train2017", "val2017"], position=0)):
        pbar.set_description(f"Converting {folder}")

        folder_path = Path(dir) / "labels" / folder

        # Get all the txt files
        txt_files = list(folder_path.glob("*.txt"))

        # Convert all the txt files
        for txt_file in tqdm(txt_files, position=1, leave=False):
            filepath = convert_single_coco(txt_file, classes_dict)

            # If the file was deleted, remove the associated image
            if filepath is not None:
                os.remove(
                    str(filepath).replace("labels", "images").replace(".txt", ".jpg")
                )

    finishing_n = len(list((dir / "images").glob("*/*.jpg")))

    print(f"Start: \t{starting_n}\nEnd: \t{finishing_n}")

    # Create a marker file to indicate that the conversion has been done
    with open(marker_file, "w"):
        pass


def convert_single_coco(filepath, mappings):
    """Convert a single COCO txt file to SquareEyes format

    Parameters
    ----------
    filepath : str
        location of the file
    mappings : dict
        mapping of COCO classes to SquareEyes classes

    Returns
    -------
    None or str
        Returns None if the file was updated, or the filepath if the file was deleted
    """
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
