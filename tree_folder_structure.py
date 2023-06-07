import os
import treelib
import regex as re

IGNORE_PLACEHOLDER = "..."  # Placeholder text for ignored folders


def add_node(tree, parent, path, ignore_folders, counter):
    """
    Recursively adds nodes to the tree for each file and folder in the given path.

    Args:
        tree (treelib.Tree): The tree object.
        parent (str): Identifier of the parent node.
        path (str): Path of the current node.
        ignore_folders (set): Set of folder names to ignore.
        counter (int): Counter to generate unique identifiers for nodes.
    """
    node_id = os.path.basename(path)
    if node_id in ignore_folders:
        parent_id = parent if parent != "HEAD" else None
        tree.create_node(IGNORE_PLACEHOLDER, f"{node_id}_{counter}", parent=parent_id)
        return
    unique_id = f"{node_id}_{counter}"
    while unique_id in tree:
        counter += 1
        unique_id = f"{node_id}_{counter}"
    node = tree.create_node(unique_id, unique_id, parent=parent)
    if os.path.isdir(path):
        try:
            for filename in os.listdir(path):
                counter += 1
                add_node(tree, node.identifier, os.path.join(path, filename), ignore_folders, counter)
        except PermissionError:
            # Handle permission denied error for certain folders
            pass


def main():
    """
    Main function to build the tree structure of a folder.
    """
    print("Please provide the path to the folder.")
    print("For a relative path, make sure the script is in the same directory as the folder.")
    print("For an absolute path, provide the full path to the folder.")

    path = input("Enter folder path: ")
    ignore = input("Enter a comma-separated list of folders to ignore: ")
    ignore_folders = set(ignore.split(","))
    counter = 1  # Start counter at 1

    tree = treelib.Tree()
    tree.create_node("HEAD", "HEAD")
    try:
        add_node(tree, "HEAD", path, ignore_folders, counter)  # Pass the counter argument
    except FileNotFoundError:
        print("Folder path not found.")
        return
    except NotADirectoryError:
        print("Invalid folder path.")
        return

    filename = path + "_tree.txt"
    try:
        tree.save2file(filename)

        with open(filename, "r", encoding='utf-8') as f:
            contents = f.read()
            contents = re.sub(r'_\d+\n', r'\n', contents)
        
        with open(filename, "w", encoding='utf-8') as f:
            f.write(contents)



        print("Tree saved to", filename)
    except PermissionError:
        print("Permission denied. Unable to save the tree structure.")

if __name__ == "__main__":
    main()
