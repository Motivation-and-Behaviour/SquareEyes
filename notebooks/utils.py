import concurrent.futures
import decimal
import multiprocessing
import os
import shutil
import zipfile

import requests
from pycocotools.coco import COCO
from tqdm import tqdm

multiprocessing.set_start_method("spawn", True)


def download_coco_subset(folder, labels=None, parallel=True, class_file=None):
    def convert_classes(old_id, class_list=None):
        return class_list[old_id]

    def truncate_to_str(n, places=6):
        return str(round(decimal.Decimal(n), places))

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
                        truncate_to_str(x),
                        truncate_to_str(y),
                        truncate_to_str(w),
                        truncate_to_str(h),
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
    print("Making folders")
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

