# one-html-splitter

A simple utility to split large HTML files into smaller, more manageable parts.

## Features
- Split a single HTML file into multiple files based on user-defined criteria (e.g., number of lines, tags, or sections)
- Easy-to-use Python script (`splitter_app.py`)
- Standalone executable (`splitter_app.exe`) for users without Python installed

## Getting Started

### Requirements
- Python 3.x (if using the Python script)
- No installation required for the executable (`splitter_app.exe`)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/sugarypumpkin822/one-html-splitter.git
   cd one-html-splitter
   ```
2. **(Optional) Install dependencies:**
   If you plan to use the Python script, install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Using the Python Script
Run the script with Python:
```bash
python splitter_app.py --input yourfile.html --output output_folder [options]
```
- `--input`: Path to the input HTML file
- `--output`: Directory to save the split files
- Additional options may be available (see script help)

### Using the Executable
Simply double-click `splitter_app.exe` or run it from the command line:
```bash
splitter_app.exe --input yourfile.html --output output_folder [options]
```

## Example
```bash
python splitter_app.py --input largefile.html --output parts/
```
This will split `largefile.html` into smaller files saved in the `parts/` directory.

## File Structure
- `splitter_app.py` - Main Python script for splitting HTML files
- `splitter_app.exe` - Standalone executable version
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Contact
For questions or suggestions, open an issue on [GitHub](https://github.com/sugarypumpkin822/one-html-splitter). 
