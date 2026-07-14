# Changelog

## Square Eyes Coding Manual

### Major Update <small>14th June 2024</small>

Our change from the network drive to SharePoint, and a series of changes in the newer versions of the Timelapse software, has meant a bunch of changes were needed to the coding manual.

#### Changes from transition to SharePoint

- Updated all of the references to the network drive to now point to the new SharePoint site.
- Replaced the previous instructions about 'making a local cache' with instructions on how to [download a zip of the files](coding_workflow/setup.md#step-2-download-the-participant-data)
  This is the new workflow to be followed.
- Also included instructions on how to use [7-Zip to extract the folder](coding_workflow/setup.md#step-3-unzip-the-downloaded-folder).
  The built-in Windows extraction tool does not always work with large zip folders from SharePoint.

#### Changes from updates to Timelapse

- Added instructions for [sorting the images before coding](coding_workflow/setup.md#44-set-the-image-order).
  The new versions of Timelapse do not sort the images by filename by default.
  While they would normally use the datetime, if the datetime are missing they are replaced with a placeholder (`9999-12-31 23:59:59`) which puts them at the bottom.
  Sorting by filename resolves this issue.

#### Other changes

- Restructured the instructions to hopefully be clearer to new coders.
- Added explicit instructions for [assigning on Asana](coding_workflow/setup.md#step-1-assign-yourself-to-images-in-asana), and [marking complete](coding_workflow/finish.md#step-3-mark-the-timepoint-as-complete-in-asana) when done.
  This was previously discussed with the team, but not codified.
- Updated the [checklist](checklist.md) to reflect all of the other changes.
- Added a new [overview of the process](coding_workflow/index.md#workflow-overview) as a diagram.
- Fixed a bunch of typos

#### Changes not made

- Some changes to Timelapse have slightly changed the names for the menu items.
  These still seem clear enough, but could be updated later.
- The videos and most screenshots have not been updated, only because this is too time consuming.
  Again, the existing screenshots are mostly clear enough.
