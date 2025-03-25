# NCBA-mp3

NCBA-mp3 downloads drum major competition audio files with a renaming function a CSV formatted by NCBA, featuring a simple graphical user interface (GUI) for ease of use.

## Prerequisites
- Python >= 3.12.9 (Older versions may work, but this is recommended)
- Git (to clone the repository)

## Installation and Running

IMPORTANT: Rename the downloaded CSV to `schedule.csv` or else the script will not run.

### Option 1: Using Setup Scripts (Recommended)
These scripts automatically install Python and Git if missing, clone the repository, and run the script.
Note: Due to how the csv is setup from NCBA, Judge Names need to be manually inputted. An alternative name will still work with full functionality.

#### Windows
1. **Download `Windows-Run.bat`**:
   - Download from the repository releases or clone the repo manually.
2. **Run the Script**:
   - On `Windows-Run.bat`, Right-click and Select 'Run as Admisistrator' or run it in Command Prompt (preferably as Administrator for automatic installations).
   - If prompted, allow the script to install Python 3.12 and Git using `winget`.
3. **Prepare the CSV**:
   - Place `schedule.csv` (exported from your Google Sheet) in the `NCBA_mp3_downloader` directory created by the script.
4. **Follow GUI Instructions**

#### macOS/Linux
1. **Download `MacOSLinux-run.sh`**:
   - Download from the repository releases or clone the repo manually. Save to your Downloads folder
2. **Make it Executable**:
   ```bash
   cd Downloads/
   chmod +x MacOSLinux-run.sh
3. **Run the Bash Script**
   ```bash
   sudo bash ./MacOSLinux-run.sh

### Option 2: Manual Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/NephyMephy/NCBA-mp3.git