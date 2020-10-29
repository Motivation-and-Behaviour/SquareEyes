import concurrent.futures
import decimal
import glob
import multiprocessing
import os
import shutil
import zipfile
from collections import Counter

import pandas as pd
import requests
from pycocotools.coco import COCO
from tqdm import tqdm

multiprocessing.set_start_method("spawn", True)


def _truncate_to_str(n, places=6):
    return str(round(decimal.Decimal(n), places))


def download_coco_subset(folder, labels=None, parallel=True, class_file=None):
    def convert_classes(old_id, class_list=None):
        return class_list[old_id]

    def dwnld_im_and_lbls(
        image,
        images_folder=os.path.join(folder, "images"),
        labels_folder=os.path.join(folder, "labels"),
    ):
        # Images
        if not os.path.exists(os.path.join(images_folder, image["file_name"])):
            r = requests.get(image["coco_url"], allow_redirects=True)
            with open(
                os.path.join(images_folder, image["file_name"]), "wb"
            ) as img_data:
                img_data.write(r.content)

        # Labels
        label_name = os.path.join(
            labels_folder, image["file_name"].replace(".jpg", ".txt")
        )

        if not os.path.exists(label_name):
            ann_ids = coco.getAnnIds(imgIds=image["id"], catIds=cat_ids, iscrowd=False)
            anns = coco.loadAnns(ann_ids)

            with open(label_name, "a") as label_file:
                for ann in anns:
                    # Convert the class ID
                    class_id = convert_classes(
                        ann["category_id"], class_list=class_list
                    )

                    xmin = ann["bbox"][0]
                    ymin = ann["bbox"][1]
                    xmax = ann["bbox"][2] + ann["bbox"][0]
                    ymax = ann["bbox"][3] + ann["bbox"][1]

                    x = (xmin + xmax) / 2
                    y = (ymin + ymax) / 2

                    w = xmax - xmin
                    h = ymax - ymin

                    x = x * (1 / image["width"])
                    w = w * (1 / image["width"])
                    y = y * (1 / image["height"])
                    h = h * (1 / image["height"])

                    label_items = [
                        str(class_id),
                        _truncate_to_str(x),
                        _truncate_to_str(y),
                        _truncate_to_str(w),
                        _truncate_to_str(h),
                    ]

                    label_file.write(" ".join(label_items))
                    label_file.write("\n")
            label_file.close()

    # Set decimals to round down for proper truncation
    decimal.getcontext().rounding = decimal.ROUND_DOWN

    # First check if the JSONs are available
    print("Finding meta-data")
    if not os.path.exists(folder + "//instances_val2017.json") or not os.path.exists(
        folder + "//instances_train2017.json"
    ):
        print("Missing JSON files")
        # Check if the zip file exists
        if not os.path.exists(folder + "//annotations_trainval2017.zip"):
            print("Missing Zip file")
            # No JSON or zip, download the file
            r = requests.get(
                "http://images.cocodataset.org/annotations/annotations_trainval2017.zip",
                allow_redirects=True,
            )
            with open(folder + "//annotations_trainval2017.zip", "wb") as zipdata:
                zipdata.write(r.content)
            print("Zip file downloaded")

        # Off chance that annotations folder already exists
        if os.path.exists(os.path.join(folder, "annotations")) and os.path.isdir(
            os.path.join(folder, "annotations")
        ):
            shutil.rmtree(os.path.join(folder, "annotations"))

        # Extract the zip
        with zipfile.ZipFile(
            folder + "//annotations_trainval2017.zip", "r"
        ) as to_unzip:
            to_unzip.extractall(folder)
        print("zip file extracted")

        # Move files to top level
        for file in ["instances_val2017.json", "instances_train2017.json"]:
            shutil.copyfile(
                os.path.join(folder, "annotations", file), os.path.join(folder, file),
            )

        # Remove annotations folder
        shutil.rmtree(os.path.join(folder, "annotations"))

    # Check if the folders exists, or make them
    if not os.path.exists(os.path.join(folder, "images")):
        os.makedirs(os.path.join(folder, "images"))
    if not os.path.exists(os.path.join(folder, "labels")):
        os.makedirs(os.path.join(folder, "labels"))

    # Get the COCO labels and image IDs
    print("Getting coco data")
    for file in ["instances_val2017.json", "instances_train2017.json"]:
        print(f"Working on {file}")
        coco = COCO(os.path.join(folder, file))

        cats = coco.loadCats(coco.getCatIds())
        if labels == None:
            # Use all labels
            labels = [cat["name"] for cat in cats]

        cat_ids = coco.getCatIds(catNms=labels)

        img_ids = set()
        for cat in cat_ids:
            for x in coco.getImgIds(catIds=cat):
                img_ids.add(x)

        images = coco.loadImgs(img_ids)

        # Create the conversion list for the classes

        if not "class_list" in locals():
            with open(class_file, "r") as text_file:
                classes = text_file.read().split("\n")

            class_list = {}
            for cat in cats:
                try:
                    class_list[cat["id"]] = classes.index(cat["name"])
                except ValueError:
                    pass

        if parallel:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                list(tqdm(executor.map(dwnld_im_and_lbls, images), total=len(images)))
        else:
            t = tqdm(images)
            for image in t:
                t.set_description(f"Working on image id: {image['id']}")
                t.refresh
                dwnld_im_and_lbls(image)


