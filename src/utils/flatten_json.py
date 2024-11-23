"""
This module provides functionality to flatten a nested JSON object into a list of 
    (tag, data_type, value) triples.

Functions:
    flatten_json(json_obj):
        Flattens a nested JSON object into a list of (tag, data_type, value) triples.

        Args:
            json_obj (dict): The nested JSON object to flatten.

        Returns:
            list: A list of tuples, each containing a tag (str), data type (str), and value.
"""

import json
import logging
import sys


def flatten_json(json_obj: dict) -> list:
    """
    Flattens a nested JSON object into a list of (tag, data_type, value) triples.

    This function takes a nested JSON object and flattens it such that each element
    in the resulting list is a tuple containing the tag (key), the data type of the value,
    and the value itself. The tag is derived from the last key in the nested structure.

    Args:
        json_obj (dict): The nested JSON object to flatten.

    Returns:
        list: A list of tuples, each containing a tag (str), data type (str), and value.
    """
    my_name = "flatten_json"

    emsg = f"{my_name}: json_obj:\n\t{json_obj}"
    logging.debug(emsg)

    items = []  # List to store flattened data

    def recurse(obj: dict, current_key="") -> None:
        """recursively flatten the JSON object"""
        my_name = "flatten_json.recurse"
        emsg = f"{my_name}:\n\tcurrent_key = {current_key},\n\tobj = {obj}"
        logging.debug(emsg)

        if isinstance(obj, dict):
            for key, value in obj.items():
                recurse(value, key)
        elif isinstance(obj, list):
            data_type = "serialized list"
            serialized_obj = json.dumps(obj)
            emsg = (
                f"{my_name}: appending\n\t{current_key}, {data_type}, {serialized_obj}"
            )
            logging.debug(emsg)
            items.append((current_key, data_type, serialized_obj))
        else:
            data_type = type(obj).__name__
            emsg = f"{my_name}: appending\n\t{current_key}, {data_type}, {obj}"
            logging.debug(emsg)
            items.append((current_key, data_type, obj))

    emsg = f"{my_name}: json_obj:\n\t{json_obj}"
    logging.debug(emsg)

    items = []

    recurse(json_obj)
    emsg = f"{my_name}: returning:\n\t{items}"
    logging.debug(emsg)

    return items


def main():
    """
    Main function to read JSON input, flatten it, and print the flattened data.

    This function performs the following steps:
    1. Reads JSON data from standard input.
    2. Parses the JSON data.
    3. Flattens the JSON data into a list of (tag, data_type, value) triples.
    4. Prints each triple in the format: "tag (data_type): value".

    Note:
        The function expects the JSON input to be provided via standard input.

    Raises:
        JSONDecodeError: If the input is not valid JSON.
    """

    # Read JSON from standard input
    json_input = sys.stdin.read()
    data = json.loads(json_input)

    # Flatten the JSON data
    flattened_data = flatten_json(data)

    # Print the flattened (tag, data_type, value) triples
    logging.debug("Main: Flattened data:")
    for tag, data_type, value in flattened_data:
        emsg = f"\t{tag}: {data_type} = {value}"
        logging.debug(emsg)


if __name__ == "__main__":
    main()
