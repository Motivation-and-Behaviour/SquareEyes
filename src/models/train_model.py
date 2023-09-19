from clearml import Task
from ultralytics import YOLO


def train_model(yolo_model, model_name, model_params, clearml_name=None):
    if clearml_name == None:
        clearml_name = model_name

    task = Task.init(
        project_name="Square Eyes",
        task_name=clearml_name,
    )

    task.set_parameter("model_variant", yolo_model.replace(".pt", ""))
    task.connect(model_params)

    config_yaml = task.connect_configuration(
        name="Ultralytics YAML",
        configuration=model_params["data"],
    )

    model = YOLO(yolo_model)

    model.train(name=model_name, **model_params)

    task.close()
