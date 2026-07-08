---
id: billing-line-items-jp
title: 日本宠物医疗账单项目解释
domain: billing
jurisdiction: JP
language: zh
currency: [JPY]
species: [dog, cat]
source_tier: internal_template
risk_level: medium
allowed_outputs: [explain_bill_item, cost_breakdown, clinic_questions]
forbidden_outputs: [price_fairness_judgment, diagnosis_from_bill, mix_payment_with_charge]
sources: [internal-anonymized-billing-taxonomy]
last_reviewed: 2026-07-08
expires_at: 2027-07-08
---

# 日本宠物医疗账单项目解释

## 用户会怎么问

日本动物病院的领收书怎么看？検察、手術、投薬是什么？

## 简明解释

日本动物病院的领收书常见项目包括検察（检查）、投薬（用药）、注射、手術（手术）、入院（住院）、画像診断（影像诊断）等。费用以日元（JPY）计算。PetVault 只能解释类别和核对点，不能替病院判断价格是否合理。

## 用户需要检查

- 每一行是否是医疗 charge、payment、discount、refund 或 tax。
- 未识别项目必须标记 unknown。
- 高额项目需要原始领收书行和病院解释。

## 可以输出

- 费用分类、金额小计、需要向病院确认的问题。

## 禁止输出

- 将 payment、discount、refund 算入医疗收费。
- 仅凭领收书判断诊断或治疗必要性。

## 证据与来源

- internal-anonymized-billing-taxonomy

## 不确定性

领收书缩写和病院命名差异很大，识别准确度较低的项目需要人工复核。
