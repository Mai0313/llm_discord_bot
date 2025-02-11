# Installation

This page will guide you through the installation process this project.

## Install Dependency Management Tool

=== "uv"

    Install [uv](https://docs.astral.sh/uv/)

    ```bash
    make uv-install
    ```

=== "Rye"

    Install [Rye](https://rye.astral.sh/guide/installation/)

    ```bash
    make rye-install
    ```

=== "Conda"

    - Please visit [miniconda](https://docs.anaconda.com/miniconda/install/) to install miniconda.

    ```bash
    conda create -n plotly python=3.9 -y
    conda activate plotly
    pip install uv
    ```

=== "PIP"

    - Please visit [Python](https://www.python.org/downloads/) to install Python for using pip.

    ```bash
    pip install uv
    ```

## Export Proxy (Optional)

=== "uv"

    ```bash
    export https_proxy=http://mtkdrone01.mediatek.inc:23984
    ```

=== "Rye"

    ```bash
    export https_proxy=http://mtkdrone01.mediatek.inc:23984
    ```

=== "Conda"

    ```bash
    export https_proxy=http://mtkdrone01.mediatek.inc:23984
    ```

=== "PIP"

    ```bash
    export https_proxy=http://mtkdrone01.mediatek.inc:23984
    ```

## Install/Setup Dependencies

=== "uv"

    ```bash
    uv sync
    ```

=== "Rye"

    ```bash
    rye sync
    ```

=== "Conda"

    ```bash
    uv pip sync pyproject.toml
    ```

=== "PIP"

    ```bash
    uv pip sync pyproject.toml
    ```

- Once you have done the above steps, you can run the following commands to start the application.
- If your environment is messed up, you can run `uv sync` again to fix it.
