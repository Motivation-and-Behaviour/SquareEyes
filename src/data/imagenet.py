import csv
import os
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi
from PIL import Image
from tqdm import tqdm

from .. import utils
from .classes import load_imagenet_classes


def download_and_convert_ImageNet(dir="datasets/ImageNet", reset=False, cleanup=True):
    """Download and convert the ImageNet dataset to SquareEyes format

    Parameters
    ----------
    dir : str, optional
        Name of the dataset folder, by default "datasets/ImageNet"
    reset : bool, optional
        Whether to redo the conversion, by default False
    cleanup : bool, optional
        Whether to remove the downloaded zip files, by default True

    Raises
    ------
    Exception
        If the Kaggle API key is not found
    """
    dir = Path(dir)
    marker_file = Path(dir) / ".converted"
    if marker_file.exists() and not reset:
        print(f"ImageNet has already been converted")
        return

    classes_dict = load_imagenet_classes()

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
