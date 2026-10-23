# Overview

## Workflow Overview

The diagram below shows the full workflow for coding a participant's images, from assigning yourself on Asana through to marking the participant as complete.

```mermaid
flowchart TD
    subgraph prep ["Getting Ready"]
        direction TB
        A[Assign yourself to a<br>participant's images on Asana] --> B[Download the zipped images<br>from SharePoint]
        B --> C[Unzip the folder<br>for coding]
        C --> D[Set up Timelapse for<br>this set of images]
    end

    subgraph code ["Coding Images"]
        E[Code the images]
    end

    subgraph finish ["Finishing Up"]
        direction TB
        F[Upload the database file and<br>Backups folder to SharePoint]
        F --> G[Delete the unzipped <em>and</em><br>zipped image folders]
        G --> H[Mark the participant as<br>complete on Asana]
    end

    prep --> code --> finish
```

The rest of this section details how to do each of these steps.
