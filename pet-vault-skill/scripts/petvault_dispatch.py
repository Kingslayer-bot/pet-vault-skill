"""
petvault_dispatch: unified request dispatcher (emergency / knowledge / report routing).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

EMERGENCY_PATTERNS = [
    re.compile(r"中毒|毒素|毒物|吃了.*(巧克力|葡萄|洋葱|大蒜|百合|老鼠|蟑螂|杀虫剂|清洁剂|药品|药片|药丸|人[用吃].*药)", re.IGNORECASE),
    re.compile(r"抽搐|痉挛|癫痫|seizure", re.IGNORECASE),
    re.compile(r"呼吸困难|喘不上气|喘不过气|breathing\s+difficulty|trouble\s+breathing", re.IGNORECASE),
    re.compile(r"尿不出来|无法排尿|尿闭|排尿困难|can['\u2019]t\s+urinate|cannot\s+urinate|unable\s+to\s+urinate", re.IGNORECASE),
    re.compile(r"持续呕吐|不停[地在]吐|persistent\s+vomiting|constant\s+vomiting", re.IGNORECASE),
    re.compile(r"严重外伤|大出血|严重创伤|severe\s+trauma|heavy\s+bleeding", re.IGNORECASE),
    re.compile(r"晕倒|昏迷|不醒|休克|collapse|unconscious|passed\s+out", re.IGNORECASE),
    re.compile(r"吞了|吃[进了]异物|误食|foreign\s+body|swallowed.*object", re.IGNORECASE),
    re.compile(r"腹胀|胃胀|腹部膨胀|bloat|gastric\s+dilatation|GDV", re.IGNORECASE),
    re.compile(r"木糖醇|xylitol", re.IGNORECASE),
]

EMERGENCY_RESPONSE = """\
⚠️ 紧急提醒：你描述的情况可能属于需要立即处理的宠物急症。

请立即联系兽医或拨打宠物中毒热线：
- 美国 ASPCA Poison Control: (888) 426-4435
- 请尽快带宠物到最近的动物医院就诊。

不要等待观察，不要自行用药。记录摄入毒物的种类、数量、时间并带到医院。

---

⚠️ URGENT: The situation you described may be a pet emergency.

Contact your veterinarian immediately or call:
- ASPCA Poison Control (US): (888) 426-4435
- Take your pet to the nearest veterinary hospital now.

Do not wait to observe. Do not self-medicate. Record what was ingested, how much, and when, and bring this information to the hospital.
"""

KNOWLEDGE_PATTERNS = [
    re.compile(r"(什么|啥|怎么|咋).*(意思|含义|定义|是|回事)", re.IGNORECASE),
    re.compile(r"(解释|说明|介绍).*[一下]?", re.IGNORECASE),
    re.compile(r"(what|explain|tell me about|definition|meaning|define)", re.IGNORECASE),
]


def get_emergency_response() -> str:
    return EMERGENCY_RESPONSE


def detect_emergency(request_text: str) -> bool:
    if not request_text:
        return False
    for pattern in EMERGENCY_PATTERNS:
        if pattern.search(request_text):
            return True
    return False


def detect_knowledge_intent(request_text: str) -> bool:
    if not request_text:
        return False
    for pattern in KNOWLEDGE_PATTERNS:
        if pattern.search(request_text.lower()):
            return True
    return False


def knowledge_only_answer(query: str) -> str:
    if not query:
        return "请提供具体问题。"
    result = subprocess.run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "query_knowledge_base.py"),
            query,
            "--limit",
            "3",
        ],
        cwd=str(SKILL_DIR.parent),
        text=True,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        return f"查询知识库时出错：{result.stderr[:300]}"
    try:
        data = json.loads(result.stdout)
        matches = data.get("matches", [])
    except json.JSONDecodeError:
        return result.stdout[:600]
    if not matches:
        return (
            "当前本地知识库未找到相关答案。"
            "您可以向兽医咨询，或上传相关材料生成详细报告。\n\n"
            "No matching answer found in the local knowledge base. "
            "Please consult your veterinarian or upload materials for a detailed report."
        )
    lines = ["## 本地知识库查询结果", ""]
    for i, match in enumerate(matches[:3], 1):
        title = match.get("title", "无标题")
        domain = match.get("domain", "")
        jurisdiction = match.get("jurisdiction", "")
        snippet = match.get("snippet", match.get("body", ""))[:300]
        lines.append(f"### {i}. {title}")
        lines.append(f"领域：{domain} | 地区：{jurisdiction}")
        lines.append(f"{snippet}")
        lines.append("")
    return "\n".join(lines)


def dispatch(request_text: str, input_dir: Path | None = None, has_materials: bool = False) -> str:
    if request_text and detect_emergency(request_text):
        return "emergency"

    actual_has_materials = has_materials or (
        input_dir is not None and input_dir.exists() and input_dir.is_dir() and any(input_dir.iterdir())
    )

    if actual_has_materials:
        return "report"

    if request_text and detect_knowledge_intent(request_text):
        return "knowledge_query"

    if request_text:
        return "knowledge_query"

    return "report"


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="PetVault unified request dispatcher.")
    parser.add_argument("--request", default="", help="User request text.")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "report", "knowledge", "emergency"],
        help="Dispatch mode (default: auto).",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON.")
    args = parser.parse_args()
    result = dispatch(args.request)
    if args.json:
        json.dump({"route": result, "mode": args.mode, "request": args.request}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"Route: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
