import os
from pathlib import Path

import numpy as np
import ultralytics as ul
from pycocotools.coco import COCO
from tqdm import tqdm

from .classes import load_coco_classes, load_main_classes, load_obj365_classes


def download_coco(dir="src/squareeyes/datasets"):
    """Download COCO data and annotations

    Adapted from ultralytics/cfg/datasets/coco.yaml

    Parameters
    ----------
    dir : str, optional
        location to download dataset, by default "src/squareeyes/datasets"
    """

    # Get the labels
    url = "https://github.com/ultralytics/yolov5/releases/download/v1.0/coco2017labels.zip"
    dir = Path(dir)
    ul.download([url], dir=dir)

    # Download data
    urls = [
        "http://images.cocodataset.org/zips/train2017.zip",  # 19G, 118k images
        "http://images.cocodataset.org/zips/val2017.zip",  # 1G, 5k images
    ]
    ul.download(urls, dir=dir / "coco" / "images", threads=2)


def convert_dataset(dataset, folders, classes, reset=False):
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
    dir = Path("src/squareeyes/datasets") / dataset

    marker_file = Path(dir) / ".converted"
    if marker_file.exists() and not reset:
        print(f"{dataset} has already been converted")
        return

    starting_n = len(list((dir / "labels").glob("*/*.jpg")))

    for folder in (pbar := tqdm(folders, position=0)):
        pbar.set_description(f"Converting {folder}")

        folder_path = Path(dir) / "labels" / folder

        # Get all the txt files
        txt_files = list(folder_path.glob("*.txt"))

        # Convert all the txt files
        for txt_file in tqdm(txt_files, position=1, leave=False):
            filepath = convert_single_coco(txt_file, classes)

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


def download_and_convert_obj365(dir="src/squareeyes/datasets/Objects365", reset=False):
    """Download Objects365 data and annotations

    Adapted from ultralytics/cfg/datasets/objects365.yaml

    Parameters
    ----------
    dir : str, optional
        location to download dataset, by default "src/squareeyes/datasets"
    reset : bool, optional
        whether to redo the conversion, by default False
    """
    classes = load_obj365_classes()
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
            if str(cid) not in classes.keys():
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
                                f"{classes[str(cid)]} {x:.5f} {y:.5f} {w:.5f} {h:.5f}\n"
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

    # Create a marker file to indicate that the conversion has been done
    with open(marker_file, "w"):
        pass
