from pathlib import Path
import os

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_dataset(uploaded_file, filename, mode="error"):
    file_path = DATA_DIR / filename

    if file_path.exists():
        if mode == "overwrite":
            uploaded_file.seek(0)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())
            return str(file_path)

        elif mode == "increment":
            file_path = increment_filename(file_path)
            uploaded_file.seek(0)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())
            return str(file_path)

        elif mode == "rename":
            raise ValueError("For 'rename' mode, call save_dataset() with the new filename explicitly.")

        else:
            raise FileExistsError(f"File '{filename}' already exists.")

    else:
        uploaded_file.seek(0)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        return str(file_path)


def increment_filename(path: Path):
    counter = 1
    new_path = path
    while new_path.exists():
        new_stem = f"{path.stem} ({counter})"
        new_path = path.with_name(new_stem + path.suffix)
        counter += 1
    return new_path

def delete_dataset(filename: str):
    file_path = DATA_DIR / filename
    if file_path.exists():
        file_path.unlink()
    else:
        raise FileNotFoundError(f"File '{filename}' not found.")

def rename_dataset(old_filename: str, new_filename: str):
    old_path = DATA_DIR / old_filename
    new_path = DATA_DIR / new_filename
    if not old_path.exists():
        raise FileNotFoundError(f"File '{old_filename}' not found.")
    if new_path.exists():
        raise FileExistsError(f"File '{new_filename}' already exists.")
    old_path.rename(new_path)

def file_size_limit(upload_file, max_mb: int = 10):
    size = len(upload_file.file.read())
    upload_file.file.seek(0)  # Reset cursor after reading
    if size > max_mb * 1024 * 1024:
        raise ValueError(f"File size exceeds {max_mb} MB limit.")


