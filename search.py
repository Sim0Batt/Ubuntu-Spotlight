import os

class SearchInFiles():
    def __init__(self):
        pass

    def search_files(search_text):
        matching_files = {}
        if search_text != "":
            count = 0  # Counter to limit results
            for root, dirs, files in os.walk("/home/simone/"):  # Search from the root directory
                for file in files:
                    if search_text in file:
                        matching_files[file] = os.path.join(root, file)
                        count += 1
                        if count >= 10:  # Stop after 10 results
                            return matching_files
        return matching_files  # Always return a dictionary

    def open_file(file_path):
        os.system(f'code "{file_path}"')