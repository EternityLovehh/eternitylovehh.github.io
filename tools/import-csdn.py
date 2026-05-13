#!/usr/bin/env python3
"""
Import all CSDN blog posts of a given user into this Hexo site.

Usage:
    pip3 install --user requests beautifulsoup4 markdownify
    python3 scripts/import-csdn.py --username <csdn_user>          # full import
    python3 scripts/import-csdn.py --username <csdn_user> --dry-run
    python3 scripts/import-csdn.py --username <csdn_user> --limit 1
    python3 scripts/import-csdn.py --username <csdn_user> --overwrite

Output:
    source/_posts/<title>.md         (Hexo front matter + markdown body)
    source/images/posts/csdn-<id>-N.<ext>   (images downloaded locally)
"""
from __future__ import annotations

import argparse
import mimetypes
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_md

REPO = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO / "source" / "_posts"
IMAGES_DIR = REPO / "source" / "images" / "posts"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def list_posts(username: str, page_size: int = 40):
    """Yield every post dict from CSDN's home-api listing."""
    seen = 0
    page = 1
    while True:
        url = (
            "https://blog.csdn.net/community/home-api/v1/get-business-list"
            f"?page={page}&size={page_size}&businessType=blog&username={username}"
        )
        r = requests.get(
            url,
            headers={"User-Agent": UA, "Referer": f"https://blog.csdn.net/{username}"},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 200:
            raise RuntimeError(f"home-api error: {data}")
        rows = data.get("data", {}).get("list") or []
        if not rows:
            return
        for row in rows:
            yield row
            seen += 1
        total = data["data"].get("total", 0)
        if seen >= total or len(rows) < page_size:
            return
        page += 1
        time.sleep(0.4)


def fetch_post(url: str, fallback_date: str | None = None):
    """Return dict with title/date/categories/tags and the soup of the body div."""
    r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    title_el = (
        soup.find("h1", id="articleContentId")
        or soup.find("h1", class_="title-article")
    )
    title = title_el.get_text(strip=True) if title_el else None

    # Prefer the API's postTime; HTML's `span.time` shows "最新推荐" (recommended) time, not publish time.
    date = fallback_date
    if not date:
        date_el = soup.find("span", class_="time") or soup.find("span", class_="time-style")
        if date_el:
            m = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", date_el.get_text())
            if m:
                date = m.group(1)

    # Tags: .tags-box / .blog-tags-box hold tag anchors. Skip the user-profile anchor and strip leading #.
    tags = []
    seen_tags = set()
    for a in soup.select(".tags-box a.tag-link-new, .blog-tags-box a.tag-link-new"):
        text = a.get_text(strip=True).lstrip("#").strip()
        if text and text not in seen_tags:
            seen_tags.add(text)
            tags.append(text)

    # Categories: each .column-group .column-group-item carries one column; clean name is in .tit
    categories = []
    seen_cats = set()
    for item in soup.select(".column-group .column-group-item"):
        tit = item.select_one(".tit")
        name = tit.get_text(strip=True) if tit else None
        if not name:
            link = item.select_one("a.item-target[title]")
            if link:
                name = link.get("title", "").strip()
        if name and name not in seen_cats:
            seen_cats.add(name)
            categories.append(name)

    body = soup.find("div", id="content_views") or soup.find(
        "div", class_="markdown_views"
    )
    if body is None:
        raise RuntimeError(f"no content_views in {url}")

    # Strip CSDN-injected junk that should not land in markdown
    junk_selectors = [
        ".copy-content",
        ".article-copyright",
        ".hide-article-box",
        ".csdn-side-toolbar",
        ".csdn-common-logo",
        ".article-source-link",
        ".aside-box",
        ".recommend-box",
        ".blog_extension",
        "script",
        "style",
    ]
    for sel in junk_selectors:
        for el in body.select(sel):
            el.decompose()

    return {
        "title": title,
        "date": date,
        "categories": categories,
        "tags": tags,
        "body": body,
    }


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\n\r\t]+', "_", name).strip().strip(".")
    return cleaned or "untitled"


def ext_from_url_or_ct(url: str, content_type: str) -> str:
    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"):
        return ext
    if content_type:
        guess = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ""
        if guess == ".jpe":
            guess = ".jpg"
        return guess or ".png"
    return ".png"


