import os
import sqlite3
import tempfile

import pandas as pd
from redcap import Project
from tqdm import tqdm


def search_files(root, extension):
    # Get the number of folders in the root folder
    toplevel = [
        folder
        for folder in os.listdir(root)
        if os.path.isdir(os.path.join(root, folder))
    ]

    usable_files = []
    exclude = set(["Backups", "Practice Data", "Accelerometer", "Cognitive", "images"])

    for folder in tqdm(toplevel, desc="Searching folders"):
        # Get the full path of the folder
        folder_path = os.path.join(root, folder)

        for dirpath, dirnames, filenames in os.walk(folder_path, topdown=True):
            if "Backups" not in dirpath and "Practice Data" not in dirpath:
                # Remove dirs we don't need to search
                dirnames[:] = [d for d in dirnames if d not in exclude]
                for filename in filenames:
                    if filename.endswith(extension):
                        usable_files.append(os.path.join(dirpath, filename))

    return usable_files


def clean_rows(row):
    # Fix rows that are likely mistakes
    for num in ["1", "2", "3"]:
        if (
            pd.notnull(row[f"Device{num}"])
            and pd.isnull(row[f"Content{num}"])
            and pd.isnull(row[f"Content{num}_Purpose"])
        ):
            row[f"Device{num}"] = pd.NA

    # Count the number of rows to make sure DeviceNum is plausible
    device_count = sum(pd.notnull(row[f"Device{i}"]) for i in ["1", "2", "3"])
    if pd.notnull(row["DeviceNum"]) and device_count < int(row["DeviceNum"]):
        if device_count == 0:
            row["DeviceNum"] = pd.NA
        else:
            row["DeviceNum"] = device_count

    # Fix columns that default to false
    if pd.isnull(row["Device1"]):
        for col in ["Content1_Violent", "Content2_Violent", "Content3_Violent"]:
            row[col] = pd.NA

    return row


def retrieve_data(file):
    conn = sqlite3.connect(file)
    cursor = conn.cursor()

    # Execute a query
    cursor.execute("SELECT * FROM DataTable")

    # Fetch all the rows
    rows = cursor.fetchall()

    # Create a pandas DataFrame from the query result
    df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return df


def find_and_upload(root, redcap_key):
    if not redcap_key:
        print("Could not find REDCap API key")
        return
    # Search for files to process
    files = search_files(root, "ddb")

    # Tidy up each file and upload to REDCap
    pbar = tqdm(files, desc="Uploading files")
    for file in pbar:
        pbar.set_description(f"Uploading file ({file})")
        # Extract the ID and timepoint
        participant_id = file.split("/")[7]
        timepoint_dict = {
            "Baseline": "baseline_visit_2_arm_1",
            "12m_visit_2_arm_1": "Time_1",
            "24m_visit_2_arm_1": "Time_2",
        }
        timepoint = timepoint_dict[file.split("/")[8]]

        # Extract the data from the file
        df = retrieve_data(file)

        # Clean the data
        cleaned_df = (
            df.replace("", pd.NA)
            .drop(
                [
                    "RelativePath",
                    "DeleteFlag",
                    "RequiresScreening",
                    "NonScreenIndicators",
                ],
                axis=1,
            )
            .apply(clean_rows, axis=1)
        )

        # Upload the data to REDCap
        api_url = "https://rdcap.acu.edu.au/api/"
        api_key = redcap_key
        project = Project(api_url, api_key)

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=True, suffix=".csv"
        ) as tmpfile:
            cleaned_df.to_csv(tmpfile.name, index=False)

            with open(tmpfile.name, "rb") as f:
                project.import_file(
                    record=participant_id,
                    field="camera_file",
                    event=timepoint,
                    file_object=f,
                    file_name=f"{participant_id}_{timepoint.split('_')[0]}.csv",
                )
        project.import_records(
            [
                {
                    "record_id": participant_id,
                    "redcap_event_name": timepoint,
                    "camera_data_complete": 2,
                }
            ]
        )
