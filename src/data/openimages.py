import csv
import os
import re
from concurrent import futures
from pathlib import Path

import boto3
import botocore
from tqdm import tqdm

from .. import utils
from .classes import load_openimages_classes


def download_and_convert_OpenImages(dir="datasets/OpenImages", reset=False):
    """Download and convert the OpenImages dataset to SquareEyes format

    Parameters
    ----------
    dir : str, optional
        Name of the dataset folder, by default "datasets/OpenImages"
    reset : bool, optional
        whether to redo the conversion, by default False
    """
    dir = Path(dir)
    classes_dict = load_openimages_classes()
    marker_file = Path(dir) / ".converted"
    if marker_file.exists() and not reset:
        print(f"OpenImages has already been converted")
        return

    for p in "images", "labels":
        (dir / p).mkdir(parents=True, exist_ok=True)
        for q in "train", "val":
            (dir / p / q).mkdir(parents=True, exist_ok=True)

    for split, url_sect, split_name in [
        ("train", "v6/oidv6-train-", "train"),
        ("val", "v5/test-", "test"),
    ]:
        print(f"Downloading boxes for {split} ...")
        url = (
            f"https://storage.googleapis.com/openimages/{url_sect}annotations-bbox.csv"
        )
        boxes_file = dir / f"{url_sect.split('/')[-1]}annotations-bbox.csv"
        if not os.path.isfile(boxes_file):
            utils.download(url, dir)
        images, labels = dir / "images" / split, dir / "labels" / split
        imgs_set = set()
        boxes_file_nrows = utils.count_csv_rows(boxes_file, dict=True)
        with open(boxes_file, "r") as file:
            reader = csv.DictReader(file)
            for row in tqdm(reader, desc=f"Processing {split}", total=boxes_file_nrows):
                oi_label = row["LabelName"]
                if oi_label not in classes_dict.keys():
                    continue
                imgs_set.add(row["ImageID"])
                # Create a label file
                with open(labels / f"{row['ImageID']}.txt", "a") as file:
                    # Convert the bounding box to x, y, w, h
                    x = (float(row["XMin"]) + float(row["XMax"])) / 2
                    y = (float(row["YMin"]) + float(row["YMax"])) / 2
                    w = float(row["XMax"]) - float(row["XMin"])
                    h = float(row["YMax"]) - float(row["YMin"])
                    file.write(
                        f"{classes_dict[oi_label]} {x:.5f} {y:.5f} {w:.5f} {h:.5f}\n"
                    )
        # Create the image list to download
        with open(dir / f"{split}_ids.txt", "w") as file:
            for img in imgs_set:
                file.write(f"{split_name}/{img}\n")

        print(f"Downloading images for {split} ...")
        download_openimages(images, dir / f"{split}_ids.txt", 8)
        # Delete any txt where the image couldn't be downloaded
        for txt in tqdm(labels.glob("*.txt"), desc=f"Cleaning up {split}"):
            if not os.path.isfile(images / f"{txt.stem}.jpg"):
                os.remove(txt)

    with open(marker_file, "w"):
        pass


def download_openimages(download_folder, image_list, num_processes):
    BUCKET_NAME = "open-images-dataset"
    REGEX = r"(test|train|validation|challenge2018)/([a-fA-F0-9]*)"

    def check_and_homogenize_one_image(image):
        split, image_id = re.match(REGEX, image).groups()
        yield split, image_id

    def check_and_homogenize_image_list(image_list):
        for line_number, image in enumerate(image_list):
            try:
                yield from check_and_homogenize_one_image(image)
            except (ValueError, AttributeError):
                raise ValueError(
                    f"ERROR in line {line_number} of the image list. The following image "
                    f'string is not recognized: "{image}".'
                )

    def read_image_list_file(image_list_file):
        with open(image_list_file, "r") as f:
            for line in f:
                yield line.strip().replace(".jpg", "")

    def download_one_image(bucket, split, image_id, download_folder):
        try:
            bucket.download_file(
                f"{split}/{image_id}.jpg",
                os.path.join(download_folder, f"{image_id}.jpg"),
            )
        except botocore.exceptions.ClientError as exception:
            print(
                f"ERROR when downloading image `{split}/{image_id}`: {str(exception)}"
            )

    bucket = boto3.resource(
        "s3", config=botocore.config.Config(signature_version=botocore.UNSIGNED)
    ).Bucket(BUCKET_NAME)

    image_list = list(check_and_homogenize_image_list(read_image_list_file(image_list)))

    progress_bar = tqdm(total=len(image_list), desc="Downloading images", leave=True)
    with futures.ThreadPoolExecutor(max_workers=num_processes) as executor:
        all_futures = [
            executor.submit(
                download_one_image, bucket, split, image_id, download_folder
            )
            for (split, image_id) in image_list
        ]
        for future in futures.as_completed(all_futures):
            future.result()
            progress_bar.update(1)
    progress_bar.close()
