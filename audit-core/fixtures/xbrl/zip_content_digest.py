# -*- coding: utf-8 -*-
"""ZIP の**中身だけ**から作る印。Core のコードではない。

なぜ要るか(2026-10-08 に実測): **EDINET は要求ごとに ZIP を作り直すので、
ZIP の sha256 は再現しない。** 同じ `docID` を取り直したら、バイト数は同じ
541,790 のままで sha256 が `d8337184477d6554…` → `74c51c983fe55d0b…` に変わった。
原因は ZIP の中のメンバーの**日時が梱包した時刻**になっていること
(31 メンバーのうち 26 件が `2026-10-08 15:59:36`、5 件が `15:59:34`)。

**だから「取った書類が同じものか」を ZIP の sha256 で確かめてはいけない。**
この印は**メンバーの名前・CRC・展開後の大きさだけ**を、名前で並べ替えてから
まとめるので、梱包の時刻・並び・圧縮の強さに依らない。

    python3 fixtures/xbrl/zip_content_digest.py S100Z37J [S100Z4N9 ...]

**中身は展開しない**(中央ディレクトリの CRC を読むだけ)。通信はしない。
"""

import hashlib
import io
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from adapters.xbrl import edinet as E  # noqa: E402


def content_digest(zbytes):
    """``{メンバー名: (CRC, 展開後の大きさ)}`` を名前順に並べてまとめた sha256。"""

    z = zipfile.ZipFile(io.BytesIO(zbytes))
    items = sorted((i.filename, i.CRC, i.file_size) for i in z.infolist())
    text = "\n".join("%s %08x %d" % it for it in items)
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), len(items)


def main(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        raise SystemExit(__doc__)
    for doc in args:
        path = E.cache_path(doc)
        data = open(path, "rb").read()
        digest, n = content_digest(data)
        print("%-10s %9d バイト  メンバー %2d  中身の印 %s  (ZIP の sha256 %s ― **再現しない**)"
              % (doc, len(data), n, digest, hashlib.sha256(data).hexdigest()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
