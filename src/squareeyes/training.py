from . import classes, datasets


def make_training_data():
    # Fetch premade datasets
    print("Dataset: COCO")
    datasets.download_and_convert_coco()

    print("Dataset: Objects365")
    datasets.download_and_convert_obj365()

    print("Dataset: OpenImages")
    datasets.download_and_convert_OpenImages()

    print("Dataset: ImageNet")
    datasets.download_and_convert_ImageNet()

    # Fetch custom data

    # ImageNet?
    # Restrict premade to relevant classes


def make_training_yaml():
    pass
