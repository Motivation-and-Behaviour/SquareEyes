# Ethics Background

As a coder, you will have access to the images collected during data collection.
It is important to remember that these are captured by real people in their own homes, and they have put their trust in us to handle their data with care and respect.

We've gone to great lengths to ensure that we maintain the privacy of participants, and also third-parties who may have been incidentally captured.
These procedures extend to the processes used during the coding of the data.

Below are some of the procedures that are used during data collection to maintain privacy.
You don't need to know all of these to code images, but it is useful to understand the extent to which we've gone to protect the privacy of participants.
It will also help add context to some of the things you might see in images, such as blurred faces.

## Data Collection Privacy

### Encrypted Write-Only SD Cards

We use special *write-only* SD cards to capture images.
These SD cards allow the camera to write data to the card, but not read it back.
Specifically, we use the [swissbit iShield sd card](https://www.swissbit.com/en/products/security-products/ishield-archive-and-ishield-camera/).
The cards are encrypted using a key known only to the data collection team.

Using these write-only cards means that the data are secure even if the camera is lost.
It also protects third-party privacy, as participants cannot access the data on their camera.

### Face Blurring

When the images are exported off the camera, they are processed using a face detection algorithm.
Each time a face is detected, the region with the face is blurred and only the blurred version of the image is retained.
We perform this prior to anyone (both research team and participants) viewing the images, with the goal of protecting the privacy of third-parties who may have been incidentally captured.

The full details of the algorithm and blurring procedure are available on the [Motivation-and-Behaviour/faceblurring](https://github.com/Motivation-and-Behaviour/faceblurring) repo.

### Image Review

After face blurring, participants are invited to review the images captured.
They do this by watching a timelapse video of the images, with an ID number shown for each image.
Participants indicate on a spreadsheet any images they wish to have deleted, and these are automatically deleted from the dataset.
All of this occurs before anyone on the research team views any of the images, with the goal that participants will remove any images that they feel are too personal.
Participants have to review the images while someone from the research team is present to prevent them from making copies of the images (to further protect third-party privacy).

## Required Additional Reading

Please also read [Ethical Framework for Wearable Camera Research](https://doi.org/10.1016/j.amepre.2012.11.006) by Kelly et al, which is the basis for our ethical guidelines.

## Optional Additional Reading

These documents might answer other questions you have about the ethics of the research, or how we created our guidelines:

* [Australian Catholic University Research Code of Conduct](https://policies.acu.edu.au/736355)
* 