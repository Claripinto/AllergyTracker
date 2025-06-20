# Allergy Tracker Web Application

## 1. Overview
A web application built with Python and Flask to manage an inventory of allergenic extracts.
Core features include adding, viewing, editing, and deleting extracts, as well as tracking stock levels and monitoring expiry dates, all through an intuitive web interface.

## 2. Prerequisites
-   Python 3.x installed on your system.
-   Pip (Python package installer), which usually comes with Python.
-   Git for cloning the repository (recommended).
-   Required Python packages are listed in `requirements.txt` (primarily Flask).

## 3. Setup
1.  **Clone the Repository:**
    Open your terminal or command prompt and run:
    ```bash
    git clone <repository_url>  # Replace <repository_url> with the actual URL
    cd AllergyTracker          # Or your chosen directory name
    ```
    If you downloaded the files as a ZIP, extract them to a directory.

2.  **Install Dependencies:**
    Navigate to the project directory in your terminal and install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Database Initialization:**
    The SQLite database (`allergy_tracker.db`) and its necessary table (`allergenic_extracts`) will be created automatically when you first run the web application (`python app.py`).
    Alternatively, you can initialize the database manually beforehand by running:
    ```bash
    python database_setup.py
    ```

## 4. Running the Web Application
1.  Ensure you are in the project's root directory in your terminal.
2.  Execute the following command to start the Flask development server:
    ```bash
    python app.py
    ```
3.  Once the server is running (you should see output like `* Running on http://127.0.0.1:5001/`), open your web browser and navigate to:
    `http://127.0.0.1:5001/`
    (Note: The default port in the current `app.py` is 5001. If you see 5000 in Flask's output, use that.)

## 5. Using the Web Interface
-   **Main Page (Home):**
    -   Displays a table listing all allergenic extracts in the inventory.
    -   Each row shows key details and provides actions for each extract.

-   **Adding a New Extract:**
    -   Click the "Add New Extract" button located above the table on the main page.
    -   Fill in the form with the extract's details (Name and Quantity are mandatory).
    -   Click "Create Extract" to save.

-   **Editing an Extract:**
    -   On the main page, click the "Edit" button next to the extract you wish to modify.
    -   The form will be pre-filled with the current details. Make your changes and click "Update Extract".

-   **Deleting an Extract:**
    -   On the main page, click the "Delete" button next to the extract.
    -   A confirmation prompt will appear in your browser. Click "OK" to confirm deletion.

-   **Updating Stock Quantity:**
    -   On the main page, each extract row has a small input field for quantity and an "Update Qty" button.
    -   Enter the amount by which you want to change the stock (e.g., `20` to add 20 units, `-5` to remove 5 units).
    -   Click "Update Qty". The page will refresh with the updated quantity and a confirmation message.

-   **Reports:**
    -   In the navigation bar at the top of the page, click the "Reports" dropdown.
    -   **Nearing Expiry:** Select this to view extracts that are close to their expiry date. You can enter a custom "Days Threshold" (default is 30 days) and click "View Report".
    -   **Low Stock:** Select this to view extracts that are low in stock. You can enter a custom "Quantity Threshold" (default is 10 units) and click "View Report".

## 6. Database
-   The application uses an SQLite database, which is a single-file, serverless database engine.
-   All data is stored in a file named `allergy_tracker.db`, located in the project's root directory.
-   **Caution:** It's generally not recommended to manually edit the `allergy_tracker.db` file directly, as this could lead to data corruption. The web application provides all necessary functions to manage the inventory data safely.

## 7. Unit Tests (For Developers)
The project includes unit tests for the backend database interaction logic found in `database_operations.py`.

-   **Test File:** `test_database_operations.py`
-   **Running Tests:**
    1.  Ensure you are in the application's root directory in your terminal.
    2.  The test script is configured to use a temporary database file (`test_allergy_tracker.db`) for its operations. This relies on global variables `DB_FILE` in `database_operations.py` and `SETUP_DB_FILE` in `database_setup.py` being accessible for the test script to override.
    3.  Execute the following command:
        ```bash
        python -m unittest test_database_operations.py -v
        ```
    This will run the tests in verbose mode, showing the status of each test case.

## 8. Command-Line Interface (CLI)
-   In addition to the web interface, a command-line interface (`cli.py`) is available for managing extracts.
-   This can be useful for scripting or if a graphical interface is not preferred.
-   To use the CLI, ensure the database is set up (as mentioned in Section 3) and run the following command from the project directory:
    ```bash
    python cli.py
    ```
    Follow the on-screen prompts to interact with the CLI menu.

## 9. Running with Docker

You can also build and run the Allergy Tracker web application using Docker. This provides a consistent environment for running the app.

### Prerequisites for Docker
- Docker installed on your system.

### Building the Docker Image
1.  Navigate to the root directory of the project (where the `Dockerfile` is located).
2.  Run the following command to build the Docker image. The `-t allergy-tracker` tag names the image `allergy-tracker`.
    ```bash
    docker build -t allergy-tracker .
    ```

### Running the Application using Docker
1.  Once the image is built, run the application in a Docker container using:
    ```bash
    docker run -p 5001:5000 allergy-tracker
    ```
2.  This command does the following:
    - `docker run`: Starts a new container.
    - `-p 5001:5000`: Maps port `5001` on your host machine to port `5000` inside the Docker container (where the Flask app is running). You can change `5001` to another available port on your host if needed.
    - `allergy-tracker`: Specifies the image to run.
3.  Open your web browser and go to: `http://localhost:5001/` (or whichever host port you used).

### Database Persistence with Docker
- **Important Note:** With the basic `docker run` command above, the `allergy_tracker.db` database file will be created *inside* the Docker container's `/app` directory. **If you remove the container, the database and all your data will be lost.**
- **For persistent storage:** You can use a Docker bind mount to save the database file to your host machine.
    1. Create a directory on your host machine where you want to store the database, for example:
       ```bash
       mkdir allergy_db_on_host
       ```
    2. When running the container, map this directory to the `/app` directory inside the container (where `allergy_tracker.db` is written):
       ```bash
       docker run -p 5001:5000 -v "$(pwd)/allergy_db_on_host:/app" allergy-tracker
       ```
       Now, the `allergy_tracker.db` file will be saved in the `allergy_db_on_host` directory on your computer.
    **Note:** This method mounts your host directory into `/app` in the container. Ensure your application code (copied via `COPY . .` in Dockerfile) does not conflict if this directory is not empty. For more advanced scenarios or if the application were to write to multiple locations, named volumes are often preferred.
