from . import classes, datasets


def make_training_data():
    # Fetch premade datasets
    # COCO
    datasets.download_coco()
    datasets.convert_dataset(
        dataset="coco",
        folders=["train2017", "val2017"],
        classes=classes.load_coco_classes(),
    )

    # Objects365
    datasets.download_and_convert_obj365()

    # Fetch custom data

    # OpenImages?
    # ImageNet?
    # Restrict premade to relevant classes


def make_training_yaml():
    pass
