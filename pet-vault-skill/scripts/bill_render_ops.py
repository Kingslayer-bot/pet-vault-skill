"""bill_render_ops: Reconstructed bill rendering for user-readable PDF reports.

Converts extracted bill items into clean, user-readable Markdown tables.
Does NOT embed raw invoice images — instead re-renders structured data.
"""
from __future__ import annotations

# User-visible kind labels (Chinese)
KIND_LABELS = {
    "charge": "收费项目",
    "payment": "已支付",
    "discount": "折扣/减免",
    "refund": "退款",
    "balance": "余额",
    "total": "合计",
    "tax": "税费",
    "unknown": "待确认项目",
}

# Category labels for bill items
CATEGORY_LABELS = {
    "检查": "检查",
    "治疗": "治疗",
    "药品": "药品",
    "耗材": "耗材",
    "服务": "服务",
    "付款": "付款",
    "折扣": "折扣",
    "退款": "退款",
    "余额": "余额",
    "合计": "合计",
    "其他": "其他",
}


def _format_amount(amount: float, currency: str) -> str:
    """Format amount with currency for display."""
    return f"{amount:.2f} {currency}"


def _kind_label(kind: str) -> str:
    """Get user-visible label for bill item kind."""
    return KIND_LABELS.get(kind, "待确认项目")


def _category_label(category: str) -> str:
    """Get user-visible label for bill item category."""
    return CATEGORY_LABELS.get(category, category)


def render_reconstructed_bill_section(
    bill_items: list[dict],
    totals: dict[str, float],
    *,
    source_label: str | None = None,
) -> str:
    """Render a reconstructed bill section from extracted bill items.

    Produces a clean Markdown table suitable for PDF rendering.
    Does NOT embed raw invoice images.

    Args:
        bill_items: List of bill items from billing_ops.build_bill_items().
        totals: Charge totals from billing_ops.summarize_charge_totals().
        source_label: Optional label for the source material.

    Returns:
        Markdown string with reconstructed bill section.
    """
    lines = []
    lines.append("## 账单复刻区")
    lines.append("")
    lines.append("以下内容根据上传材料提取并重新排版，仅用于帮助理解账单，不替代原始票据。")
    lines.append("")

    if not bill_items:
        lines.append("当前材料未提取到账单明细。")
        lines.append("")
        return "\n".join(lines)

    # Build table
    lines.append("| 项目 | 类型 | 金额 | 说明 |")
    lines.append("|---|---|---:|---|")

    for item in bill_items:
        name = item.get("name", "未知项目")
        kind = item.get("kind", "unknown")
        amount = item.get("signed_amount", item.get("amount", 0))
        currency = item.get("currency", "CNY")
        category = item.get("category", "其他")

        kind_display = _kind_label(kind)
        amount_display = _format_amount(amount, currency)
        category_display = _category_label(category)

        # Truncate long names
        if len(name) > 30:
            name = name[:27] + "..."

        lines.append(f"| {name} | {kind_display} | {amount_display} | {category_display} |")

    lines.append("")

    # Summary
    if totals:
        summary_parts = [f"{_format_amount(amount, currency)}" for currency, amount in sorted(totals.items())]
        lines.append(f"识别到的收费合计：{'；'.join(summary_parts)}")
    else:
        lines.append("识别到的收费合计：待确认")

    lines.append("")
    return "\n".join(lines)


def render_bill_summary_text(
    bill_items: list[dict],
    totals: dict[str, float],
) -> str:
    """Render a short bill summary text for chat output.

    Args:
        bill_items: List of bill items.
        totals: Charge totals.

    Returns:
        Short summary string.
    """
    if not bill_items:
        return "当前材料未提取到账单明细。"

    charge_count = len([i for i in bill_items if i.get("kind") == "charge"])
    if totals:
        summary_parts = [f"{_format_amount(amount, currency)}" for currency, amount in sorted(totals.items())]
        total_str = "；".join(summary_parts)
        return f"识别到 {charge_count} 个收费项目，合计约 {total_str}。"

    return f"识别到 {charge_count} 个收费项目，但无法计算合计。"
