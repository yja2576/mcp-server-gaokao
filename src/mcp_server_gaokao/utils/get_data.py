import json
import random
from pydantic import BaseModel
from importlib.resources import files


class Major(BaseModel):
    id: str


# -------------------------------------------------------获得标准的专业名称-------------------------------------------------------
file_path_major = str(files("mcp_server_gaokao.data") / "all_major.json")
with open(file_path_major, "r", encoding="utf-8") as f:
    all_major = json.load(f)


def get_major(major_name: str, major_level: str) -> Major:
    level_map = {"本科": "1", "专科": "2"}
    level1 = level_map.get(major_level, "0")
    filtered_majors = [major for major in all_major if major["level1"] == level1]
    for major in filtered_majors:
        if major_name in major["name"]:
            return Major(id=major["special_id"])
    for major in filtered_majors:
        if major_name in major["level3_name"]:
            return Major(id=major["special_id"])
    raise ValueError(f'Invalid "major_name": "{major_name}". When major level is {major_level}, the major does not exist.')


# -------------------------------------------------------获得随机请求头-------------------------------------------------------
file_path_headers = str(files("mcp_server_gaokao.data") / "all_headers.json")
with open(file_path_headers, "r", encoding="utf-8") as f:
    all_headers = json.load(f)


def get_headers() -> dict:
    headers = random.choice(all_headers)
    return headers
