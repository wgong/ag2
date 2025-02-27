# Website

This website is built using [Mintlify](https://mintlify.com/docs/quickstart), a modern website generator.

## How to get a notebook rendered on the website

See [here](https://github.com/ag2ai/ag2/blob/main/notebook/contributing.md#how-to-get-a-notebook-displayed-on-the-website) for instructions on how to get a notebook in the `notebook` directory rendered on the website.

## Build documentation locally

Follow these steps to build and serve the documentation on your local machine:

1. Install Node.js:
    - Download and install [Node.js](https://nodejs.org/en/download/)

2.  Install Quarto:
    - Visit the Quarto download [page](https://quarto.org/docs/download/).
    - Click on the Pre-release tab and download the latest version of Quarto.
    - Ensure you install version `1.5.23` or higher.

3. Install Required Python Packages:
    - From the project root directory, install the necessary Python packages by running:

    ```console
    pip install -e ".[docs]"
    ```

4. Build and Serve the Documentation:

    - To build and serve the documentation locally, run the following command from the project root directory:

        ```console
        ./scripts/docs_serve.sh
        ```

    - Optionally, you can pass the `--force` flag to clean up all temporary files and generate the documentation from scratch:

        ```console
        ./scripts/docs_serve.sh --force
        ```

    - The above command starts a local development server and opens up a browser window.

5. Handling Updates or Changes:

    - Whenever you update the documentation, stop the server and re-run the `./scripts/docs_serve.sh` command to serve the docs with the latest changes and view them live.

    - If deleted files are still displayed, it indicates cached or temporary files may be causing issues. To resolve this, use the `--force` flag to clean the build directory and regenerate the documentation.

By following these steps, you can build, serve, and update the documentation locally.

## Build with Dev Containers

To build and test documentation using Dev Containers, open the project using [VSCode](https://code.visualstudio.com/), press `Ctrl+Shift+P` and select `Dev Containers: Reopen in Container`.

This will open the project in a Dev Container with all the required dependencies installed.

Build and Serve the Documentation:

    - Open a terminal and run the following commands from the project root directory to build and serve the documentation:

        ```console
        pip install -e ".[docs]"
        ./scripts/docs_serve.sh
        ```

    - Optionally, you can pass the `--force` flag to clean up all temporary files and generate the documentation from scratch:

        ```console
        pip install -e ".[docs]"
        ./scripts/docs_serve.sh --force
        ```

    Once done you should be able to access the documentation at `http://localhost:3000/`.

Handling Updates or Changes:

    - Whenever you update the documentation, stop the server and re-run the `./scripts/docs_serve.sh` command to serve the docs with the latest changes and view them live.

    - If deleted files are still displayed, it indicates cached or temporary files may be causing issues. To resolve this, use the `--force` flag to clean the build directory and regenerate the documentation.
