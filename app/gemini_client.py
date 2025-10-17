import os
# Suppress noisy gRPC/absl logs early
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GLOG_minloglevel", "2")
from typing import Any, Dict, List
from dotenv import load_dotenv
import concurrent.futures

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "45"))

def build_prompt(profile: Dict[str, Any], schedule_text: str, summaries: List[Dict[str, Any]]) -> str:
    return f"""
你是一个专业的跑步教练AI。请基于以下内容进行：
1) 分析上传的历史训练FIT数据（距离、配速、时长、心率等）,并做出总结说明。
2) 为未来一周制定训练计划，默认保持用户的时间安排结构不变，除非发现明显问题需要微调，并解释理由。
3) 计划应包含每天的训练类型（轻松跑、强度课、LSD等）、目标配速或心率区间，以及训练时长。
3) 输出简洁明了的总结与建议。

[用户基础信息]
{profile.get('basic_info','')}

[心率与分区说明]
{profile.get('hr_zones','')}

[其他说明]
{profile.get('other_info','')}

[当前时间安排文本]
{schedule_text}

[历史FIT汇总]
{summaries}

请先输出「分析总结」，然后输出「一周计划」：按星期一到星期天逐日列出内容。确保轻松跑以心率区间为主（Z2-Z3），强度课以配速为主，保留现有结构（周一/二轻松，周三休息，周四强度，周五休息，周六LSD，周日休息），若调整请给出理由。输出同时给出一个JSON结构，字段：days[{{day, workout_type, details, target}}]。
""".strip()

# Lazy import to avoid missing dependency at import time

def analyze_and_plan(profile: Dict[str, Any], schedule_text: str, summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        return {
            "error": "GEMINI_API_KEY 缺失。请在 .env 中配置。",
            "plan_json": None
        }
    try:
        import google.generativeai as genai
        import re
        import json

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = build_prompt(profile, schedule_text, summaries)
        # Enforce a timeout so the request doesn't hang indefinitely
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(model.generate_content, prompt)
            try:
                resp = future.result(timeout=GEMINI_TIMEOUT)
            except concurrent.futures.TimeoutError:
                return {"error": f"分析超时（>{GEMINI_TIMEOUT}s）。请稍后重试。", "plan_json": None}
        text = resp.text or ""

        plan_json = None
        # Use regex to find the json block
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                # The prompt asks for a specific structure, so we look for the 'days' key
                data = json.loads(json_str)
                if 'days' in data and isinstance(data['days'], list):
                    plan_json = data['days']
            except json.JSONDecodeError:
                pass # Ignore if JSON is malformed

        return {
            "text": text,
            "plan_json": plan_json
        }
    except Exception as e:
        return {"error": str(e), "plan_json": None}
