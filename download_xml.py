# 简易脚本：优先读取 link.json，否则读取 link.txt，下载网页的 xml 文件，保存到 xml/ 目录
import os
import re
import json
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LINK_TXT = os.path.join(BASE_DIR, "link.txt")
LINK_JSON = os.path.join(BASE_DIR, "link.json")
XML_DIR = os.path.join(BASE_DIR, "xml")
os.makedirs(XML_DIR, exist_ok=True)

def read_links_from_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    return [ln for ln in lines if ln]

def read_links_from_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 确保都是字典并包含 title 和 link
    return [(item["title"], item["link"]) for item in data if "title" in item and "link" in item]

def safe_filename(name):
    """替换掉不能作为文件名的字符"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def extract_id(url):
    m = re.search(r"/sound/(\d+)", url)
    if not m:
        m = re.search(r"id=(\d+)", url)  # 兼容 ?id=12345 这种格式
    return m.group(1) if m else None

def download_xml(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()  # bytes

def main():
    use_json = False
    if os.path.exists(LINK_JSON):
        print("检测到 link.json，优先使用 JSON 文件。")
        data = read_links_from_json(LINK_JSON)
        # 转为 (title, link) 列表
        links = [(title, link) for title, link in data]
        use_json = True
    elif os.path.exists(LINK_TXT):
        links_raw = read_links_from_txt(LINK_TXT)
        # 转为 (默认标题, link)，标题先用序号
        links = [(f"{idx+1}", link) for idx, link in enumerate(links_raw)]
    else:
        print("未找到 link.json 或 link.txt")
        return

    total = len(links)
    success = 0
    for idx, (title, link) in enumerate(links):
        sid = extract_id(link)
        if not sid:
            print(f"[跳过] 第{idx}条无法提取id: {link}")
            continue
        new_url = f"https://www.missevan.com/sound/getdm?soundid={sid}"
        try:
            data = download_xml(new_url)
            if use_json:
                safe_title = safe_filename(title)
                out_path = os.path.join(XML_DIR, f"{safe_title}.xml")
            else:
                out_path = os.path.join(XML_DIR, f"{idx+1}-{sid}.xml")

            with open(out_path, "wb") as out:
                out.write(data)
            success += 1
        except urllib.error.HTTPError as e:
            print(f"[错误 HTTP] {new_url} -> {e.code}")
        except Exception as e:
            print(f"[错误] 下载 {new_url} 失败: {e}")

    if use_json:
        print(f"在 link.json 中读取到 {total} 个记录，成功下载 {success} 个 xml 文件。")
    else:
        print(f"在 link.txt 中读取到 {total} 个网址，成功下载 {success} 个 xml 文件。")

if __name__ == "__main__":
    main()