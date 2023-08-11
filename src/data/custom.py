import glob
import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from label_studio_converter.imports import yolo
from tqdm import tqdm
from ultralytics import YOLO

from .classes import load_main_classes, load_snapit_classes


def fetch_and_preannotate_customval(
    network_dir="/mnt/MBData/Square_Eyes_DP20_Data/Validation Study/Participant Data",
    dir="datasets/Custom/validation_temp",
    model_path="runs/detect/SquareEyes_v002/weights/best.pt",
    reset=False,
):
    if not os.path.exists(network_dir):
        Exception("Can't find network drive. Are you connected?")

    seed = 42
    np.random.seed(seed)

    path_glob = network_dir + "/**/Images/**/*_Code_*.csv"

    # Find all the csv files of coded data
    print("Finding csv files of coded data...")
    files = glob.glob(path_glob, recursive=True)

    # read each csv into a dataframe
    df = pd.concat(
        [pd.read_csv(fp).assign(file_path=fp) for fp in files], ignore_index=True
    )

    # Remove the first visit from 4001 because they are so blurry
    df = df[~df["file_path"].str.contains("4001/Images/Visit 1")]

    # Add a column to the dataframe that indicates if image has one or multiple devices
    df.loc[:, "Devices"] = np.where(
        df["Device_2"].isna(), df["Device_1"], "multi device"
    )

    # Create a new data frame that randomly samples 1200 rows proportional to the frequency of devices
    df = df.sort_values(by="Filename")
    proportions = df[(df["device_no"] > 0) & (df["Devices"] != "multi device")][
        "Devices"
    ].value_counts(normalize=True)

    sample_counts = (proportions * 1200).round().astype(int)

    def sampling_func(group):
        device = group.name
        n = sample_counts[device]
        return group.sample(n, random_state=seed)

    sampled_df = (
        df[(df["device_no"] > 0) & (df["Devices"] != "multi device")]
        .groupby("Devices", group_keys=False)
        .apply(sampling_func)
    )

    sampled_multi = df[
        (df["device_no"] > 1) & (df["Devices"] == "multi device")
    ].sample(200, random_state=seed)

    val_df = pd.concat([sampled_df, sampled_multi], ignore_index=True)

    # Add the image path in
    val_df.loc[:, "image_path"] = (
        val_df["file_path"].str.rpartition("/")[0] + "/images/" + val_df["Filename"]
    )

    # Create the folders
    dir = Path(dir)
    dir.mkdir(parents=True, exist_ok=True)
    for p in "images", "labels":
        (dir / p).mkdir(parents=True, exist_ok=True)

    # Save the file for later use
    val_df.to_csv(dir / "validation_coding.csv", index=False)

    model = YOLO(model_path)

    dest_folder = dir / "images"
    # Loop through the image paths and copy them to the destination folder
    for _, row in tqdm(
        val_df.iterrows(), total=val_df.shape[0], desc="Copying and annotating images"
    ):
        image_path = row["image_path"]

        if os.path.exists(image_path):  # Ensure the source image exists
            # Extract the image file name from the path
            image_name = os.path.basename(image_path)

            # Create the destination path
            dest_path_jpg = os.path.join(dest_folder, image_name)
            dest_path_txt = dest_path_jpg.replace(".jpg", ".txt").replace(
                "images", "labels"
            )

            if not os.path.exists(dest_path_jpg):
                # Copy the image to the destination
                shutil.copy(image_path, dest_path_jpg)

            if not os.path.exists(dest_path_txt):
                # Create the predicted labels for the image
                results = model.predict(image_path, verbose=False)
                results[0].save_txt(dest_path_txt)

                if not len(results[0]):
                    with open(dest_path_txt, "w") as file:
                        pass

        else:
            print(f"Image not found: {image_path}")

    # Create the classes.txt file
    classes = load_main_classes()
    with open(dir / "classes.txt", "w") as file:
        for value in classes.values():
            file.write(value["label"] + "\n")

    # for p in "images", "labels":
    #     (dir / p).mkdir(parents=True, exist_ok=True)
    #     for q in "train", "val", "test":
    #         (dir / p / q).mkdir(parents=True, exist_ok=True)


def convert_yolo_to_ls(dir="datasets/Custom/validation_temp", name="customval"):
    yolo.convert_yolo_to_ls(
        input_dir=dir,
        out_file=dir + f"/{name}-tasks.json",
        image_root_url="/data/local-files/?d=GitHub/SquareEyes/" + dir + "/images",
        out_type="predictions",
    )


def copy_and_convert_snapit(
    dir="datasets/Custom/snapit_temp",
    network_dir="/mnt/MBData/Screen_Time_Measure_Development/SNAP_IT/YOLO_Training/Training_Images_V3",
    reset=False,
):
    if not os.path.exists(network_dir):
        Exception("Can't find network drive. Are you connected?")

    mappings = load_snapit_classes()

    # Create the folders
    dir = Path(dir)
    dir.mkdir(parents=True, exist_ok=True)
    for p in "images", "labels":
        (dir / p).mkdir(parents=True, exist_ok=True)

    files = glob.glob(network_dir + "/*.jpg", recursive=True)
    images = dir / "images"
    labels = dir / "labels"

    with ProcessPoolExecutor() as executor:
        list(
            tqdm(
                executor.map(
                    process_file,
                    files,
                    [mappings] * len(files),
                    [images] * len(files),
                    [labels] * len(files),
                ),
                total=len(files),
            )
        )

        # Create the classes.txt file
    classes = load_main_classes()
    with open(dir / "classes.txt", "w") as file:
        for value in classes.values():
            file.write(value["label"] + "\n")


def process_file(image_path, mappings, images, labels):
    image_name = os.path.basename(image_path)

    # Create the destination path
    dest_path_jpg = os.path.join(images, image_name)
    dest_path_txt = os.path.join(labels, image_name.replace(".jpg", ".txt"))

    if not os.path.exists(dest_path_jpg):
        # Copy the image to the destination
        shutil.copy(image_path, dest_path_jpg)

    if not os.path.exists(dest_path_txt):
        txt_path = image_path.replace(".jpg", ".txt")
        with open(txt_path, "r") as file:
            lines = file.readlines()

        new_lines = []
        for line in lines:
            line_parts = line.split()

            if line_parts[0] in mappings:
                line_parts[0] = str(mappings[line_parts[0]])
                new_lines.append(" ".join(line_parts) + "\n")

        with open(dest_path_txt, "w") as file:
            file.writelines(new_lines)
