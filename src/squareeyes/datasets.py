from pathlib import Path

import ultralytics as ul


def download_coco(path="src/squareeyes/datasets"):
    # Get the labels
    url = "https://github.com/ultralytics/yolov5/releases/download/v1.0/coco2017labels.zip"
    dir = Path(path)
    ul.download([url], dir=dir)

    # Download data
    urls = [
        "http://images.cocodataset.org/zips/train2017.zip",  # 19G, 118k images
        "http://images.cocodataset.org/zips/val2017.zip",  # 1G, 5k images
        "http://images.cocodataset.org/zips/test2017.zip",  # 7G, 41k images (optional)
    ]
    ul.download(urls, dir=dir / "coco" / "images", threads=3)
    # Clean up zip files to free up space
    # Create some kind of flag that download is done
