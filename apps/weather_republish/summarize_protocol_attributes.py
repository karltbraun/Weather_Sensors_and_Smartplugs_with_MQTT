import json
import os
from collections import defaultdict
from typing import Dict, Set

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

    print("List of all protocols:")
    print(f"\t{protocols}")

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


def analyze_common_attributes(data: Dict) -> None:
    """Analyze which attributes are shared across protocols."""
    # Create mappings for analysis
    attr_to_protocols = defaultdict(set)
    protocol_groups = defaultdict(list)

    # Build mapping of attributes to protocols that have them
    for protocol_id in data:
        attributes = set(data[protocol_id].get("attributes", {}).keys())
        attr_set = frozenset(attributes)
        protocol_groups[attr_set].append(protocol_id)
        for attr in attributes:
            attr_to_protocols[attr].add(protocol_id)

    print("\nProtocol Attribute Analysis:")
    print("=" * 50)

    # 1. Show total number of unique protocols
    all_protocols = sorted(data.keys(), key=int)
    print(f"\nTotal number of protocols: {len(all_protocols)}")
    print(f"Protocol IDs: {', '.join(all_protocols)}")

    # 2. Show attributes common to all protocols
    common_attrs = {
        attr
        for attr, protocols in attr_to_protocols.items()
        if len(protocols) == len(all_protocols)
    }
    print(f"\nAttributes common to ALL protocols ({len(common_attrs)}):")
    for attr in sorted(common_attrs):
        print(f"- {attr}")

    # 3. Show protocol groups with identical attribute sets
    print("\nProtocol groups with identical attribute sets:")
    for attr_set, protocols in protocol_groups.items():
        protocols = sorted(protocols, key=int)
        if len(protocols) > 1:
            print(
                f"\nThe following protocols share {len(attr_set)} attributes:"
            )
            print(f"Protocols: {', '.join(protocols)}")
            print("Shared attributes:")
            for attr in sorted(attr_set):
                print(f"- {attr}")

    # 4. Show unique attribute sets
    print("\nProtocols with unique attribute sets:")
    for attr_set, protocols in protocol_groups.items():
        if len(protocols) == 1:
            protocol = protocols[0]
            print(
                f"\nProtocol {protocol} has {len(attr_set)} unique attributes:"
            )
            for attr in sorted(attr_set):
                print(f"- {attr}")


def main():
    full_path = os.path.abspath(FILEPATH_IN)
    print(f"\nLoading protocol data from:\n\t{full_path}\n")
    data = load_protocol_data(full_path)
    summarize_protocol(data)
    analyze_common_attributes(data)


if __name__ == "__main__":
    main()
