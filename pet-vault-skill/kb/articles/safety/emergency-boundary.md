---
id: emergency-boundary
title: 急症安全边界
domain: safety
jurisdiction: global
language: zh
species: [dog, cat]
source_tier: veterinary_reference
risk_level: high
allowed_outputs: [urgent_safety_response, ask_time_weight_dose, contact_vet]
forbidden_outputs: [diagnose, downplay_emergency, delay_vet_care]
sources: [aspca-poison-control, merck-veterinary-manual]
last_reviewed: 2026-07-07
expires_at: 2027-07-07
---

# 急症安全边界

## 用户会怎么问

宠物呼吸困难、抽搐、无法排尿、持续呕吐、严重外伤、昏迷、腹胀、疑似异物吞食怎么办？

## 简明解释

急症问题优先触发安全边界，不走普通知识问答。应提醒用户尽快联系兽医急诊或当地动物毒物热线，同时可收集发生时间、体重、剂量、症状变化等信息。

## 用户需要检查

- 发生时间。
- 宠物体重和症状。
- 可能接触或吞食的物品。

## 可以输出

- 立即联系兽医或毒物热线的提醒。
- 带去医院的信息清单。
- 各地区紧急联系方式：
  - 美国：ASPCA Poison Control (888) 426-4435
  - 中国：联系当地动物疫病预防控制中心或最近的 24 小时动物医院
  - 香港：渔农自然护理署 (AFCD) 2708 8885
  - 新加坡：AVS Animal Response Centre 1800-476-1600
  - 日本：各都道府县动物愛護センター

## 禁止输出

- 诊断结论。
- 延误就医的安抚话术。

## 证据与来源

- aspca-poison-control
- merck-veterinary-manual

## 不确定性

远程文字无法判断严重程度，红线场景按紧急处理。
