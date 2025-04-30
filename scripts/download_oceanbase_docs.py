"""
下载并处理OceanBase文档用于知识库。
"""
import os
import requests
from bs4 import BeautifulSoup
import markdown
from urllib.parse import urljoin

BASE_URL = "https://www.oceanbase.com/docs/enterprise-tutorials-cn-1000000001390092"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "oceanbase_docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_page(url):
    """获取页面内容"""
    response = requests.get(url)
    response.encoding = "utf-8"
    if response.status_code == 200:
        return response.text
    return None

def parse_links(html, base_url):
    """解析页面中的链接"""
    soup = BeautifulSoup(html, "html.parser")
    links = []

    menu_links = soup.select(".menu-list a, .toc a, .catalog a, .sidebar a")

    for link in menu_links:
        href = link.get("href")
        if href and isinstance(href, str) and not href.startswith("#") and not href.startswith("http"):
            full_url = urljoin(base_url, href)
            title = link.get_text(strip=True)
            links.append({"url": full_url, "title": title})

    return links

def extract_content(html):
    """提取页面主要内容"""
    soup = BeautifulSoup(html, "html.parser")
    content_area = soup.select_one(".doc-content, .main-content, article, .content")

    if content_area:
        return content_area.get_text(separator="\n")

    body = soup.body
    if body:
        return body.get_text(separator="\n")

    return ""

def main():
    """主函数"""
    print("开始下载OceanBase文档...")

    main_page = fetch_page(BASE_URL)
    if not main_page:
        print(f"无法获取主页: {BASE_URL}")
        return

    links = parse_links(main_page, BASE_URL)
    print(f"找到 {len(links)} 个文档页面")

    main_content = extract_content(main_page)
    with open(os.path.join(OUTPUT_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write(f"# OceanBase从入门到实践\n\n{main_content}")

    for i, link in enumerate(links):
        print(f"正在处理 ({i+1}/{len(links)}): {link['title']}")
        page_content = fetch_page(link["url"])

        if page_content:
            content = extract_content(page_content)
            filename = f"{i+1:03d}_{link['title'].replace('/', '_').replace(' ', '_')}.md"
            with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
                f.write(f"# {link['title']}\n\nURL: {link['url']}\n\n{content}")

    print("文档下载完成!")

if __name__ == "__main__":
    main()
