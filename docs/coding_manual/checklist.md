# Summary and Checklist

The below checklist is a summary of the steps to follow each time you start coding a participant.
You can use it as a reminder and to make sure nothing is missed.
Keep in mind that your progress on this checklist isn't saved.
You can take advantage of that to clear the checklist by refreshing the page.

## Create a Local folder on your PC

- [ ] Open the file explorer on your computer and click on This PC > Desktop.
- [ ] Right Click and select New > Folder.
      Rename this folder to “Square Eyes Data”.
- [ ] Enter this folder, and create a new folder for the participant data you will be coding.
      The label should match the four-digit participant data number (e.g., 0000).
- [ ] Click on the participant folder.
      Create a new folder, and rename it to “Images”.
      This folder will be used to store network files while coding each participant.

## Copy Participant Data Files from the Network folder into the Local Folder

- [ ] Open the network folder (This PC > M&B).
- [ ] Open the Square Eyes Data Folder (Square_Eyes_DP20_Data)
- [ ] Open the Participant Data Folder (Participant_Data)
- [ ] Select Main Study > Community Sample
- [ ] Select the participant folder that you are going to code (e.g., 0000)
- [ ] Select Baseline > Images.
- [ ] Select all files in this folder.
      Copy and paste into the “Images” folder you created for the corresponding participant in the local folder.

## Setup Timelapse

- [ ] Open Timelapse (Labeled Timelapse2).
- [ ] Select `File > Load Template, images and video files...`
- [ ] Select SquareEyes Template (TBD file) and open.
- [ ] Select `File > Import Data from a .csv file… > Image Data Import` and open.
- [ ] Select `Recognitions > Import image recognition data for this image set... > Square Eyes Detections.json` and open.
- [ ] Select Recognitions > Set bounding box options… > Change the slider to 0.3 and press Okay.

## To Create a QuickPaste

- [ ] Select `Edit > Show Quick Paste Window`.
- [ ] Fill in the QuickPaste options.
      Repeat as needed

## Pasting Files Back Onto the Network Folder

This must be done after you complete coding for each participant.

- [ ] Only paste the “SquareEyes Detections.ddb” and “Backups” folder back into the corresponding participant folder on the network folder.
      It should replace the existing files if they exist for this participant.
