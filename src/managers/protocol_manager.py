"""protocol_manager.py
Protocol Manager to handle RTL_433 protocols
"""

from typing import Tuple, Union

from src.managers.config_file_manager import ConfigurationFileManager

# ###################################################################### #
#                      ProtocolManager Class
# ###################################################################### #


class ProtocolManager:
    """Protocol Manager to handle RTL_433 protocols"""

    def __init__(
        self,
        config_dir: str = "./config",
        protocols_file: str = "rtl_433_protocols.json",
        categories_file: str = "protocol_categories.json",
    ):
        self.protocols_manager = ConfigurationFileManager(
            config_file=protocols_file,
            config_dir=config_dir,
            check_interval=60,
        )
        self.categories_manager = ConfigurationFileManager(
            config_file=categories_file,
            config_dir=config_dir,
            check_interval=60,
        )

    # ############################ _load_iconfigurations ############################ #

    def _load_configurations(self) -> None:
        """Load configurations if files have been modified"""
        self.protocols = self.protocols_manager._load_configuration()
        self.categories = self.categories_manager._load_configuration()

    # ############################ get_protocl_info ############################ #

    def protocol_name(self, protocol_id: str) -> str:
        """Get the protocol name for a protocol ID"""
        self._load_configurations()
        protocol_info = self.protocols.get(protocol_id, {})
        if not protocol_info:
            raise ValueError(
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                f"protocol_name: Protocol ID {protocol_id} not found"
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            )

        return protocol_info.get("name", "*UNK_PROTOCL_NAME*")

    def protocol_description(self, protocol_id: str) -> str:
        """Get the protocol description for a protocol ID"""
        self._load_configurations()
        protocol_info = self.protocols.get(protocol_id, {})
        if not protocol_info:
            raise ValueError(
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                f"protocol_description: Protocol ID \\{protocol_id}\\ not found"
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            )

        return protocol_info.get("description", "*UNK_PROTOCL_DESC*")

    # ############################ protocol_info ############################ #
    # returns either a Tuple of type [str, str] or a Tuple of type [None, None]
    def protocol_info(
        self, protocol_id: str
    ) -> Union[Tuple[str, str], Tuple[None, None]]:
        """Get the protocol information for a protocol ID"""
        self._load_configurations()
        protocol_info = self.protocols.get(protocol_id, {})
        if not protocol_info:
            return None, None
            # raise ValueError(
            #     f"protocol_info: Protocol ID \\{protocol_id}\\ not found"
            # )

        protocol_name = protocol_info.get("name", "*UNK_PROTOCL_NAME*")
        protocol_description = protocol_info.get(
            "protocol_description", "*UNK_PROTOCL_DESC*"
        )

        return (protocol_name, protocol_description)

    # ############################ is_weather_sensor ############################ #

    def is_weather_sensor(self, protocol_id: str) -> bool:
        """Check if protocol ID is for a weather sensor"""
        self._load_configurations()
        return protocol_id in self.categories.get(
            "weather_sensor_protocol_ids", []
        )

    # ############################ is_unk_weather_sensor ############################ #

    def is_unk_weather_sensor(self, protocol_id: str) -> bool:
        """Check if protocol ID is for a pressure sensor"""
        self._load_configurations()
        return protocol_id in self.categories.get("pressure_sensors", [])

    # ############################ is_pressure_sensor ############################ #

    def is_pressure_sensor(self, protocol_id: str) -> bool:
        """Check if protocol ID is for a pressure sensor"""
        self._load_configurations()
        return protocol_id in self.categories.get(
            "pressure_sensor_protocol_ids", []
        )
