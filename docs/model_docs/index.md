# Introduction

These documents are to help other use and deploy the Square Eyes model.
These documents assume you have some experience with Python, and at least some knowledge on machine learning.

## Improving these documents

You can help us improve by submitting a [bug report](https://github.com/Motivation-and-Behaviour/SquareEyes/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=) when things break, or suggesting a [change to the docs](https://github.com/Motivation-and-Behaviour/SquareEyes/issues/new?assignees=&labels=documentation&projects=&template=documentation.md&title=%5BDOCS%5D).

## Broad Overview

The Square Eyes model is a computer vision model intended to detect screens in images captured from wearable cameras.
It's a fine-tuning of the [YOLOv8](https://yolov8.com/) model developed by [Ultralytics](https://www.ultralytics.com/).
Ultralytics provides a really straightforward interface for training and deploying the model, which removes the need for a lot of the usual boilerplate code.