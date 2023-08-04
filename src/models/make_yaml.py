from src.data import classes


def make_training_yaml(
    name, desc, coco=True, obj365=True, openimages=True, imagenet=False, custom=False
):
    main_classes = classes.load_main_classes()
    names = {key: value["label"] for key, value in main_classes.items()}

    data = {
        "name": name,
        "desc": desc,
        "path": "data/datasets",
        "train": [],
        "val": [],
        "names": names,
    }

    if coco:
        data["train"].append("coco/images/train2017")
        data["val"].append("coco/images/val2017")

    if obj365:
        data["train"].append("obj365/images/train")
        data["val"].append("obj365/images/val")

    if openimages:
        data["train"].append("openimages/images/train")
        data["val"].append("openimages/images/val")

    if imagenet:
        data["train"].append("imagenet/images/train")
        data["val"].append("imagenet/images/val")

    if custom:
        # TODO: Add custom dataset
        pass

    with open(f"models/configs/{name}.yaml", "w") as file:
        for line in data["desc"].split("\n"):
            file.write(f"# {line}\n")
        file.write(f"name: {data['name']}\n\n")
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
