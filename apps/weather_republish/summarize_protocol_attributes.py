import json
import os
from typing import Dict

# DIRECTORY_IN = "./apps/weather_republish"
DIRECTORY_IN = "."
FILENAME_IN = "protocol_attributes.json"
FILEPATH_IN = f"{DIRECTORY_IN}/{FILENAME_IN}"


def load_protocol_data(filepath: str) -> Dict:
    """Load the protocol attributes JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def summarize_protocol(data: Dict) -> None:
    """Analyze and display protocol summaries."""
    # Sort protocols numerically
    protocols = sorted(data.keys(), key=lambda x: int(x))

    for protocol_id in protocols:
        protocol = data[protocol_id]
        attributes = protocol.get("attributes", {})

        print(f"\nProtocol {protocol_id}:")
        print("-" * 50)

        # Sort attributes alphabetically
        for attr_name in sorted(attributes.keys()):
            attr_data = attributes[attr_name]
            value_types = attr_data.get("value_types", [])
            values = attr_data.get("values", [])

            # Convert values to set to get unique entries
            unique_values = set(str(v) for v in values)

            print(f"\nAttribute: {attr_name}")
            print(f"Value types: {', '.join(value_types)}")

            # Display value summary based on type and count
            if len(unique_values) > 10:
                sample_values = list(unique_values)[:5]
                print(f"Values: {len(unique_values)} unique values")
                print(f"Sample values: {', '.join(sample_values)}...")
            else:
                print(f"Values: {', '.join(unique_values)}")

            # Show value ranges for numeric types
            if "float" in value_types or "int" in value_types:
                try:
                    numeric_values = [float(v) for v in values]
                    if numeric_values:
                        print(
                            f"Range: {min(numeric_values)} to {max(numeric_values)}"
                        )
                except (ValueError, TypeError):
                    pass


def main():
    full_path = os.path.abspath(FILEPATH_IN)
    print(f"\nLoading protocol data from:\n\t{full_path}\n")
    data = load_protocol_data(full_path)
    summarize_protocol(data)


if __name__ == "__main__":
    main()
