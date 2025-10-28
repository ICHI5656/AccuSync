#!/usr/bin/env python3
"""
Test script for product keyword extraction.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.import_service import ImportService

# Test cases from the sample CSV
test_cases = [
    "ハードケース(ボタニカル 青春花柄：ホワイト)h077@04/F-53E_大(974)",
    "ハードケース(電池切れ猫：オレンジ)h240124/F-51B_大(975)",
    "手帳型カバーmirror(刺繍風プリント：グリーン)095@04m/wish4(mirror)_3L(976)",
    "手帳型カバーmirror(北欧アニマル柄：オレンジ)188@02m/Pixel 10(mirror)_L(977)",
    "ハードケース(カメレオン：ピンク)h066@05/SM-A366_若特大(978)",
    "手帳型カバーmirror(紫犬：もずくリーボ)210356m/iPhone Air(mirror)_2L(979)",
    "手帳型カバーcard(刺繍風プリント：カーキ)095@01c/iPhone 16(card)_L(980)",
    "手帳型カバーmirror(和柄 千代紙風：レッド)180a01m/iphone16e(mirror)_L(981)",
    "ハードケース(バイク猫：ぴんく)h219@05/F-53E_大(982)",
    "手帳型カバーmirror(ボタニカル 赤青花柄：ブラック)077@02m/iPhone 15 Plus(mirror)_2L(983)",
    "手帳型カバーcard(リスク熊：モスグリーン)210585c/iPhone 11(card)_L(984)",
    "手帳型カバーcard(柴犬：ぴんく)210355c/Pixel 9a(card)_LL(985)",
]

print("=" * 80)
print("商品名からのキーワード抽出テスト")
print("=" * 80)
print()

for i, product_name in enumerate(test_cases, 1):
    keywords = ImportService._extract_product_keywords(product_name)
    print(f"テスト {i}:")
    print(f"  商品名: {product_name}")
    print(f"  抽出結果: {keywords}")
    print()

print("=" * 80)
print("テスト完了")
print("=" * 80)
