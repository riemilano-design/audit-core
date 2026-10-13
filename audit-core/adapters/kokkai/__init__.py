# -*- coding: utf-8 -*-
"""国会会議録の限定デモ adapter(2026-10-14、計画 ``docs/KOKKAI_DEMO_PLAN_2026-10-14.md``)。

「文章を書く側が根拠(発言番号)を添える」形の claim を、会議録(国会会議録
検索システム API の応答 JSON)と照らす。確かめるのは 4 点だけ: 発言番号が
実在するか / 発言者が一致するか / 引用が発言に在るか / 数が発言に在るか。
一般の議事録への一般化は主張しない(人間の決定 2026-10-13)。

Core(``audit_core``)を import するのは ``recipes.py``・``registry_setup.py``・
``verify_meeting.py`` だけ。``load.py``・``numerals.py``・``resolve.py``・
``comparators.py`` は Core を知らない(``comparators.py`` は Core の
``Comparison`` を返すために関数の中で import する ― 将棋 adapter と同じ形)。
"""
