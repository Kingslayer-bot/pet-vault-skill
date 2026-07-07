---
id: billing-line-items-cn
title: 中国宠物医疗账单项目解释
domain: billing
jurisdiction: CN
language: zh
currency: [CNY, RMB]
species: [dog, cat]
source_tier: internal_template
risk_level: medium
allowed_outputs: [explain_bill_item, cost_breakdown, clinic_questions]
forbidden_outputs: [price_fairness_judgment, diagnosis_from_bill, mix_payment_with_charge]
sources: [internal-anonymized-billing-taxonomy]
last_reviewed: 2026-07-07
expires_at: 2027-07-07
---

# 中国宠物医疗账单项目解释

## 用户会怎么问

检查费、B 超、血检、处置费、药费、废弃物处理费、优惠和付款分别是什么？

## 简明解释

中国宠物医疗账单常见项目包括诊疗/问诊、急诊费、血检、尿检、影像、B 超、住院、输液、麻醉、手术、药品、针剂、处方粮、医疗废弃物处理、服务费、税费、付款、折扣和退款。付款、折扣、退款不是医疗服务收费，必须分开。

## 用户需要检查

- 金额币种是否是 CNY/RMB 或明确的人民币符号。
- 付款和优惠是否被误混入治疗费用。
- 模糊项目是否标记 unknown。

## 可以输出

- 人民币金额分类、费用大头、待向医院确认的项目。

## 禁止输出

- 代替医院解释收费合理性。
- 用账单反推宠物疾病结论。

## 证据与来源

- internal-anonymized-billing-taxonomy

## 不确定性

不同医院的中文简称差异大，必须保留原文行作为证据。
