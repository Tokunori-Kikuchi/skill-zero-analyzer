#!/usr/bin/env python3
"""
分析結果HTML生成スクリプト
完成したドキュメントフォーマットを他の参加者のanalysis_result.txtにも適用
"""

import os
import re
from pathlib import Path

def read_template(template_path):
    """HTMLテンプレートを読み込み"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_analysis_result(result_path):
    """analysis_result.txtファイルを解析して内容を抽出"""
    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 参加者名を抽出
    name_match = re.search(r'([^@\s]+@[^\s]+|[^\s]+)さんへのアドバイス', content)
    name = name_match.group(1) if name_match else "参加者"

    # 各セクションの内容を抽出
    sections = {}

    # 現状の分析
    analysis_match = re.search(r'\*\*現状の分析:\*\*\s*\n(.*?)(?=\*\*得意を活かせる道と副業の可能性:\*\*|$)', content, re.DOTALL)
    if analysis_match:
        sections['analysis_summary'] = analysis_match.group(1).strip()

    # 得意を活かせる道と副業の可能性
    proposal_match = re.search(r'\*\*得意を活かせる道と副業の可能性:\*\*\s*\n(.*?)(?=\*\*オフ会でのヒント:\*\*|$)', content, re.DOTALL)
    if proposal_match:
        sections['proposal_content'] = proposal_match.group(1).strip()

    # オフ会でのヒント
    tips_match = re.search(r'\*\*オフ会でのヒント:\*\*\s*\n(.*?)(?=\*\*リスク管理・注意点:\*\*|$)', content, re.DOTALL)
    if tips_match:
        sections['tips_content'] = tips_match.group(1).strip()

    # リスク管理・注意点
    risk_match = re.search(r'\*\*リスク管理・注意点:\*\*\s*\n(.*?)(?=$)', content, re.DOTALL)
    if risk_match:
        sections['risk_content'] = risk_match.group(1).strip()

    return name, sections

def convert_markdown_to_html(markdown_text):
    """MarkdownテキストをHTMLに変換"""
    if not markdown_text:
        return ""

    # 基本的なMarkdown変換
    html = markdown_text

    # 提案項目（【title】）を処理
    html = re.sub(r'【提案(\d+)】(.*?)(?=【提案\d+】|具体的なアクション:|$)',
                  r'<div class="proposal-item"><h3>提案\1</h3>\2</div>',
                  html, flags=re.DOTALL)

    # 強調（**text**）
    html = re.sub(r'\*\*(.*?)\*\*', r'<span class="highlight">\1</span>', html)

    # 具体的なアクションセクションを処理
    html = re.sub(r'具体的なアクション:\s*\n(.*?)(?=\n\n|\n\*\*|$)',
                  r'<div class="action-list"><h4>具体的なアクション:</h4><ul>\1</ul></div>',
                  html, flags=re.DOTALL)

    # 箇条書きの処理 - より確実な方法
    # まず、箇条書きの行を特定
    lines = html.split('\n')
    result_lines = []
    in_list = False
    list_items = []

    for line in lines:
        if line.strip().startswith('・'):
            # 箇条書きの開始
            if not in_list:
                in_list = True
            # 箇条書きの内容を抽出
            content = line.strip()[1:].strip()  # ・を除去
            list_items.append(f'<li>{content}</li>')
        else:
            # 箇条書き以外の行
            if in_list and list_items:
                # 箇条書きを終了してulタグで囲む
                result_lines.append(f'<ul>{"".join(list_items)}</ul>')
                list_items = []
                in_list = False
            result_lines.append(line)

    # 最後の箇条書きを処理
    if in_list and list_items:
        result_lines.append(f'<ul>{"".join(list_items)}</ul>')

    html = '\n'.join(result_lines)

    # 段落処理
    html = re.sub(r'\n\n', r'</p><p>', html)

    # 改行を処理
    html = re.sub(r'\n', r'<br>', html)

    # 段落タグで囲む
    html = f'<p>{html}</p>'

    return html

def generate_html_result(name, sections, template):
    """HTML結果を生成"""
    html = template

    # プレースホルダーを置換
    html = html.replace('{{NAME}}', name)

    # 各セクションの内容をHTMLに変換して置換
    if 'analysis_summary' in sections:
        analysis_html = convert_markdown_to_html(sections['analysis_summary'])
        html = html.replace('{{ANALYSIS_SUMMARY}}', analysis_html)

    if 'proposal_content' in sections:
        proposal_html = convert_markdown_to_html(sections['proposal_content'])
        html = html.replace('{{PROPOSAL_CONTENT}}', proposal_html)

    if 'tips_content' in sections:
        tips_html = convert_markdown_to_html(sections['tips_content'])
        html = html.replace('{{TIPS_CONTENT}}', tips_html)

    if 'risk_content' in sections:
        risk_html = convert_markdown_to_html(sections['risk_content'])
        html = html.replace('{{RISK_CONTENT}}', risk_html)

    return html

def main():
    """メイン処理"""
    output_dir = Path('output')
    template_path = output_dir / 'analysis_result_template.html'

    # テンプレートを読み込み
    template = read_template(template_path)

    # analysis_result.txtファイルを検索
    result_files = list(output_dir.glob('*_analysis_result.txt'))

    print(f"処理対象ファイル数: {len(result_files)}")

    for result_file in result_files:
        try:
            print(f"処理中: {result_file.name}")

            # 分析内容を解析
            name, sections = parse_analysis_result(result_file)

            # HTML結果を生成
            html_result = generate_html_result(name, sections, template)

            # 結果ファイル名を生成
            result_filename = result_file.name.replace('_analysis_result.txt', '_analysis_result.html')
            result_path = output_dir / result_filename

            # HTMLファイルを保存
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(html_result)

            print(f"生成完了: {result_filename}")

        except Exception as e:
            print(f"エラー ({result_file.name}): {e}")

    print("すべての処理が完了しました。")

if __name__ == "__main__":
    main()