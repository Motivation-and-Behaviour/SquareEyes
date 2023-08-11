from src.data import classes


def make_training_yaml(
    name,
    desc,
    use_coco=True,
    use_obj365=True,
    use_openimages=True,
    use_imagenet=False,
    use_custom=False,
):
    """Create a yaml file for model training

    Parameters
    ----------
    name : str
        The name of the model
    desc : str
        The description of the model
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

    Returns
    -------
    str
        Path to the generated yaml file
    """
    main_classes = classes.load_main_classes()
    names = {key: value["label"] for key, value in main_classes.items()}

    data = {
        "name": name,
        "desc": desc,
        "path": ".",
        "train": [],
        "val": [],
        "names": names,
    }

    if use_coco:
        data["train"].append("coco/images/train2017")
        data["val"].append("coco/images/val2017")

    if use_obj365:
        data["train"].append("Objects365/images/train")
        data["val"].append("Objects365/images/val")

    if use_openimages:
        data["train"].append("OpenImages/images/train")
        data["val"].append("OpenImages/images/val")

    if use_imagenet:
        data["train"].append("ImageNet/images/train")
        data["val"].append("ImageNet/images/val")

    if use_custom:
        # TODO: Add custom dataset
        pass

    with open(f"models/configs/{name}.yaml", "w") as file:
        for line in data["desc"].split("\n"):
            file.write(f"# {line}\n")
        file.write(f"path: {data['path']}\n")
        file.write("train:\n")
        for item in data["train"]:
            file.write(f"  - {item}\n")
        file.write("val:\n")
        for item in data["val"]:
            file.write(f"  - {item}\n")
        file.write("names:\n")
        for key, value in data["names"].items():
            file.write(f"  {key}: {value}\n")

    return f"models/configs/{name}.yaml"
