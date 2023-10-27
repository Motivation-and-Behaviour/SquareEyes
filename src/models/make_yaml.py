from src.data import classes


def make_training_yaml(name, desc):
    """Create a yaml file for model training

    Parameters
    ----------
    name : str
        The name of the model
    desc : str
        The description of the model

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
        "train": ["training_data/images/train"],
        "val": ["training_data/images/val"],
        "test": ["training_data/images/test"],
        "names": names,
    }

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
        file.write("test:\n")
        for item in data["test"]:
            file.write(f"  - {item}\n")
        file.write("names:\n")
        for key, value in data["names"].items():
            file.write(f"  {key}: {value}\n")

    return f"models/configs/{name}.yaml"
