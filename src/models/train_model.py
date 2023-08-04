from ultralytics import YOLO


def train_model(yolo_model, yaml_path, name, epochs, batch_size, img_size):
    model = YOLO(yolo_model)

    model.train(
        data=yaml_path, name=name, epochs=epochs, batch=batch_size, imgsz=img_size
    )
