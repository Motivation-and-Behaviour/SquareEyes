import os
import zipfile
from typing import List

import requests
from tqdm import tqdm


def download(url: str, dir: os.PathLike):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get("content-length", 0))
    fname = dir / url.split("/")[-1]
    with tqdm.wrapattr(
        open(fname, "wb"),
        "write",
        miniters=1,
        desc=url.split("/")[-1],
        total=int(resp.headers.get("content-length", 0)),
    ) as fout:
        for chunk in resp.iter_content(chunk_size=4096):
            fout.write(chunk)


def list_zip_contents(zip_filepath):
    with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
        return zip_ref.namelist()


def extract_specific_files(
    zip_filepath: str, filenames: List[str], dest_path: str, progress: bool = True
) -> None:
    if len(filenames) == 1:
        progress = False
    with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
        if progress:
            iterator = tqdm(filenames)
        else:
            iterator = filenames
        for filename in iterator:
            try:
                file_data = zip_ref.read(filename)
                # use os.path.basename to remove directory info from filename
                with open(
                    os.path.join(dest_path, os.path.basename(filename)), "wb"
                ) as f:
                    f.write(file_data)
            except KeyError:
                print(f"{filename} is not found in the zip file.")


def find_partial_match(my_list, substring):
    for i, s in enumerate(my_list):
        if substring in s:
            return i
    return None


def count_csv_rows(csv_file, dict=True):
    with open(csv_file, "r") as f:
        if dict:
            return sum(1 for line in f) - 1
        else:
            return sum(1 for line in f)


def generate_base_model_params():
    return {
        "data": None,
        "epochs": 100,
        "patience": 50,
        "batch": 16,
        "imgsz": 640,
        "save": True,
        "exist_ok": False,
        "optimizer": "auto",
        "verbose": False,
        "seed": 0,
        "deterministic": True,
        "single_cls": False,
        "rect": False,
        "cos_lr": False,
        "close_mosaic": 0,
        "resume": False,
        "amp": True,
        "fraction": 1.0,
        "profile": False,
        "lr0": 0.01,
        "lrf": 0.01,
        "momentum": 0.937,
        "weight_decay": 0.0005,
        "warmup_epochs": 3.0,
        "warmup_momentum": 0.8,
        "warmup_bias_lr": 0.1,
        "box": 7.5,
        "cls": 0.5,
        "dfl": 1.5,
        "label_smoothing": 0.0,
        "nbs": 64,
        "val": True,
    }
