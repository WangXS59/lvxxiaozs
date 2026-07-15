"""
LLM 行程生成 Agent
- 组装 Prompt
- 调用 qwen-max 生成结构化旅行计划
- 解析 JSON 输出
"""
import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.agents.tools.rag_tool import build_destination_query
from app.rag.retriever import retrieve_travel_guide, format_context_for_llm

SYSTEM_PROMPT = """你是一个专业的旅行规划师。根据提供的参考资料和用户需求，生成一份详细的旅行计划。

## 严格要求

1. 只输出一个 JSON 对象，用 ```json 代码块包裹
2. 每天安排 1-2 个景点，节奏符合用户指定的轻松/适中/紧凑
3. 景点名称和住宿推荐必须来自参考资料，不要编造
4. 每天必须包含：spot_name, spot_description, meal_name, meal_notes, daily_note
5. 为每天推荐当晚住宿区域（hotel_name, hotel_notes），优先推荐靠近当前景点或次日景点的住宿

## JSON 格式（严格复制，字段名不能变）

```json
{
    "summary": "2句话的行程概览",
    "tips": ["建议1", "建议2", "建议3"],
    "days": [
        {
            "day_index": 0,
            "theme": "主题",
            "spot_name": "景点名",
            "spot_description": "景点描述",
            "meal_name": "推荐餐食",
            "meal_notes": "餐食说明",
            "daily_note": "当天备注",
            "hotel_name": "推荐住宿区域或酒店名",
            "hotel_notes": "住宿说明（价格范围、特色等）"
        }
    ]
}
```

## 注意
- days 数组长度 = 旅行天数
- day_index 从 0 开始，最后一天如果没有住宿，hotel_name可以为空
- spot_name, spot_description, meal_name, meal_notes, daily_note 都是**必填字段**，不能省略
- hotel_name 从参考资料中的住宿建议章节提取
"""


def _extract_json(text: str) -> dict:
    """从 LLM 返回的文本中提取 JSON 对象"""
    text = text.strip()
    # 去掉 ```json ... ``` 包裹
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if m:
        text = m.group(1)
    # 找最外层 {...}
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        text = m.group(0)
    return json.loads(text)


def generate_planner_draft(
    destination: str,
    day_count: int,
    travelers: int,
    budget: float | None,
    preferences: str,
    pace: str,
    special_notes: str,
    hotel_level: str,
) -> dict:
    """
    调用 LLM 生成行程草稿。

    返回: {"summary": str, "tips": [str], "days": [dict]}
    """
    # ① 获取 RAG 上下文
    query = build_destination_query(destination, preferences, pace, special_notes)
    rag_chunks = retrieve_travel_guide(query, destination=destination, top_k=3)
    context = format_context_for_llm(rag_chunks) if rag_chunks else "暂无参考资料"

    # ② 组装 Human Prompt
    budget_str = f"¥{budget:,.0f}" if budget else "不限制"
    user_desc_parts = [f"目的地：{destination}"]
    user_desc_parts.append(f"天数：{day_count}天")
    user_desc_parts.append(f"人数：{travelers}人")
    user_desc_parts.append(f"预算：{budget_str}")
    if preferences:
        user_desc_parts.append(f"偏好：{preferences}")
    if pace:
        user_desc_parts.append(f"节奏：{pace}")
    if special_notes:
        user_desc_parts.append(f"特殊要求：{special_notes}")
    user_desc_parts.append(f"住宿档次：{hotel_level}")

    human_prompt = f"""以下是参考资料：

{context}

---
用户需求：
{chr(10).join(user_desc_parts)}

请根据参考资料和用户需求，生成一个 {day_count} 天的{destination}旅行计划（JSON格式）。"""

    # ③ 调用 LLM
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0.7,
        max_tokens=3000,
    )
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ]
    resp = llm.invoke(messages)
    result_text = resp.content

    # ④ 解析 JSON
    try:
        draft = _extract_json(result_text)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"LLM 返回的 JSON 解析失败: {e}\n原始内容: {result_text[:500]}")

    # ⑤ 校验天数
    days = draft.get("days", [])
    if len(days) != day_count:
        raise ValueError(f"生成天数不匹配：期望 {day_count} 天，实际 {len(days)} 天")

    return draft


def edit_day_draft(
    destination: str,
    current_day_json: str,
    instruction: str,
) -> dict:
    """
    智能编辑：根据用户自然语言指令，修改某一天的行程。

    参数：
    - destination: 目的地
    - current_day_json: 当前该天的完整 DayPlan JSON
    - instruction: 用户的编辑指令（自然语言）

    返回：修改后的单天 draft（格式同 generate_planner_draft 的 day 元素）
    """
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0.5,
        max_tokens=1500,
    )

    edit_prompt = f"""你是一个旅行行程编辑器。用户想修改{destination}行程中某一天的内容。

## 当前行程（JSON）：
{current_day_json}

## 用户修改指令：
{instruction}

## 要求：
1. 根据指令修改当前行程内容，只改动用户要求变更的部分，其余保持原样
2. **必须保持与「当前行程」完全相同的 JSON 结构**：
   - 景点放在 spots 数组里（每个元素含 name / description，若知道坐标可填 location.latitude / location.longitude / location.address）
   - 餐饮放在 meals 数组里（每个元素含 type / name / description）
   - 住宿放在 hotel 对象里（含 name / level / notes）
3. 只输出修改后的单天 JSON，用 ```json 包裹
4. 不要输出任何解释文字，只输出 JSON 代码块

输出示例：
```json
{{
    "day_index": 0,
    "date": "2026-07-16",
    "theme": "修改后的主题",
    "spots": [
        {{"name": "新景点名", "description": "景点介绍", "location": {{"address": "地址", "latitude": 34.68, "longitude": 112.47}}}}
    ],
    "meals": [
        {{"type": "正餐", "name": "新餐食", "description": "餐食说明"}}
    ],
    "hotel": {{"name": "住宿名", "level": "舒适型", "notes": "住宿说明"}},
    "notes": "当天备注"
}}
```"""

    messages = [
        SystemMessage(content="你是旅行行程编辑器，只输出 JSON。"),
        HumanMessage(content=edit_prompt),
    ]
    resp = llm.invoke(messages)
    result_text = resp.content

    try:
        return _extract_json(result_text)
    except (json.JSONDecodeError, ValueError):
        raise ValueError(f"编辑失败，LLM返回无法解析。原始内容: {result_text[:300]}")
