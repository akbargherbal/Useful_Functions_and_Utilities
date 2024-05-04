import os

def extract_text_with_paths(directory):
    output = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, directory)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                output.append(f"{file_path}:\n{content}\n")
            except UnicodeDecodeError:
                print(f"Unable to read file: {relative_path}")
    return "\n".join(output)

# Usage example
text_with_paths = extract_text_with_paths("./llama_factory_in_google_colab/")
print(text_with_paths)