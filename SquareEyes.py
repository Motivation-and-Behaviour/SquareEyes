import argparse
import configparser

from src.processing.process import process_folders
from src.processing.utils import generate_filepaths


def main():
    parser = argparse.ArgumentParser(
        description="Use the SquareEyes model to process folders"
    )

    group = parser.add_argument_group(
        "Processing options",
        "You must provide one of --folders or --ids",
    )
    exclusive_group = group.add_mutually_exclusive_group(required=True)

    exclusive_group.add_argument(
        "-f", "--folders", required=False, nargs="+", help="Folders to process"
    )
    exclusive_group.add_argument(
        "-i", "--ids", required=False, nargs="+", help="Participant IDs to process"
    )

    group.add_argument(
        "-t",
        "--timepoint",
        required=False,
        choices=range(0, 3),
        type=int,
        default=0,
        help="Timepoint to process (only used with --ids)",
    )

    group.add_argument(
        "-o",
        "--overwrite",
        required=False,
        default=False,
        help="Overwrite existing files",
        action="store_true",
    )

    debug_group = parser.add_argument_group(
        "Debug and Testing", "These options are for debugging and testing purposes only"
    )
    debug_group.add_argument(
        "-e",
        "--env",
        choices=["DEFAULT", "TESTING"],
        default="DEFAULT",
        help="Environment to use",
    )

    args = parser.parse_args()

    # Further validation
    if args.timepoint and not args.ids:
        parser.error("--timepoint requires --ids to be provided as well.")

    # Load the configs
    config = configparser.ConfigParser()
    config.read("config.ini")
    configs = config[args.env]

    # Create the folder paths if needed
    if args.ids:
        print("Generating filepaths...")
        folders = generate_filepaths(
            args.ids, args.timepoint, configs["folder_prefix"], configs["folder_suffix"]
        )
    else:
        folders = args.folders

    # Process the folders
    print("Processing folders...")
    process_folders(folders, int(configs["n_back"]), args.overwrite)


if __name__ == "__main__":
    main()
