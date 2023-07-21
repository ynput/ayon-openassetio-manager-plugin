# -*- coding: utf-8 -*-
"""Package to hold utility functions used in tests."""
import uuid
import hashlib
import random


def create_file_list(
        project_name: str, project_code: str, asset_name: str, product_name: str,
        version: int, ext: str, frame_start: int, frame_end: int) -> list[dict]:
    """Creates a list of file structures with the given project name and number of files

    Args:
        project_name: Name of the project to be used in file names.
        project_code: Code of the project to be used in file names.
        asset_name: Name of the asset to be used in file names.
        product_name: Name of the product to be used in file names.
        version: Version number to be used in file names.
        ext: Extension to be used in file names.
        frame_start: Start frame to use for the frame range.
        frame_end: End frame to use for the frame range.

    Returns:
        list: List of file structures.

    """
    files = []

    for frame in range(frame_start, frame_end):
        file_name = f"{project_code}_{asset_name}_{product_name}_v{version:03d}.{frame:04d}.{ext}"
        files.append({
            "id": uuid.uuid4().hex,
            "name": file_name,
            "path": f"{{root[work]}}/{project_name}/{asset_name}/publish/render/v{version:03d}/{file_name}",
            "size": random.randint(100000, 1000000),
            "hash": hashlib.md5(file_name.encode()).hexdigest(),
            "hashType": "md5"
        })
    return files
