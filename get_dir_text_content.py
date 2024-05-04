import os

def extract_text_with_paths(directory):
    output = []
    for root, dirs, files in os.walk(directory):
        # Exclude the '.get' folder from traversing
        if '.git' in dirs:
            dirs.remove('.git')
        for file in files:
            file_path = os.path.join(root, file).replace('\\', '/')
            relative_path = os.path.relpath(file_path, directory)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                output.append(f"{file_path}:\n{content}\n")
            except UnicodeDecodeError:
                print(f"Unable to read file: {relative_path}")
    return "\n".join(output)

# Usage example
# get folder name:
folder = input("Enter the folder name: ")



text_with_paths = extract_text_with_paths(folder)

with open("text_with_paths.txt", "w", encoding="utf-8") as f:
    f.write(text_with_paths)
