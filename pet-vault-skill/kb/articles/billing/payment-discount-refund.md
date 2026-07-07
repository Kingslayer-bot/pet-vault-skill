---
id: payment-discount-refund
title: 付款、折扣和退款不能混入医疗费用
domain: billing
jurisdiction: global
language: zh
currency: [USD, CNY, RMB, HKD, SGD, JPY]
species: [dog, cat]
source_tier: internal_template
risk_level: high
allowed_outputs: [amount_validation, payment_reconciliation]
forbidden_outputs: [payment_counted_as_charge, discount_counted_as_charge, refund_counted_as_charge]
sources: [internal-anonymized-billing-taxonomy]
last_reviewed: 2026-07-07
expires_at: 2027-07-07
---

# 付款、折扣和退款不能混入医疗费用

## 用户会怎么问

Paid、Payment、Discount、Refund、CareCredit Payment、优惠、退款这些要不要算进总费用？

## 简明解释

charge 是医疗服务或商品收费；payment 是已付款；discount 是折扣或减免；refund 是退款；tax 是税。PetVault 必须分别核算，不能把付款、折扣、退款混入医疗费用。

## 用户需要检查

- 负数、括号金额和 Paid/Payment 字样。
- Discount/优惠/adjustment 字样。
- Refund/退款/退费字样。

## 可以输出

- “本次医疗收费小计”和“付款/折扣/退款记录”分开展示。

## 禁止输出

- 用付款金额抵消后再说医疗费用为零。
- 忽略币种或未知币种。

## 证据与来源

- internal-anonymized-billing-taxonomy

## 不确定性

如果一行同时出现合计和付款，应要求用户提供完整账单或人工复核。
