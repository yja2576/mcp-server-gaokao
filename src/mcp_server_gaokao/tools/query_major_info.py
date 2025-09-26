import json
from typing import Any, Literal

import requests
from pydantic import BaseModel, Field

from mcp_server_gaokao.tools.base import BaseTool, ToolResult
from mcp_server_gaokao.utils import generate_param_schema, get_headers, get_major


class QueryMajorInfoParameters(BaseModel):
    major_name: str = Field(
        ...,
        description="专业名称，请使用标准名称，不要使用简称。如果用户提供的是简称，并且该简称有多个对应的专业（例如：'自动化'就对应'电气工程及其自动化'和'机械设计制造及其自动化'两个专业），你要询问用户来确认是哪一个专业",
    )
    major_level: Literal["本科", "专科"] = Field(..., description="专业层次")


class QueryMajorInfo(BaseTool):
    name: str = "query_major_info"
    description: str = (
        "查询某个专业的信息，返回信息包括：类别、代码、男女比例、文理比例、修业年限、授予学位、选科建议、介绍、开设课程、考研方向、社会名人、就业情况（就业率、薪酬、就业行业分布、就业岗位分布、就业地区分布）"
    )
    parameters: dict = generate_param_schema(QueryMajorInfoParameters)

    def execute(self, return_format: str = "json", **kwargs: Any) -> ToolResult:
        try:
            params = QueryMajorInfoParameters(**kwargs)
            major_name = params.major_name
            major_level = params.major_level
            major = get_major(major_name, major_level)
            if return_format == "markdown":
                major_info = self.get_major_info_markdown(major.id)
            elif return_format == "json":
                major_info = self.get_major_info_json(major.id)
            else:
                raise ValueError(f'Invalid "return_format": "{return_format}". Must be "markdown" or "json".')
            return ToolResult(name=self.name, content=major_info, success=True)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return ToolResult(name=self.name, content=error_msg, success=False)

    def get_major_info_markdown(self, major_id: str) -> str:
        url = f"https://static-data.gaokao.cn/www/2.0/special/{major_id}/pc_special_detail.json?a=www.gaokao.cn"
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        data: dict = response.json()["data"]
        # 就业率
        job_rate_data = data.get("jobrate", [])
        job_rate_md = ""
        if job_rate_data:
            for single in job_rate_data:
                job_rate_md += f"- {single.get('year', 'N/A')}: {single.get('rate', 'N/A')}\n"
        else:
            job_rate_md += "暂无数据"
        # --- 薪酬概览 ---
        work_years = ["应届生", "2年经验", "5年经验", "10年经验"]
        professionalsalary = data.get("professionalsalary", {})
        # 本专业平均月薪
        majorsalaryavg = professionalsalary.get("majorsalaryavg", [])
        majorsalaryavg_md = ""
        if majorsalaryavg:
            for i, salary in enumerate(majorsalaryavg):
                year_label = work_years[i] if i < len(work_years) else f"阶段 {i+1}"
                salary_str = f"{salary} 元" if salary != 0 else "N/A"
                majorsalaryavg_md += f"- {year_label}: {salary_str}\n"
        else:
            majorsalaryavg_md += "暂无数据"
        # 所有专业平均月薪
        allmajorsalaryavg = professionalsalary.get("allmajorsalaryavg", [])
        allmajorsalaryavg_md = ""
        if allmajorsalaryavg:
            for i, salary in enumerate(allmajorsalaryavg):
                year_label = work_years[i] if i < len(work_years) else f"阶段 {i+1}"
                salary_str = f"{salary} 元" if salary != 0 else "N/A"
                allmajorsalaryavg_md += f"- {year_label}: {salary_str}\n"
        else:
            allmajorsalaryavg_md += "暂无数据"
        # --- 就业分布 ---
        job_detail = data.get("jobdetail", {})
        # Industry Distribution
        industry_distribution_data = job_detail.get("1", [])
        industry_distribution_md = ""
        if industry_distribution_data:
            for single in industry_distribution_data:
                industry_distribution_md += f"- {single.get('name', 'N/A')}: {single.get('rate', 'N/A')}%\n"
        else:
            industry_distribution_md += "暂无数据"
        # Position Distribution
        position_distribution_data = job_detail.get("3", [])
        position_distribution_md = ""
        if position_distribution_data:
            for single in position_distribution_data:
                position_distribution_md += f"- **{single.get('detail_pos', 'N/A')}** ({single.get('rate', 'N/A')}%):\n"
                position_distribution_md += f"    - 具体职业: {single.get('detail_job', 'N/A')}\n"
                position_distribution_md += f"    - 所在行业: {single.get('name', 'N/A')}\n"
        else:
            position_distribution_md += "暂无数据"
        # Area Distribution
        area_distribution_data = job_detail.get("2", [])
        area_distribution_md = ""
        if area_distribution_data:
            for single in area_distribution_data:
                area_distribution_md += f"- {single.get('area', 'N/A')}: {single.get('rate', 'N/A')}%\n"
        else:
            area_distribution_md += "暂无数据"

        md_string = f"""
# {data.get('name', 'N/A')}

## 一、基本信息
**类别:** {data.get('level1_name', 'N/A')} > {data.get('type', 'N/A')} > {data.get('type_detail', 'N/A')}
**代码:** {data.get('code', 'N/A')}
**男女比例:** {data.get('rate', 'N/A')}
**文理比例:** {data.get('rate2', 'N/A')}
**修业年限:** {data.get('limit_year', 'N/A')}
**授予学位:** {data.get('degree', 'N/A')}
**选科建议:** {data.get('sel_adv', 'N/A')}
**专业介绍:** {data.get('is_what', 'N/A')}
**开设课程:** {data.get('learn_what', 'N/A')}
**考研方向:** {data.get('direction', 'N/A')}
**社会名人:** {data.get('celebrity', 'N/A')}

## 二、就业情况
### 就业率
{job_rate_md.strip()}

### 薪酬概览
**本专业平均月薪:**
{majorsalaryavg_md.strip()}

**所有专业平均月薪:**
{allmajorsalaryavg_md.strip()}

### 就业分布
**最多就业行业:** {data.get('mostemploymentindustry', 'N/A')}
**最多就业岗位:** {data.get('mostemployedeposition', 'N/A')}
**最多就业地区:** {data.get('mostemploymentarea', 'N/A')}

**行业分布**
{industry_distribution_md.strip()}

**岗位分布**
{position_distribution_md.strip()}

**地区分布**
{area_distribution_md}
""".strip()
        return md_string

    def get_major_info_json(self, major_id: str) -> str:
        url = f"https://static-data.gaokao.cn/www/2.0/special/{major_id}/pc_special_detail.json?a=www.gaokao.cn"
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        data: dict = response.json()["data"]
        job_rate = {"year": [], "rate": []}
        for single in data.get("jobrate", []):
            job_rate["year"].append(single.get("year"))
            job_rate["rate"].append(single.get("rate"))
        job_detail = data.get("jobdetail", {})
        industry_distribution = []  # 就业行业分布
        position_distribution = []  # 就业岗位分布
        area_distribution = []  # 就业地区分布
        industry_distribution_data = job_detail.get("1", [])
        for single in industry_distribution_data:
            industry_distribution.append(
                {
                    "行业": single.get("name"),
                    "rate": f"{single.get('rate','')}%",
                }
            )
        position_distribution_data = job_detail.get("3", [])
        for single in position_distribution_data:
            position_distribution.append(
                {
                    "岗位": single.get("detail_pos"),
                    "rate": f"{single.get('rate','')}%",
                    "具体职业": single.get("detail_job"),
                    "所在行业": single.get("name"),
                }
            )
        area_distribution_data = job_detail.get("2", [])
        for single in area_distribution_data:
            area_distribution.append(
                {
                    "地区": single.get("area"),
                    "rate": f"{single.get('rate','')}%",
                }
            )
        professionalsalary = data.get("professionalsalary", {})
        majorsalaryavg = professionalsalary.get("majorsalaryavg")
        allmajorsalaryavg = professionalsalary.get("allmajorsalaryavg")
        result = {
            "名称": data.get("name"),
            "类别": f"{data.get('level1_name')}>{data.get('type')}>{data.get('type_detail')}",
            "代码": data.get("code"),
            "男女比例": data.get("rate"),
            "文理比例": data.get("rate2"),
            "修业年限": data.get("limit_year"),
            "授予学位": data.get("degree"),
            "选科建议": data.get("sel_adv"),
            "考研方向": data.get("direction"),
            "社会名人": data.get("celebrity"),
            "专业介绍": data.get("is_what"),
            "开设课程": data.get("learn_what"),
            "就业率": job_rate,
            "薪酬": {
                "工作年限": ["应届生", "2年经验", "5年经验", "10年经验"],
                "本专业平均薪酬/月": majorsalaryavg,
                "所有专业平均薪酬/月": allmajorsalaryavg,
            },
            "最多就业行业": data.get("mostemploymentindustry"),
            "最多就业岗位": data.get("mostemployedeposition"),
            "最多就业地区": data.get("mostemploymentarea"),
            "就业行业分布": industry_distribution,
            "就业岗位分布": position_distribution,
            "就业地区分布": area_distribution,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
