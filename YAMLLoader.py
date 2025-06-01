from typing import Callable, Awaitable
from zonelogger import logger, LogZone
import yaml
import os
from typing import Any
from enums.roles import Roles
from enums.languages import Language
from core.handlerTypes import HandlerTypes
from models.nodesDict import NodesRootIDs

class YAMLLoader():
    def __init__(self, handlers: dict[HandlerTypes, dict[Language, dict[str, Callable[..., Awaitable[Any]]]]]):
        self._handlers = handlers
        self._id_counter = 1 #для разделения работы ref

    def _get_next_node_id(self):
        id = self._id_counter
        self._id_counter += 1
        return id

    def load_folder(self, folder_path, lang: Language) ->NodesRootIDs:
        ref_ids = {}
        dialog_nodes = {}
        root_nodesIds: dict[Roles, int] = {}
        root_path = os.path.abspath(os.path.dirname(__file__))
        target_path = os.path.join(root_path, folder_path)

        for dirpath, _, filenames in os.walk(target_path):
            for file in filenames:
                if file.endswith(('.YAML', '.yaml')):
                    full_path = os.path.join(dirpath, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            root_node_id = self._get_next_node_id()
                            file_role = 0
                            match os.path.splitext(file)[0]:
                                case "admin":
                                    file_role = Roles.ADMIN
                                case "user":
                                    file_role = Roles.USER
                                case "support":
                                    file_role = Roles.SUPPORT
                                case "banned":
                                    file_role = Roles.BANNED
                                case "global":
                                    file_role = Roles.GLOBAL
                            root_nodesIds[file_role] = root_node_id
                            self._make_node(root_node_id, data, file_role, lang, dialog_nodes, ref_ids)
                    except Exception as e:
                        logger.error(LogZone.YAML,f"cant load file {full_path}: {e}")
        for node_id, node in dialog_nodes.items():
            if "ref" in node:
                ref = node["ref"]
                if isinstance(ref, str):
                    ref_node_id = ref_ids[ref]
                    if ref_node_id:
                        node["ref"] = ref_node_id
                    else:
                        logger.error(LogZone.YAML,f"ref was missed for {node_id} node")

        logger.debug(LogZone.YAML, "all nodes")
        for node_id, node in dialog_nodes.items():
            logger.debug(LogZone.YAML, f"{node_id}: {node}")
        logger.debug(LogZone.YAML, "ref id dict")
        for node_id, node in ref_ids.items():
            logger.debug(LogZone.YAML, f"{node_id}: {node}")

        return {"nodes": dialog_nodes, "roots": root_nodesIds}

    def _make_node(self, node_id, node_data, file_role: Roles, lang, dialog_nodes, ref_ids: dict[str,int]):
        if node_data:
            node = {"role":file_role}
            for key, value in node_data.items():
                match key:
                    case "triggers":
                        node["triggers"] = {}
                        for trigger in value:
                            [(in_keys, in_value)] = trigger.items()
                            in_node_id = self._get_next_node_id()
                            self._make_node(in_node_id,in_value, file_role, lang,  dialog_nodes, ref_ids)
                            in_keys_list = [k.strip() for k in in_keys.split(';')]
                            for in_key in in_keys_list:
                                node["triggers"][in_key] = in_node_id
                    case "cmd_triggers":
                        node["cmd_triggers"] = {}
                        for cmd_trigger in value:
                            [(in_keys, in_value)] = cmd_trigger.items()
                            in_node_id = self._get_next_node_id()
                            self._make_node(in_node_id,in_value, file_role, lang, dialog_nodes, ref_ids)
                            in_keys_list = [k.strip() for k in in_keys.split(';')]
                            for in_key in in_keys_list:
                                node["cmd_triggers"][in_key] = in_node_id
                    case "cmd_id":
                        handler = self._handlers.get(HandlerTypes.CMD, {}).get(lang, {}).get(value)
                        if handler:
                            node["cmd_handler"] = handler
                        else:
                            logger.warning(LogZone.YAML, f"cmd_handler '{value}' was missed for {node_id} node in {lang}")
                    case "cmd_exit_id":
                        handler = self._handlers.get(HandlerTypes.CMD_EXIT, {}).get(lang, {}).get(value)
                        if handler:
                            node["cmd_exit_handler"] = handler
                        else:
                            logger.warning(LogZone.YAML, f"cmd_handler '{value}' was missed for {node_id} node in {lang}")
                    case "answer_id":
                        handler = self._handlers.get(HandlerTypes.ANSWER, {}).get(lang, {}).get(value)
                        if handler:
                            node["answer_handler"] = handler
                        else:
                            logger.warning(LogZone.YAML, f"answer_handler '{value}' was missed for {node_id} node in {lang}")
                    case "message_preprocess_id":
                        handler = self._handlers.get(HandlerTypes.MESSAGE_PREPROCESS, {}).get(lang, {}).get(value)
                        if handler:
                            node["message_preprocess_handler"] = handler
                        else:
                            logger.warning(LogZone.YAML, f"message_preprocess_handler '{value}' was missed for {node_id} node in {lang}")
                    case "freeInput_id":
                        handler = self._handlers.get(HandlerTypes.FREE_INPUT, {}).get(lang, {}).get(value)
                        if handler:
                            node["freeInput_handler"] = handler
                        else:
                            logger.warning(LogZone.YAML, f"freeInput_handler '{value}' was missed for {node_id} node in {lang}")
                    case "ref_id":
                        ref_ids[value] = node_id
                    case default:
                        node[key] = value
            dialog_nodes[node_id] = node