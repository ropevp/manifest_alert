# Deploying the Manifest Alerts Solution to Another PC

This guide explains how to move and run the Manifest Alerts solution on a different Windows PC using Python and a virtual environment (venv).

## 1. Prerequisites
- Windows 10/11 PC
- Python 3.8 or newer (matching your current version)
- (Optional) Git, if you want to clone from a repository

## 2. Copy the Project
- Copy the entire `manifest_alerts` folder (including all subfolders and files) to the new PC. You can use a USB drive, network share, or a zip file.

## 3. Install Python
- Download Python from https://www.python.org/downloads/
- During installation, check **Add Python to PATH**.
- Verify installation by running in Command Prompt:
  ```
  python --version
  ```

## 4. Create a Virtual Environment
Open Command Prompt or PowerShell in the `manifest_alerts` folder:

```
python -m venv venv
```

This creates a `venv` folder with an isolated Python environment.

## 5. Activate the Virtual Environment
- **Command Prompt:**
  ```
  venv\Scripts\activate
  ```
- **PowerShell:**
  ```
  .\venv\Scripts\Activate.ps1
  ```

You should see `(venv)` at the start of your prompt.

## 6. Install Dependencies
Run:
```
pip install -r requirements.txt
```

## 7. Run the Application
Still in the activated venv, run:
```
python main.py
```

## 8. (Optional) Create a Shortcut
- You can create a shortcut to `python main.py` (with venv activated) for easier launching.

## 9. Notes
- If you change the Python version, re-create the venv and reinstall requirements.
- If you add new dependencies, update `requirements.txt` and repeat step 6 on the new PC.
- All config and log files are stored in the project folder.

---

For any issues, check the README or contact your developer.
