"""共通HTTPユーティリティ（標準ライブラリのみ・外部依存ゼロ）"""
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "gaikoku-policy-checker-bot/1.0 (public-interest data dashboard; polite crawler)"
# 一部の府省サイト（CloudFront）はbot UAのHTMLを拒否するためブラウザUAでフォールバックする
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

# python.org版のmacOS Pythonは証明書ストアが空のことがあるため、
# OS既知のCAバンドルにフォールバックする（Linux/CIでも同様に解決できる）
_CA_CANDIDATES = (
    "/etc/ssl/cert.pem",
    "/etc/ssl/certs/ca-certificates.crt",
    "/opt/homebrew/etc/ca-certificates/cert.pem",
)


def _ssl_context():
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats()["x509_ca"] == 0:
        for path in _CA_CANDIDATES:
            if os.path.exists(path):
                ctx.load_verify_locations(path)
                break
    return ctx


_CTX = _ssl_context()


def http_get_json(url, *, retries=3, delay=1.0, timeout=60, cache_key=None, use_cache=False):
    """JSONをGETする。礼儀としてリクエスト間に delay 秒待つ。

    cache_key を渡すと cache/ に生レスポンスを保存し、
    use_cache=True なら再リクエストせずそれを返す（開発時用）。
    """
    if use_cache and cache_key:
        p = CACHE_DIR / cache_key
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    last_err = None
    for attempt in range(retries):
        # CloudFront等がbot UAのレスポンスをHTMLで返す（=JSONパース失敗）ことがあるため、
        # 試行ごとにbot UA→ブラウザUAへ切り替えてフォールバックする
        ua = UA if attempt == 0 else BROWSER_UA
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
                data = json.loads(r.read().decode("utf-8"))
            if cache_key:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                (CACHE_DIR / cache_key).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            time.sleep(delay)
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
            last_err = e
            time.sleep(delay * (attempt + 2))
    raise RuntimeError(f"GET failed after {retries} tries: {url}: {last_err}")


def http_get_text(url, *, retries=3, delay=1.0, timeout=60):
    """HTMLページを取得し、タグ除去済みの素のテキストを返す（証跡文字列の照合用）"""
    import html as html_mod
    import re
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
                raw = r.read().decode("utf-8", errors="replace")
            text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S)
            text = html_mod.unescape(re.sub(r"<[^>]+>", " ", text))
            time.sleep(delay)
            return re.sub(r"\s+", "", text)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            time.sleep(delay * (attempt + 2))
    raise RuntimeError(f"GET failed after {retries} tries: {url}: {last_err}")


def http_get_raw(url, *, ua=BROWSER_UA, retries=2, delay=0.6, timeout=40):
    """生のHTML文字列を返す（404等は None）。プレスリリースのタイトル・本文解析用。"""
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
                raw = r.read().decode("utf-8", errors="replace")
            time.sleep(delay)
            return raw
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last_err = e
            time.sleep(delay * (attempt + 2))
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(delay * (attempt + 2))
    return None


def url_alive(url, timeout=20):
    """出典URLの生存確認。HEADを拒否するサイトがあるのでGETにフォールバック。"""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
                if 200 <= r.status < 400:
                    return True
        except Exception:
            continue
    return False
