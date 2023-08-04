import textwrap

from src.data.make_data import make_training_data
from src.models.make_yaml import make_training_yaml
from src.models.train_model import train_model


def main():
    use_coco = True
    use_obj365 = True
    use_openimages = True
    use_imagenet = False
    use_custom = False
    name = "SquareEyes_v001"
    desc = """
    First version of the SquareEyes model.
    Includes COCO, Objects365, and OpenImages datasets with no custom data
    Trained for 50 epochs with batch size of 16 and image size of 640 using YOLOv8s as base"""

    make_training_data(
        use_coco=use_coco,
        use_obj365=use_obj365,
        use_openimages=use_openimages,
        use_imagenet=use_imagenet,
        use_custom=use_custom,
    )

    yaml_path = make_training_yaml(
        name=name,
        desc=textwrap.dedent(desc),
        use_coco=use_coco,
        use_obj365=use_obj365,
        use_openimages=use_openimages,
        use_imagenet=use_imagenet,
        use_custom=use_custom,
    )

    train_model(
        yolo_model="yolov8s.pt",
        yaml_path=yaml_path,
        name=name,
        epochs=50,
        batch_size=16,
        img_size=640,
    )


if __name__ == "__main__":
    main()
