---
id: billing-line-items-sg
title: 新加坡宠物医疗账单项目解释
domain: billing
jurisdiction: SG
language: zh
currency: [SGD]
species: [dog, cat]
source_tier: internal_template
risk_level: medium
allowed_outputs: [explain_bill_item, cost_breakdown, clinic_questions]
forbidden_outputs: [price_fairness_judgment, diagnosis_from_bill, mix_payment_with_charge]
sources: [internal-anonymized-billing-taxonomy]
last_reviewed: 2026-07-08
expires_at: 2027-07-08
---

# 新加坡宠物医疗账单项目解释

## 用户会怎么问

新加坡兽医账单里的 consultation、procedure、medication 是什么？

## 简明解释

新加坡兽医账单常见项目包括 consultation（诊费）、procedure（治疗/手术）、medication（药物）、diagnostic（化验/影像）、hospitalization（住院）、vaccination（疫苗）等。费用以新加坡元（SGD）计算。PetVault 只能解释类别和核对点，不能替医院判断价格是否合理。

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

账单缩写和医院命名差异很大，识别准确度较低的项目需要人工复核。
