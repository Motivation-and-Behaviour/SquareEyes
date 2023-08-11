import textwrap

from src.data.make_data import make_training_data
from src.models.make_yaml import make_training_yaml
from src.models.train_model import train_model
from src.utils.utils import generate_base_model_params


def main():
    use_coco = True
    use_obj365 = True
    use_openimages = True
    use_imagenet = False
    use_custom = False

    make_training_data(
        use_coco=use_coco,
        use_obj365=use_obj365,
        use_openimages=use_openimages,
        use_imagenet=use_imagenet,
        use_custom=use_custom,
    )

    yaml_name = "SquareEyes_Base"
    desc = """
    This is the base model for the Square Eyes model.
    Includes COCO, Objects365, and OpenImages datasets with no custom data for training or testing.
    """

    yaml_path = make_training_yaml(
        name=yaml_name,
        desc=textwrap.dedent(desc),
        use_coco=use_coco,
        use_obj365=use_obj365,
        use_openimages=use_openimages,
        use_imagenet=use_imagenet,
        use_custom=use_custom,
    )

    model_params = generate_base_model_params()

    model_params["epochs"] = 25
    model_params["data"] = yaml_path

    model_list = [
        {"name": "Base_small", "model": "yolov8s.pt"},
        {"name": "Base_medium", "model": "yolov8m.pt"},
        {"name": "Base_large", "model": "yolov8l.pt"},
        {"name": "Base_extralarge", "model": "yolov8x.pt"},
    ]

    for model in model_list:
        train_model(
            yolo_model=model["model"],
            name=model["name"],
            model_params=model_params,
        )


if __name__ == "__main__":
    main()
