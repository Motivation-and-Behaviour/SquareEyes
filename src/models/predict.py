from ultralytics import YOLO


class Predictor:
    def __init__(self, weights="models/SquareEyes.pt"):
        self.model = YOLO(weights)

    def predict(self, images, verbose=False, stream=True, conf=0.25):
        return self.model(
            images, verbose=False, stream=True, conf=conf, agnostic_nms=True
        )
