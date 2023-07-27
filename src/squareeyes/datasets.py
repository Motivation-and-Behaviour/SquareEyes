import csv
import os
import re
from concurrent import futures
from pathlib import Path

import boto3
import botocore
import numpy as np
import requests
import ultralytics as ul
from datasets import load_dataset
from kaggle.api.kaggle_api_extended import KaggleApi
from PIL import Image
from pycocotools.coco import COCO
from tqdm import tqdm

from . import classes, utils


def download_and_convert_coco(dir="src/squareeyes/datasets/coco", reset=False):
    """Convert a dataset to SquareEyes format

    Parameters
    ----------
    dataset : str
        Name of the dataset folder
    folders : list
        A list of the subfolders to convert
    classes : dict
        Mapping of classes to convert
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
    ul.download([url], dir=dir)

    # Download data
    urls = [
        "http://images.cocodataset.org/zips/train2017.zip",  # 19G, 118k images
        "http://images.cocodataset.org/zips/val2017.zip",  # 1G, 5k images
    ]
    ul.download(urls, dir=dir / "images", threads=2)

    starting_n = len(list((dir / "labels").glob("*/*.jpg")))
    classes_dict = classes.load_coco_classes()

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

    finishing_n = len(list((dir / "labels").glob("*/*.jpg")))

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


def download_and_convert_obj365(
    dir="src/squareeyes/datasets/Objects365", reset=False, cleanup=True
):
    """Download Objects365 data and annotations

    Adapted from ultralytics/cfg/datasets/objects365.yaml

    Parameters
    ----------
    dir : str, optional
        location to download dataset, by default "src/squareeyes/datasets"
    reset : bool, optional
        whether to redo the conversion, by default False
    cleanup : bool, optional
        whether to delete the .tag.gz files once finished, by default True
    """
    classes_dict = classes.load_obj365_classes()
    marker_file = Path(dir) / ".converted"
    if marker_file.exists() and not reset:
        print(f"Objects365 has already been converted")
        return

    dir = Path(dir)
    for p in "images", "labels":
        (dir / p).mkdir(parents=True, exist_ok=True)
        for q in "train", "val":
            (dir / p / q).mkdir(parents=True, exist_ok=True)

    # Train, Val Splits
    for split, patches in [("train", 50 + 1), ("val", 43 + 1)]:
        print(f"Processing {split} in {patches} patches ...")
        images, labels = dir / "images" / split, dir / "labels" / split

        # Download
        url = f"https://dorc.ks3-cn-beijing.ksyun.com/data-set/2020Objects365%E6%95%B0%E6%8D%AE%E9%9B%86/{split}/"
        if split == "train":
            ul.download(
                [f"{url}zhiyuan_objv2_{split}.tar.gz"], dir=dir
            )  # annotations json
            ul.download(
                [f"{url}patch{i}.tar.gz" for i in range(patches)],
                dir=images,
                curl=True,
                threads=8,
            )
        elif split == "val":
            ul.download(
                [f"{url}zhiyuan_objv2_{split}.json"], dir=dir
            )  # annotations json
            ul.download(
                [f"{url}images/v1/patch{i}.tar.gz" for i in range(15 + 1)],
                dir=images,
                curl=True,
                threads=8,
            )
            ul.download(
                [f"{url}images/v2/patch{i}.tar.gz" for i in range(16, patches)],
                dir=images,
                curl=True,
                threads=8,
            )

        # Move
        for f in tqdm(images.rglob("*.jpg"), desc=f"Moving {split} images"):
            f.rename(images / f.name)  # move to /images/{split}

        # Labels
        coco = COCO(dir / f"zhiyuan_objv2_{split}.json")
        names = [x["name"] for x in coco.loadCats(coco.getCatIds())]
        for cid, cat in enumerate(names):
            # Check if class is in SquareEyes classes
            if str(cid) not in classes_dict.keys():
                continue

            catIds = coco.getCatIds(catNms=[cat])
            imgIds = coco.getImgIds(catIds=catIds)
            for im in tqdm(
                coco.loadImgs(imgIds),
                desc=f"Class {cat}",
            ):
                width, height = im["width"], im["height"]
                path = Path(im["file_name"])  # image filename
                try:
                    with open(labels / path.with_suffix(".txt").name, "a") as file:
                        annIds = coco.getAnnIds(
                            imgIds=im["id"], catIds=catIds, iscrowd=None
                        )
                        for a in coco.loadAnns(annIds):
                            # bounding box in xywh (xy top-left corner)
                            x, y, w, h = a["bbox"]
                            xyxy = np.array([x, y, x + w, y + h])[None]  # pixels(1,4)
                            # normalized and clipped
                            x, y, w, h = ul.utils.ops.xyxy2xywhn(
                                xyxy, w=width, h=height, clip=True
                            )[0]
                            file.write(
                                f"{classes_dict[str(cid)]} {x:.5f} {y:.5f} {w:.5f} {h:.5f}\n"
                            )
                except Exception as e:
                    print(e)

        # Remove any images that don't have a txt file
        txt_basenames = [
            os.path.splitext(os.path.basename(file))[0] for file in labels.glob("*.txt")
        ]

        for jpg in tqdm(images.rglob("*.jpg"), desc=f"Cleaning up {split} images"):
            jpg_basename = os.path.splitext(os.path.basename(jpg))[0]
            if jpg_basename not in txt_basenames:
                # Delete the jpg file
                os.remove(jpg)

        # Run the clean up
        if cleanup:
            for gz in tqdm(
                images.rglob("*.tar.gz"), desc=f"Cleaning up {split} tar.gz"
            ):
                os.remove(gz)

    # Create a marker file to indicate that the conversion has been done
    with open(marker_file, "w"):
        pass


def download_and_convert_OpenImages(
    dir="src/squareeyes/datasets/OpenImages", reset=False
):
    dir = Path(dir)
    classes_dict = classes.load_openimages_classes()
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


def download_and_convert_ImageNet(
    dir="src/squareeyes/datasets/ImageNet", reset=False, cleanup=True
):
    dir = Path(dir)
    marker_file = Path(dir) / ".converted"
    if marker_file.exists() and not reset:
        print(f"ImageNet has already been converted")
        return

    classes_dict = classes.load_imagenet_classes()

    for p in "images", "labels":
        (dir / p).mkdir(parents=True, exist_ok=True)
        for q in "train", "val":
            (dir / p / q).mkdir(parents=True, exist_ok=True)

    # Remember that you need to put the API key in ~/.kaggle/kaggle.json first
    api = KaggleApi()
    try:
        api.authenticate()
    except:
        raise Exception(
            "Couldn't authenticate with Kaggle API. Have you downloaded the API key?"
        )

    api.competition_download_files(
        "imagenet-object-localization-challenge", path=dir, quiet=False
    )

    zip_path = dir / "imagenet-object-localization-challenge.zip"

    zip_contents = utils.list_zip_contents(
        dir / "imagenet-object-localization-challenge.zip"
    )

    for split, csv_file in [
        ("train", "LOC_train_solution.csv"),
        ("val", "LOC_val_solution.csv"),
    ]:
        images, labels = dir / "images" / split, dir / "labels" / split
        print(f"Unzipping boxes for {split} ...")

        utils.extract_specific_files(zip_path, [csv_file], dir)

        usable_rows = []
        img_paths = []
        csv_filepath = dir / csv_file
        csv_nrows = utils.count_csv_rows(csv_filepath, dict=True)

        with open(csv_filepath, "r") as file:
            reader = csv.DictReader(file)
            for row in tqdm(reader, desc=f"Processing {split}", total=csv_nrows):
                if any(
                    labels in row["PredictionString"] for labels in classes_dict.keys()
                ):
                    img_idx = utils.find_partial_match(
                        zip_contents, f"{row['ImageId']}.JPEG"
                    )
                    if img_idx is None:
                        continue
                    img_paths.append(zip_contents[img_idx])
                    usable_rows.append(row)

        # Unpack the images
        print(f"Unzipping images for {split} ...")
        utils.extract_specific_files(zip_path, img_paths, images)
        # Make the labels
        for row in tqdm(usable_rows, desc=f"Making labels for {split}"):
            image_filename = f"{row['ImageId']}.JPEG"
            # Get the dimensions of the image
            with Image.open(images / image_filename) as img:
                width, height = img.size

            row_string_split = row["PredictionString"].split()
            for i in range(0, len(row_string_split), 5):
                bounding_box = row_string_split[i : i + 5]
                if bounding_box[0] not in classes_dict.keys():
                    continue

                x_min, y_min, x_max, y_max = bounding_box[1:]

                # Create a label file
                with open(labels / f"{row['ImageId']}.txt", "a") as file:
                    # Convert the bounding box to x, y, w, h
                    x = ((float(x_min) + float(x_max)) / 2) / width
                    y = ((float(y_min) + float(y_max)) / 2) / height
                    w = (float(x_max) - float(x_min)) / width
                    h = (float(y_max) - float(y_min)) / height
                    file.write(
                        f"{classes_dict[bounding_box[0]]} {x:.5f} {y:.5f} {w:.5f} {h:.5f}\n"
                    )

    # Run the clean up
    if cleanup:
        os.remove(zip_path)

    with open(marker_file, "w"):
        pass
