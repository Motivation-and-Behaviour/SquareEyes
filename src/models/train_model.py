from clearml import Task
from ultralytics import YOLO


def train_model(yolo_model, name, model_params):
    task = Task.init(
        project_name="Square Eyes",
        task_name=name,
    )

    task.set_parameter("model_variant", yolo_model.replace(".pt", ""))
    task.connect(model_params)

    model = YOLO(yolo_model)

    model.train(name=name, **model_params)
