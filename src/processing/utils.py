def generate_filepaths(
    ids: list,
    timepoint=0,
    prefix="/mnt/MBData/Square_Eyes_DP20_Data/Participant_Data/Main Study/Community Sample",
    suffix="Images",
) -> list[str]:
    """Generate a list of filepaths from a list of participant IDs

    Parameters
    ----------
    ids : list
        The list of participant IDs
    timepoint : int, optional
        The timepoint for the file path, where 0 = Baseline, 1 = Time 1, and 2 = Time 2. By default 0
    prefix : str, optional
        The start of the filepath, by default "/mnt/MBData/Square_Eyes_DP20_Data/Participant_Data/Main Study/Community Sample"
    suffix : str, optional
        The end of the filepath, by default "Images"

    Returns
    -------
    list[str]
        The returned filepaths
    """
    out_list = []
    timepoints = ["Baseline", "Time_1", "Time_2"]
    time_str = timepoints[timepoint]

    for id in ids:
        out_list.append(f"{prefix}/{id}/{time_str}/{suffix}")

    return out_list
