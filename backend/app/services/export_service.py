"""
导出服务 — Markdown / PDF
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from app.models.schemas import Itinerary

# 尝试注册中文字体
try:
    pdfmetrics.registerFont(TTFont("SimSun", "C:/Windows/Fonts/simsun.ttc"))
    CN_FONT = "SimSun"
except Exception:
    CN_FONT = "Helvetica"


def itinerary_to_markdown(itinerary: Itinerary) -> str:
    """将行程渲染为 Markdown"""
    lines = [
        f"# {itinerary.destination}旅行计划",
        f"",
        f"**概要**：{itinerary.summary}",
        f"",
        f"**预算**：¥{itinerary.estimated_budget:,.0f}",
        f"",
    ]

    if itinerary.tips:
        lines.append("## 旅行提示")
        for tip in itinerary.tips:
            lines.append(f"- {tip}")
        lines.append("")

    for day in itinerary.days:
        lines.append(f"## 第{day.day_index+1}天：{day.theme or '行程'}")
        if day.date:
            lines.append(f"**日期**：{day.date}")
        lines.append("")

        for spot in day.spots:
            lines.append(f"### {spot.name}")
            if spot.description:
                lines.append(f"{spot.description}")
            if spot.estimated_cost and spot.estimated_cost > 0:
                lines.append(f"- 💰 门票：¥{spot.estimated_cost}")
            if spot.location and spot.location.address:
                lines.append(f"- 📍 地址：{spot.location.address}")
            lines.append("")

        for meal in day.meals:
            lines.append(f"**🍽 {meal.type}**：{meal.name}")
            if meal.description:
                lines.append(f"  {meal.description}")
            lines.append("")

        if day.notes:
            lines.append(f"> {day.notes}")
            lines.append("")

    # 预算明细
    bd = itinerary.budget_breakdown
    lines.append("## 预算明细")
    lines.append(f"| 类别 | 金额 |")
    lines.append(f"|------|------|")
    lines.append(f"| 交通 | ¥{bd.transport} |")
    lines.append(f"| 住宿 | ¥{bd.hotel} |")
    lines.append(f"| 餐饮 | ¥{bd.meals} |")
    lines.append(f"| 门票 | ¥{bd.tickets} |")
    lines.append(f"| 其他 | ¥{bd.other} |")
    lines.append(f"| **合计** | **¥{bd.total}** |")

    return "\n".join(lines)


def itinerary_to_pdf_bytes(itinerary: Itinerary) -> bytes:
    """将行程渲染为 PDF，返回字节"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()

    cn_style = ParagraphStyle(
        "CN", parent=styles["Normal"],
        fontName=CN_FONT, fontSize=11, leading=18,
    )
    title_style = ParagraphStyle(
        "CNTitle", parent=styles["Heading1"],
        fontName=CN_FONT, fontSize=18, leading=24,
    )

    story = []
    story.append(Paragraph(f"{itinerary.destination}旅行计划", title_style))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(f"概要：{itinerary.summary}", cn_style))
    story.append(Paragraph(f"预算：¥{itinerary.estimated_budget:,.0f}", cn_style))
    story.append(Spacer(1, 4*mm))

    for day in itinerary.days:
        story.append(Paragraph(f"第{day.day_index+1}天：{day.theme or ''}", styles["Heading2"]))
        for spot in day.spots:
            story.append(Paragraph(f"景点：{spot.name}", cn_style))
            if spot.description:
                story.append(Paragraph(spot.description, cn_style))
        for meal in day.meals:
            story.append(Paragraph(f"餐饮：{meal.name}", cn_style))
        story.append(Spacer(1, 2*mm))

    doc.build(story)
    return buffer.getvalue()
