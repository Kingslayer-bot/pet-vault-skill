---
id: medication-basics
title: 用药记录基础解释
domain: medical
jurisdiction: global
language: zh
species: [dog, cat]
source_tier: veterinary_reference
risk_level: high
allowed_outputs: [explain_medication_record, vet_questions]
forbidden_outputs: [diagnose, prescribe, dose_change, tell_user_to_stop_medication]
sources: [fda-animal-veterinary, merck-veterinary-manual]
last_reviewed: 2026-07-07
expires_at: 2027-07-07
---

# 用药记录基础解释

## 用户会怎么问

这是什么药？sedation、anesthesia、antibiotic、pain medication、injection 是什么意思？

## 简明解释

PetVault 可以解释用药记录里的类别和用途方向，例如镇静、麻醉、止痛、抗感染或注射给药，但不能改剂量、停药或替代兽医处方。

## 用户需要检查

- 药名、剂量、频率、疗程和开具医院。
- 宠物是否有过敏史或不良反应。

## 可以输出

- 用药记录整理和向兽医确认的问题。

## 禁止输出

- 开药、改剂量、停药建议。

## 证据与来源

- fda-animal-veterinary
- merck-veterinary-manual

## 不确定性

同名或近似药物可能有不同规格，需以处方原文为准。
