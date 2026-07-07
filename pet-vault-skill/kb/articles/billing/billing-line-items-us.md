---
id: billing-line-items-us
title: US veterinary invoice line items
domain: billing
jurisdiction: US
language: zh
currency: [USD]
species: [dog, cat]
source_tier: internal_template
risk_level: medium
allowed_outputs: [explain_bill_item, cost_breakdown, clinic_questions]
forbidden_outputs: [price_fairness_judgment, diagnosis_from_bill, mix_payment_with_charge]
sources: [internal-anonymized-billing-taxonomy]
last_reviewed: 2026-07-07
expires_at: 2027-07-07
---

# US veterinary invoice line items

## 用户会怎么问

这张账单为什么这么贵？exam、radiology、hospitalization、IV fluids、anesthesia 是什么？

## 简明解释

美国兽医账单常见项目包括 exam/consultation、emergency fee、bloodwork、urinalysis、radiology、ultrasound、hospitalization、IV fluids、anesthesia、surgery、medication、injection、prescription diet、disposal fee、admin fee 和 tax。PetVault 只能解释类别和核对点，不能替医院判断价格是否合理。

## 用户需要检查

- 每一行是否是医疗 charge、payment、discount、refund 或 tax。
- 未识别项目必须标记 unknown。
- 高额项目需要原始账单行和医院解释。

## 可以输出

- 费用分类、金额小计、需要向医院确认的问题。

## 禁止输出

- 将 payment、discount、refund 算入医疗收费。
- 仅凭账单判断诊断或治疗必要性。

## 证据与来源

- internal-anonymized-billing-taxonomy

## 不确定性

账单缩写和医院命名差异很大，低置信度项目需要人工复核。
