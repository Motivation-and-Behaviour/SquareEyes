from . import coco, imagenet, obj365, openimages


def make_training_data(
    use_coco=True,
    use_obj365=True,
    use_openimages=True,
    use_imagenet=False,
    use_custom=False,
):
    """Make the training data for the SquareEyes model

    Parameters
    ----------
    use_coco : bool, optional
        Include the COCO dataset, by default True
    use_obj365 : bool, optional
        Include the Objects365 dataset, by default True
    use_openimages : bool, optional
        Include the OpenImages dataset, by default True
    use_imagenet : bool, optional
        Include the ImageNet dataset, by default False
    use_custom : bool, optional
        Include custom dataset, by default False
    """
    if use_coco:
        print("Dataset: COCO")
        coco.download_and_convert_coco()

    if use_obj365:
        print("Dataset: Objects365")
        obj365.download_and_convert_obj365()

    if use_openimages:
        print("Dataset: OpenImages")
        openimages.download_and_convert_OpenImages()

    if use_imagenet:
        print("Dataset: ImageNet")
        imagenet.download_and_convert_ImageNet()