def download_image(url: str, dest_basename: str) -> Path:
    # IMPORTANT: no Referer — CSDN/简书 hot-link rules ignore us if Referer is absent.
    r = requests.get(url, headers={"User-Agent": UA}, timeout=25, stream=True)
    r.raise_for_status()
    ext = ext_from_url_or_ct(url, r.headers.get("content-type", ""))
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    target = IMAGES_DIR / f"{dest_basename}{ext}"
    with open(target, "wb") as f:
        for chunk in r.iter_content(64 * 1024):
            if chunk:
                f.write(chunk)
    return target


def rewrite_images(body, slug_prefix: str):
    """Download every external <img> and rewrite src to a local path."""
    idx = 0
    for img in body.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src or not src.startswith(("http://", "https://")):
            continue
        idx += 1
        try:
            target = download_image(src, f"{slug_prefix}-{idx}")
            img["src"] = f"/images/posts/{target.name}"
            for attr in ("data-src", "data-original", "srcset"):
                if img.has_attr(attr):
                    del img[attr]
            print(f"    img: {src[:70]}{'…' if len(src) > 70 else ''}  ->  {target.name}")
        except Exception as e:
            print(f"    [warn] image fetch failed: {src[:80]}  ({e})", file=sys.stderr)


def code_language(el) -> str:
    """Tell markdownify which language to fence."""
    code = el.find("code") if el.name == "pre" else el
    if not code:
        return ""
    for cls in code.get("class", []) or []:
        if cls.startswith("language-"):
            return cls[len("language-") :]
    return ""


def yaml_escape(s: str) -> str:
    # Quote if contains characters that confuse YAML's default scalar
    if re.search(r'[:#\[\]{},&*?!|>%@`"]', s) or s.strip() != s:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def build_front_matter(meta: dict) -> str:
    lines = ["---", f"title: {yaml_escape(meta['title'])}"]
    if meta.get("date"):
        lines.append(f"date: {meta['date']}")
    if meta.get("categories"):
        lines.append("categories:")
        for c in meta["categories"]:
            lines.append(f"  - {yaml_escape(c)}")
    if meta.get("tags"):
        lines.append("tags:")
        for t in meta["tags"]:
            lines.append(f"  - {yaml_escape(t)}")
    lines += ["---", ""]
    return "\n".join(lines)


def import_post(post_url: str, article_id: str, overwrite: bool, post_time: str | None = None) -> bool:
    meta = fetch_post(post_url, fallback_date=post_time)
    if not meta["title"]:
        print(f"[skip] no title for {post_url}", file=sys.stderr)
        return False

    fname = POSTS_DIR / (sanitize_filename(meta["title"]) + ".md")
    if fname.exists() and not overwrite:
        print(f"[skip] exists: {fname.name}  (--overwrite to replace)")
        return False

    rewrite_images(meta["body"], slug_prefix=f"csdn-{article_id}")

    body_md = html_to_md(
        str(meta["body"]),
        heading_style="ATX",
        bullets="-",
        code_language_callback=code_language,
    ).strip() + "\n"

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    fname.write_text(build_front_matter(meta) + body_md, encoding="utf-8")
    print(f"[ok] {fname.name}  ({len(body_md):,} bytes)")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Import CSDN posts into Hexo source/_posts/")
    ap.add_argument("--username", required=True, help="CSDN username (in your profile URL)")
    ap.add_argument("--limit", type=int, default=0, help="only process first N posts")
    ap.add_argument("--overwrite", action="store_true", help="overwrite existing files")
    ap.add_argument("--dry-run", action="store_true", help="list only, don't fetch or write")
    args = ap.parse_args()

    processed = 0
    written = 0
    for row in list_posts(args.username):
        url = row.get("url") or row.get("articleUrl")
        title = row.get("title") or row.get("articleTitle")
        if not url:
            continue
        article_id = url.rstrip("/").split("/")[-1]
        if args.dry_run:
            print(f"[dry] {article_id}  {title}  {url}")
        else:
            try:
                ok = import_post(
                    url,
                    article_id,
                    overwrite=args.overwrite,
                    post_time=row.get("postTime"),
                )
                if ok:
                    written += 1
            except Exception as e:
                print(f"[err] {url}: {e}", file=sys.stderr)
            time.sleep(0.5)
        processed += 1
        if args.limit and processed >= args.limit:
            break

    if args.dry_run:
        print(f"\ndry-run done. listed {processed} posts.")
    else:
        print(f"\ndone. processed={processed} written={written}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
