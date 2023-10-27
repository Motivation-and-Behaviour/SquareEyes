import os
from pathlib import Path

import numpy as np
import ultralytics as ul
from pycocotools.coco import COCO
from tqdm import tqdm

from .classes import load_obj365_classes


def download_and_convert_obj365(dir="datasets/Objects365", reset=False, cleanup=True):
    """Download Objects365 data and annotations

    Adapted from ultralytics/cfg/datasets/objects365.yaml

    Parameters
    ----------
    dir : str, optional
        location to download dataset, by default "datasets/Objects365"
    reset : bool, optional
        whether to redo the conversion, by default False
    cleanup : bool, optional
        whether to delete the .tag.gz files once finished, by default True
    """
    classes_dict = load_obj365_classes()
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
