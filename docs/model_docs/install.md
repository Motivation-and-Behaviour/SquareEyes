# Install and Setup

## Prerequisites

This codebase was developed and tested on Ubuntu.
It should work on Windows and Mac, but it has not been tested and might require changes to the Conda environment.
It should also work on [WSL](https://learn.microsoft.com/en-us/windows/wsl/about), but again, it is untested.

The model should run on CPU, but it is recommended to run it on a GPU if you have one available.

Before you start you'll need to have the following installed on your system:

* Conda.
  You could install either [Anaconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
* [Git](https://git-scm.com/) (optional).
  You can download the codebase as a zip file, but it's easier to update if you have Git installed.
* GPU drivers.
  For most GPUs, this means installing [NVIDIA drivers](https://www.nvidia.com/Download/index.aspx), and the [CUDA toolkit](https://developer.nvidia.com/cuda-toolkit).
  This project was developed and tested on CUDA 11.8, and might support others in the future.

You'll also need some kind of IDE to interact with the code.
I like [VSCode](https://code.visualstudio.com/), but you could also use the tools that are bundled with Anaconda, or any other IDE you like.

## Install

### Clone the Repository

If you have Git installed, you can clone the repository with the following command:

```bash
git clone https://github.com/Motivation-and-Behaviour/SquareEyes.git
```

???+ tip
    Whenever you see a command you can run it in a linux terminal, or you could use Anaconda prompt on Windows.

If you didn't install git, you can download the codebase as a [zip file](https://github.com/Motivation-and-Behaviour/SquareEyes/archive/refs/heads/master.zip).
You'll then need to extract the zip file to a folder on your computer.

Regardless of which method you use, you should end up with a folder called `SquareEyes` on your machine.
You'll need to navigate to this folder (i.e., `cd SquareEyes`) before you can run any of the commands below.

### Create the Conda Environment

The next step is to create a Conda environment.
This will install all the dependencies you need to run the model.

```bash
conda env create -f environment.yml
```

This will take a while to run.
If you're running this on a system other than linux, this is the point I think it is most likely to fail.
If so, create a [bug report](https://github.com/Motivation-and-Behaviour/SquareEyes/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=) with the error message and we'll try to help you out.

Once the environment is created, you'll need to activate it:

```bash
conda activate square_eyes
```

Your prompt should now start with `(square_eyes)` to indicate that the environment is active.

## Test the Setup

The best way to test if everything is working correctly would be to run the example Jupyter notebook located at `notebooks/example.ipynb`.