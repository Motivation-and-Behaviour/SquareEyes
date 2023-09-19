from clearml import Dataset


def sync_dataset(ds_name, ds_path, new=False, tags=["Subsetted Existing"]):
    if new:
        parents = []
    else:
        ds = Dataset.get(dataset_project="Square Eyes", dataset_name=ds_name)
        parents = [ds.id]

    dataset = Dataset.create(
        dataset_project="Square Eyes",
        dataset_name=ds_name,
        dataset_tags=tags,
        output_uri="/mnt/MBData/Screen_Time_Measure_Development/clearml_endpoint",
        parent_datasets=parents,
    )

    # Have to remove all files first, otherwise we can duplicate them
    dataset.remove_files("*", recursive=True)

    dataset.add_files(
        path=ds_path,
        wildcard=["*.jpg", "*.txt", "*.JPEG"],
        recursive=True,
    )

    dataset.upload()
    dataset.finalize()


def create_combined_dataset(
    combined_name,
    incl_dataset=["coco", "ImageNet", "Objects365", "OpenImages"],
    tags=["Subsetted Existing", "Combined"],
):
    parent_ids = []
    for ds_name in incl_dataset:
        ds = Dataset.get(dataset_project="Square Eyes", dataset_name=ds_name)
        parent_ids.append(ds.id)

    dataset = Dataset.create(
        dataset_project="Square Eyes",
        dataset_name=combined_name,
        dataset_tags=tags,
        output_uri="/mnt/MBData/Screen_Time_Measure_Development/clearml_endpoint",
        parent_datasets=parent_ids,
    )

    dataset.finalize()


def fetch_clearml_dataset(ds_name):
    ds = Dataset.get(dataset_project="Square Eyes", dataset_name=ds_name)
    ds_folder = ds.get_mutable_local_copy("datasets/training_data", overwrite=True)
    return ds_folder
