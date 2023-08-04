from ultralytics import YOLO


def train_model(yolo_model, yaml_path, epochs, batch_size, img_size):
    model = YOLO(yolo_model)

    model.train(data=yaml_path, epochs=epochs, batch_size=batch_size, imgsz=img_size)
