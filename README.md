# NCBA-mp3

NCBA-mp3 downloads drum major competition audio files with a renaming function from a Google Sheet saved as a CSV, featuring a simple graphical user interface (GUI) for ease of use.

## Prerequisites
- Python >= 3.12.9 (Older versions may work, but this is recommended)
- Git (to clone the repository)

## Installation and Running

### Option 1: Using Setup Scripts (Recommended)
These scripts automatically install Python and Git if missing, clone the repository, and run the script.

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
   - Download from the repository releases or clone the repo manually.
2. **Make it Executable**:
   ```bash
   chmod +x MacOSLinux-run.sh

### Option 2: Manual Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/NephyMephy/NCBA-mp3.git