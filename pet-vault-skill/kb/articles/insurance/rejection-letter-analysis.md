---
id: rejection-letter-analysis
title: 拒赔信分析边界
domain: insurance
jurisdiction: global
language: zh
currency: [USD, CNY, RMB, HKD, SGD, JPY]
species: [dog, cat]
source_tier: regulator
risk_level: high
allowed_outputs: [rejection_reason_summary, insurer_questions, missing_document_checklist]
forbidden_outputs: [legal_advice, accuse_insurer, help_falsify_records, help_hide_preexisting_condition]
sources: [naic-pet-insurance-model-act, nfra-pet-insurance-risk-cn]
last_reviewed: 2026-07-07
expires_at: 2027-07-07
---

# 拒赔信分析边界

## 用户会怎么问

保险拒赔了，我该补什么材料？拒赔理由和条款在哪里？

## 简明解释

PetVault 可以提取拒赔理由、引用条款、缺少材料、可向保险公司追问的问题。不能下违法结论，也不能帮助用户修改事实材料。

## 用户需要检查

- 拒赔信原文。
- 保单对应条款页码。
- 症状首次出现时间和真实病历。

## 可以输出

- 客观询问信和材料补充清单。

## 禁止输出

- 法律结论。
- 伪造、包装或规避事实。

## 证据与来源

- naic-pet-insurance-model-act
- nfra-pet-insurance-risk-cn

## 不确定性

复核结果取决于保险公司和补充材料。
