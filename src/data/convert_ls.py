import json
import os
import random
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from .classes import load_main_classes


def process_ls_json_folder(
    root_dir, ls_folder_name="ls_annotations", split=0.8, out_dir=None
):
    mappings = {value["label"]: key for key, value in load_main_classes().items()}

    if out_dir is None:
        out_dir = root_dir

    ls_folder = Path(root_dir) / ls_folder_name
    images_folder = Path(out_dir) / "images"
    labels_folder = Path(out_dir) / "labels"

    for folder in [images_folder, labels_folder]:
        (folder / "train").mkdir(parents=True, exist_ok=True)
        (folder / "val").mkdir(parents=True, exist_ok=True)

    ls_files = [f for f in ls_folder.iterdir()]
    counter = {}

    for ls_file in tqdm(ls_files, desc="Processing JSON files"):
        img_path, annots, _ = process_ls_json(ls_file, images_folder, mappings)
        if img_path is None:
            continue

        img_name = img_path.split("/")[-1]
        txt_name = Path(img_name).with_suffix(".txt").name

        folder = "train" if random.random() < split else "val"
        dest_images = images_folder / folder
        dest_labels = labels_folder / folder

        # Copy the image
        shutil.copy(img_path, dest_images / img_name)

        # Create the label
        with open(dest_labels / txt_name, "w") as f:
            f.write("\n".join(annots))

        counter[folder] = counter.get(folder, 0) + 1

    print(
        f"Finished processing {len(ls_files)}\nTrain:\t{counter['train']}\nVal:\t{counter['val']}"
    )


def process_customdata(out_dir):
    images_folder = Path(out_dir) / "images"
    labels_folder = Path(out_dir) / "labels"

    for folder in [images_folder, labels_folder]:
        (folder / "train").mkdir(parents=True, exist_ok=True)
        (folder / "val").mkdir(parents=True, exist_ok=True)
        (folder / "test").mkdir(parents=True, exist_ok=True)

    snapit_df, snapiit_label_data = process_ls_json_folder_customdata(
        "datasets/Custom/snapit/annotating", images_folder
    )
    custom_df, custom_label_data = process_ls_json_folder_customdata(
        "datasets/Custom/validation_study/annotating", images_folder
    )

    df = pd.concat([snapit_df, custom_df], ignore_index=True)
    df_updated = assign_partition(df)
    label_data = {**snapiit_label_data, **custom_label_data}

    counter = {}
    for _, row in tqdm(
        df_updated.iterrows(),
        total=df_updated.shape[0],
        desc="Copying and annotating images",
    ):
        img_name = row["img"]
        img_path, annots = label_data[img_name][0], label_data[img_name][1]
        txt_name = Path(img_name).with_suffix(".txt").name
        image_path = images_folder / img_name
        folder = row["set"]

        if pd.isna(folder):
            print("Image could not be assigned to a partition")
            continue

        if os.path.exists(img_path):  # Ensure the source image exists
            # Create the destination path
            dest_images = images_folder / folder
            dest_labels = labels_folder / folder

            # Copy the image
            shutil.copy(img_path, dest_images / img_name)

            # Create the label
            with open(dest_labels / txt_name, "w") as f:
                f.write("\n".join(annots))

            counter[folder] = counter.get(folder, 0) + 1

        else:
            print(f"Image not found: {image_path}")

    print(
        f"Finished processing \nTrain:\t{counter['train']}\nVal:\t{counter['val']}\nTest:\t{counter['test']}"
    )

    return df_updated


def process_ls_json_folder_customdata(
    root_dir, images_folder, ls_folder_name="ls_annotations"
):
    mappings = {value["label"]: key for key, value in load_main_classes().items()}

    ls_folder = Path(root_dir) / ls_folder_name
    ls_files = [f for f in ls_folder.iterdir()]

    data = []
    label_data = {}

    for ls_file in tqdm(ls_files, desc="Processing JSON files"):
        img_path, annots, annot_dict = process_ls_json(ls_file, images_folder, mappings)
        if img_path is None:
            continue
        data.append(annot_dict)
        img_name = img_path.split("/")[-1]
        label_data[img_name] = (img_path, annots)

    df = pd.DataFrame(data).fillna(0)
    return df, label_data


def assign_partition(df):
    partitions = ["train", "test", "val"]
    partition_calcs = {"train": 1 / 7, "test": 1, "val": 1 / 2}

    df["set"] = np.nan
    row_sum = df.select_dtypes(include=["number"]).sum(axis=1)
    df["background"] = row_sum.apply(lambda x: 0 if x > 0 else 1)

    devices = [col for col in df.columns[2:] if col not in ["set"]]
    participants = df["id"].unique()

    device_partition_counts = {
        device: {"train": 0, "test": 0, "val": 0} for device in devices
    }
    df[devices] = df[devices].fillna(0)

    random.shuffle(devices)

    for device in devices:
        for participant in participants:
            subset = df[(df["id"] == participant) & (df[device] == 1)]
            # Check if any of this subset has already been assigned
            unique_values = subset["set"][pd.notna(subset["set"])].unique()
            if len(unique_values):
                assigned = unique_values[0]
            else:
                assigned = min(
                    partitions,
                    key=lambda x: device_partition_counts[device][x]
                    * partition_calcs[x],
                )

            df.loc[(df["id"] == participant) & (df[device] == 1), "set"] = assigned
            device_partition_counts[device][assigned] += 1

    sampled = (
        df.groupby(["id"] + devices)
        .apply(lambda x: x.sample(min(len(x), 30)))
        .reset_index(drop=True)
    )

    return sampled


def process_ls_json(json_file, images_folder, mappings, overwrite=False):
    with open(json_file) as f:
        data = json.load(f)

    if data["was_cancelled"]:
        # This one was skipped, don't process
        return None, None, None

    img_path = data["task"]["data"]["image"].replace(
        "/data/local-files/?d=", "/home/tasanders/"
    )
    img_name = img_path.split("/")[-1]
    id = img_name[:4]

    # Check if the image is already in the folder
    img_exists = any(images_folder.rglob(img_name))

    if img_exists and not overwrite:
        # This one was already processed, don't process
        return None, None, None

    # If we get this far, it's OK to process the annotation
    new_annots = []
    annot_dict = {"id": id, "img": img_name}
    annotations = data["result"]

    for annot in annotations:
        label = annot["value"]["rectanglelabels"][0]
        label_id = mappings[label]
        x = (annot["value"]["x"] + annot["value"]["width"] / 2) / 100
        y = (annot["value"]["y"] + annot["value"]["height"] / 2) / 100
        w = annot["value"]["width"] / 100
        h = annot["value"]["height"] / 100
        annot_dict[label] = 1

        new_annots.append(f"{label_id} {x} {y} {w} {h}")

    return img_path, new_annots, annot_dict
