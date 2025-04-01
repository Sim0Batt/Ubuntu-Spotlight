# Spotlight Clone

Spotlight Clone is a Python-based desktop search application inspired by macOS Spotlight. It allows users to search for files, directories, and applications on their system with a clean and intuitive graphical interface built using GTK.

## Features

- **File Search**: Quickly search for files on your system.
- **Directory Search**: Locate directories by name.
- **Application Search**: Search and launch applications with predefined commands.
- **Dynamic UI**: Displays search results dynamically as you type.
- **Custom Icons**: Displays file type and application-specific icons for better visual identification.
- **Keyboard Shortcuts**: 
  - Press `Escape` to close the application.
  - Use the `Enter` key to run the first app result.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Sim0Batt/Ubuntu-Spotlight
   cd spotlight
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have the following installed on your system:
   - Python 3.12 or higher
   - GTK 3
   - Cairo
   - Nautilus (for opening directories)
   - GNOME Terminal

4. Run the application:
   ```bash
   python app.py
   ```

## File Structure

```
spotlight/
├── app.py                # Main application file
├── search.py             # Search logic for files, directories, and applications
├── test.py               # Test script for launching a directory
├── assets/               # Assets folder containing icons and styles
    ├── styles.css        # CSS file for styling the application
    ├── app_icons/        # Icons for applications
    └── file_icons/       # Icons for file types
```

## Usage

1. Launch the application by running `python app.py`.
2. Type your search query in the search bar.
3. Results will be displayed in three categories:
   - **Files**
   - **Directories**
   - **Applications**
4. Click on a result to open the file, directory, or application.

## Customization

- **Application Commands**: Modify the `application_list` dictionary in [`search.py`](search.py) to add or update application commands.
- **Icons**: Add or replace icons in the `assets/app_icons/` and `assets/file_icons/` directories.
- **Styling**: Update the CSS styles in [`assets/styles.css`](assets/styles.css) to customize the appearance of the application.

## Known Limitations

- Replace the all the strings `user_name` into the code with the user of your laptop.
- Only the first 10 results are displayed for files and directories.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the application.
