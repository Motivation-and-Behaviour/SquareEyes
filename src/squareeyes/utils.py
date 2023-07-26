import os

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