def download_openimages_subset(
    folder, labels_dict=None, parallel=True, class_file=None, core_only=True
):
    OID_URL = "https://storage.googleapis.com/openimages/2018_04/"
    labels_file = "class-descriptions-boxable.csv"
    csv_files = [
        "train-annotations-bbox.csv",
        "validation-annotations-bbox.csv",
        "test-annotations-bbox.csv",
    ]

    # Check for CSV files and download if missing
    for csv_file in csv_files + [labels_file]:
        if not os.path.exists(os.path.join(folder, csv_file)):
            if csv_file in csv_files:
                file_url = OID_URL + csv_file.split("-")[0] + "/" + csv_file
            else:
                file_url = OID_URL + csv_file

            r = requests.get(file_url, allow_redirects=True, stream=True)
            total_size = int(r.headers.get("content-length", 0))
            progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
            with open(os.path.join(folder, csv_file), "wb") as f:
                for data in r.iter_content(1024):
                    progress_bar.update(len(data))
                    f.write(data)
            progress_bar.close()

    # Combine the csv files into one pandas df
    df = pd.concat(
        (
            pd.read_csv(os.path.join(folder, csv_file)).assign(
                dataset=csv_file.split("-")[0]  # dataset image is in
            )
            for csv_file in csv_files
        )
    )
    df_labels = pd.read_csv(
        os.path.join(folder, labels_file), header=None, names=["LabelName", "Label"]
    )

    # Limit labels to those from our list of interest
    df_labels = df_labels.loc[df_labels["Label"].isin(labels_dict.keys())]

    # Merge and drop unneeded
    df = df.merge(df_labels, how="right", on="LabelName")
    df = df.loc[
        (df["IsGroupOf"] == 0) & (df["IsDepiction"] == 0) & (df["IsInside"] == 0)
    ]

    # Create list of images to download based on labels
    image_list = set(list(df["dataset"] + "/" + df["ImageID"] + ".jpg"))

    # Check if the folders exists, or make them
    print("Making folders")
    if not os.path.exists(os.path.join(folder, "images")):
        os.makedirs(os.path.join(folder, "images"))
    if not os.path.exists(os.path.join(folder, "labels")):
        os.makedirs(os.path.join(folder, "labels"))

    # Convert the label numbers to match the class file
    with open(class_file, "r") as f:
        classes = f.read().split("\n")

    if core_only:
        # Keep only those in the class list
        df = df.loc[
            df["Label"].apply(lambda x: True if labels_dict[x] in classes else False)
        ]
    else:
        for val in labels_dict.values():
            if val not in classes:
                classes.append(val)
        # Create revised class list
        with open(os.path.join(folder, "new_class_list.txt", "a")) as new_classes:
            new_classes.write("\n".join(classes))

    df["LabelNum"] = df["Label"].apply(lambda x: classes.index(labels_dict[x]))

    # Function to download an image
    download_command = (
        "aws s3 --no-sign-request --only-show-errors cp s3://open-images-dataset/"
    )

    def dwnld_im(image, images_folder=os.path.join(folder, "images")):
        if not os.path.exists(os.path.join(images_folder, image.split("/")[-1])):
            os.system(download_command + image + ' "' + images_folder + '"')

    # Iterate over the image list and download the images
    print(f"getting images ({len(image_list)})")
    if parallel:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            list(tqdm(executor.map(dwnld_im, image_list), total=len(image_list)))
    else:
        t = tqdm(image_list)
        for image in t:
            t.set_description(f"Working on image: {image}")
            t.refresh
            dwnld_im(image)

    def create_label(image_id, label_num, x_min, x_max, y_min, y_max, folder=folder):
        # Check if the image has been downloaded
        labels_folder = os.path.join(folder, "images")
        if os.path.exists(os.path.join(labels_folder, image_id + ".jpg")):
            with open(
                os.path.join(labels_folder, image_id + ".txt"), "a"
            ) as label_file:
                label_items = [
                    str(label_num),
                    _truncate_to_str((x_max + x_min) / 2),
                    _truncate_to_str((y_max + y_min) / 2),
                    _truncate_to_str(x_max - x_min),
                    _truncate_to_str(y_max - y_min),
                ]

                label_file.write(" ".join(label_items))
                label_file.write("\n")

    # Create the labels for each of the images
    df.apply(
        lambda x: create_label(
            x["ImageID"], x["LabelNum"], x["XMin"], x["XMax"], x["YMin"], x["YMax"]
        ),
        axis=1,
    )


def count_instances(folders, class_file, parallel=True):
    # Get classes first
    def read_txt(file):
        with open(file, "r") as f:
            try:
                return Counter(list(map(int, f.read().split()[::5])))
            except ValueError:  # First value isn't a number
                return None

    if isinstance(folders, str):
        folders = [folders]

    files = []
    for folder in folders:
        files.extend(glob.glob(os.path.join(folder, "*.txt")))

    if parallel:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(tqdm(executor.map(read_txt, files), total=len(files)))
    else:
        t = tqdm(files)
        results = []
        for file in t:
            t.set_description(f"Working on file: {file}")
            t.refresh
            results.append(read_txt(file))

    with open(class_file, "r") as f:
        classes = f.read().split("\n")

    labels = pd.DataFrame(data=classes, columns=["label"])
    labels = labels.reindex(columns=["label", "objects", "images"])
    labels.fillna(0, inplace=True)

    for codes in tqdm(results):
        if codes == None:
            continue
        else:
            for key in codes:
                labels.loc[key, "objects"] += codes[key]
                labels.loc[key, "images"] += 1

    return labels

