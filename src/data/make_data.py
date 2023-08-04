from . import coco, imagenet, obj365, openimages


def make_training_data(
    coco=True, obj365=True, openimages=True, imagenet=False, custom=False
):
    """Make the training data for the SquareEyes model

    Parameters
    ----------
    coco : bool, optional
        Include the COCO dataset, by default True
    obj365 : bool, optional
        Include the Objects365 dataset, by default True
    openimages : bool, optional
        Include the OpenImages dataset, by default True
    imagenet : bool, optional
        Include the ImageNet dataset, by default False
    custom : bool, optional
        Include custom dataset, by default False
    """
    if coco:
        print("Dataset: COCO")
        coco.download_and_convert_coco()

    if obj365:
        print("Dataset: Objects365")
        obj365.download_and_convert_obj365()

    if openimages:
        print("Dataset: OpenImages")
        openimages.download_and_convert_OpenImages()

    if imagenet:
        print("Dataset: ImageNet")
        imagenet.download_and_convert_ImageNet()
