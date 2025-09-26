from pydantic import BaseModel


def generate_param_schema(param_model_class: type[BaseModel]) -> dict:
    param_schema = param_model_class.model_json_schema()
    _clean_schema(param_schema)
    return param_schema


def _clean_schema(schema: dict):
    # 移除key为title并且value是字符串的字段
    keys_to_remove = []
    for key, value in schema.items():
        if (key == "title" and isinstance(value, str)):
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del schema[key]
    # 移动 type 字段到第一个位置
    if "type" in schema and isinstance(schema["type"], str):
        type_value = schema["type"]
        items_list = list(schema.items())
        schema.clear()
        schema["type"] = type_value
        schema.update(items_list)
    # 确保有 required 字段
    if "properties" in schema and "required" not in schema:
        schema["required"] = []
    # 递归处理嵌套字典
    for value in schema.values():
        if isinstance(value, dict):
            _clean_schema(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _clean_schema(item)
