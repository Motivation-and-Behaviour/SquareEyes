import textwrap

from src.data.make_data import make_training_data
from src.models.train_model import train_model

from . import make_yaml


def main():
    coco = True
    obj365 = True
    openimages = True
    imagenet = False
    custom = False
    name = "SquareEyes_v001"
    desc = """
    First version of the SquareEyes model.
    Includes COCO, Objects365, and OpenImages datasets with no custom data
    Trained for 50 epochs with batch size of 16 and image size of 640 using YOLOv8s as base"""

    make_training_data(
        coco=coco,
        obj365=obj365,
        openimages=openimages,
        imagenet=imagenet,
        custom=custom,
    )

    yaml_path = make_yaml(
        name=name,
        desc=textwrap.dedent(desc),
        coco=coco,
        obj365=obj365,
        openimages=openimages,
        imagenet=imagenet,
        custom=custom,
    )

    train_model("yolov8s.pt", yaml_path, 50, 16, 640)


if __name__ == "__main__":
    main()
