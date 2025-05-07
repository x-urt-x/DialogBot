from zonelogger import logger, LogZone
import yaml
import os
from dataclasses import dataclass, field
from dialog_node_handlers_manager import handler_registry
from typing import Any

class YAMLLoader:
    def __init__(self):
        self.id_counter = 1 #для разделения работы ref
        self.ref_id_dict = {}
        self.dialog_nodes = {}

    def _get_next_node_id(self):
        id = self.id_counter
        self.id_counter += 1
        return id

    def load_folder(self, folder_path):
        root_path = os.path.abspath(os.path.dirname(__file__))
        target_path = os.path.join(root_path, folder_path)

        for dirpath, _, filenames in os.walk(target_path):
            for file in filenames:
                if file.endswith(('.YAML', '.yaml')):
                    full_path = os.path.join(dirpath, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            self._make_node(self._get_next_node_id(), data)
                    except Exception as e:
                        logger.error(LogZone.YAML,f"cant load file {full_path}: {e}")
        for node_id, node in self.dialog_nodes.items():
            if "ref" in node:
                ref = node["ref"]
                if isinstance(ref, str):
                    ref_node_id = self.ref_id_dict[ref]
                    if ref_node_id:
                        node["ref"] = ref_node_id
                    else:
                        logger.error(LogZone.YAML,f"ref was missed for {node_id} node")

        logger.debug(LogZone.YAML, "all nodes")
        for node_id, node in self.dialog_nodes.items():
            logger.debug(LogZone.YAML, f"{node_id}: {node}")
        logger.debug(LogZone.YAML, "ref id dict")
        for node_id, node in self.ref_id_dict.items():
            logger.debug(LogZone.YAML, f"{node_id}: {node}")

    def _make_node(self, node_id, node_data):
        if node_data:
            node = {}
            for key, value in node_data.items():
                match key:
                    case "triggers":
                        node["triggers"] = {}
                        for trigger in value:
                            [(in_keys, in_value)] = trigger.items()
                            in_node_id = self._get_next_node_id()
                            self._make_node(in_node_id,in_value)
                            in_keys_list = [k.strip() for k in in_keys.split(';')]
                            for in_key in in_keys_list:
                                node["triggers"][in_key] = in_node_id
                    case "cmd_triggers":
                        node["cmd_triggers"] = {}
                        for cmd_trigger in value:
                            [(in_keys, in_value)] = cmd_trigger.items()
                            in_node_id = self._get_next_node_id()
                            self._make_node(in_node_id,in_value)
                            in_keys_list = [k.strip() for k in in_keys.split(';')]
                            for in_key in in_keys_list:
                                node["cmd_triggers"][in_key] = in_node_id
                    case "cmd_id":
                        if value in handler_registry:
                            node["cmd_handler"] = handler_registry[value]
                        else:
                            logger.warning(LogZone.YAML,f"cmd_handler was missed for {node_id} node")
                    case "freeInput_id":
                        if value in handler_registry:
                            node["freeInput_handler"] = handler_registry[value]
                        else:
                            logger.warning(LogZone.YAML,f"freeInput_handler was missed for {node_id} node")
                    case "ref_id":
                        self.ref_id_dict[value] = node_id
                    case default:
                        node[key] = value
            self.dialog_nodes[node_id] = node

@dataclass
class Dialog_Node:
    id : int
    fields: dict[str, Any] = field(default_factory=dict)
