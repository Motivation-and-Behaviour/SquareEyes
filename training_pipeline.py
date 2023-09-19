import textwrap

from src.data.clearml_utils import fetch_clearml_dataset
from src.models.make_yaml import make_training_yaml
from src.models.train_model import train_model
from src.utils.utils import generate_base_model_params


def main():
    print("Fetching datasets")
    fetch_clearml_dataset("Full Training Data")

    yaml_name = "SquareEyes_FullTraining"
    desc = """
    This is a base model for the Square Eyes model.
    Includes COCO, Objects365, Imagenet, and OpenImages datasets, and data from SNAPIT and our validation study. 
    Open source datasets have been subset to only images that are similar to those that we expect to capture. 
    """

    yaml_path = make_training_yaml(name=yaml_name, desc=textwrap.dedent(desc))

    model_params = generate_base_model_params()

    model_params["epochs"] = 500
    model_params["data"] = yaml_path
    model_params["patience"] = 150

    train_model(
        yolo_model="yolov8l.pt",
        model_name="SquareEyes_Full_V2",
        model_params=model_params,
        clearml_name="Base Square Eyes Full Model - Updated Dataset",
    )


if __name__ == "__main__":
    main()
