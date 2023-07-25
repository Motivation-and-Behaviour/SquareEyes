from . import datasets


def make_training_data():
    # Fetch premade datasets
    # COCO
    datasets.download_coco()
    datasets.convert_coco()

    # Fetch custom data

    # COCO
    # Objects365?
    # OpenImages?
    # ImageNet?
    # Restrict premade to relevant classes


def make_training_yaml():
    pass
