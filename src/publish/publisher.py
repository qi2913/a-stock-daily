"""Publisher - Output content to various formats and platforms."""
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
# Project root is 2 levels up from src/publish/
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def ensure_output_dirs():
    """Create output directory structure."""
    dirs = [
        OUTPUT_DIR,
        os.path.join(OUTPUT_DIR, "daily"),
        os.path.join(OUTPUT_DIR, "weekly"),
        os.path.join(OUTPUT_DIR, "fund"),
        os.path.join(OUTPUT_DIR, "sector"),
        os.path.join(OUTPUT_DIR, "site"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def save_markdown(content: str, filename: str, category: str = "daily") -> str:
    """Save content as markdown file. Returns file path."""
    ensure_output_dirs()
    filepath = os.path.join(OUTPUT_DIR, category, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def generate_html(content: str, title: str = "A股市场分析") -> str:
    """Convert markdown to simple HTML page with SEO metadata."""
    # Simple markdown to HTML conversion
    html_content = _md_to_html(content)
    
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{title} - AI自动生成的A股市场分析报告">
    <meta name="keywords" content="A股,股票,基金,市场分析,投资,复盘">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6;
               color: #333; background: #fafafa; }}
        h1 {{ border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;
                   font-size: 0.85em; color: #999; }}
        .highlight {{ background: #fff3cd; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
    return html_template.format(title=title, html_content=html_content)


def save_html(content: str, filename: str, category: str = "daily", title: str = "A股市场分析") -> str:
    """Save content as HTML file. Returns file path."""
    ensure_output_dirs()
    html = generate_html(content, title)
    filepath = os.path.join(OUTPUT_DIR, "site", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath


def generate_site_index(articles: List[Dict[str, str]]) -> str:
    """Generate index.html with links to all articles."""
    links = ""
    for a in sorted(articles, key=lambda x: x.get("date", ""), reverse=True):
        links += f'<li><a href="{a["file"]}">{a["date"]} - {a["title"]}</a></li>\n'
    
    index_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="AI自动生成的A股市场分析报告 - 每日更新">
    <meta name="keywords" content="A股,股票分析,市场复盘,投资参考">
    <title>A股每日复盘 - AI智能分析</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; 
               padding: 20px; background: #fafafa; }}
        h1 {{ color: #e74c3c; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 10px; border-bottom: 1px solid #eee; }}
        li:hover {{ background: #f0f0f0; }}
        a {{ text-decoration: none; color: #2c3e50; }}
        a:hover {{ color: #e74c3c; }}
        .footer {{ margin-top: 40px; color: #999; font-size: 0.85em; }}
    </style>
</head>
<body>
    <h1>📊 A股每日复盘</h1>
    <p>AI自动生成的市场分析报告，每日更新。</p>
    <ul>
{links}
    </ul>
    <div class="footer">
        <p>由 AI Agent 自动生成 | 仅供参考，不构成投资建议</p>
    </div>
</body>
</html>"""
    return index_html.format(links=links)


def publish_to_github_pages(commit_message: Optional[str] = None) -> bool:
    """Publish output/site/ to GitHub Pages via git push."""
    site_dir = os.path.join(OUTPUT_DIR, "site")
    if not os.path.exists(site_dir):
        return False
    
    if commit_message is None:
        commit_message = f"Auto publish: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    try:
        subprocess.run(["git", "add", "output/site/"], check=True, cwd=HERE)
        subprocess.run(["git", "commit", "-m", commit_message], check=True, cwd=HERE)
        subprocess.run(["git", "push"], check=True, cwd=HERE)
        return True
    except subprocess.CalledProcessError:
        return False


def _md_to_html(md: str) -> str:
    """Simple markdown to HTML conversion."""
    lines = md.split('\n')
    html_lines = []
    in_paragraph = False
    
    for line in lines:
        stripped = line.strip()
        
        # Headers
        if stripped.startswith('# '):
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            html_lines.append(f'<h1>{stripped[2:]}</h1>')
        elif stripped.startswith('## '):
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            html_lines.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith('### '):
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            html_lines.append(f'<h3>{stripped[4:]}</h3>')
        # Horizontal rule
        elif stripped == '---':
            if in_paragraph: html_lines.append('</p>'); in_paragraph = False
            html_lines.append('<hr>')
        # Bold
        elif '**' in stripped:
            import re
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', stripped)
            html_lines.append(f'<p>{line}</p>')
        # Emoji + text lines
        elif stripped.startswith('##') or stripped.startswith('#'):
            pass  # already handled
        elif stripped:
            if not in_paragraph:
                html_lines.append('<p>')
                in_paragraph = True
            html_lines.append(f'{stripped}<br>')
        else:
            if in_paragraph:
                html_lines.append('</p>')
                in_paragraph = False
    
    if in_paragraph:
        html_lines.append('</p>')
    
    html_lines.append('<div class="footer"><p>由 AI Agent 自动生成 | 仅供参考，不构成投资建议</p></div>')
    return '\n'.join(html_lines)
