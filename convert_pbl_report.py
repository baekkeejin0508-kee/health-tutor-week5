import os
import sys
import re
import subprocess
import shutil
from pathlib import Path

# UTF-8 출력 설정
sys.stdout.reconfigure(encoding="utf-8")

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

MD_FILE = Path("RAG_ON_OFF_PBL_고도화_비교검증보고서.md")
HTML_FILE = Path("RAG_ON_OFF_PBL_고도화_비교검증보고서.html")
PDF_FILE = Path("RAG_ON_OFF_PBL_고도화_비교검증보고서.pdf")
DOCX_FILE = Path("RAG_ON_OFF_PBL_고도화_비교검증보고서.docx")
HWP_FILE = Path("RAG_ON_OFF_PBL_고도화_비교검증보고서.hwp")
DOWNLOADS_DIR = Path("C:/Users/user/Downloads")

# -------------------------------------------------------------
# 1. HTML & PDF 생성 로직
# -------------------------------------------------------------
def markdown_to_academic_html(md_text: str) -> str:
    def inline_fmt(text: str) -> str:
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text

    lines = md_text.splitlines()
    html_parts = []
    
    in_code_block = False
    code_block_lines = []
    code_block_type = ""
    
    in_table = False
    table_lines = []

    def flush_table():
        nonlocal in_table, table_lines
        if not in_table or not table_lines:
            return ""
        t_html = ['<div class="table-container"><table>']
        header_cells = [c.strip() for c in table_lines[0].split('|')[1:-1]]
        t_html.append('<thead><tr>')
        for h in header_cells:
            t_html.append(f'<th>{inline_fmt(h)}</th>')
        t_html.append('</tr></thead><tbody>')
        for r in table_lines[2:]:
            cells = [c.strip() for c in r.split('|')[1:-1]]
            t_html.append('<tr>')
            for c in cells:
                t_html.append(f'<td>{inline_fmt(c)}</td>')
            t_html.append('</tr>')
        t_html.append('</tbody></table></div>')
        in_table = False
        table_lines = []
        return "".join(t_html)

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_content = "\n".join(code_block_lines)
                is_rag_on = "🟢" in code_block_type or "RAG ON" in code_block_type or "Agent B" in code_block_type or "최신 PBL" in code_block_type
                badge_class = "rag-on-box" if is_rag_on else "rag-off-box"
                agent_label = '<span class="agent-pill on-pill">🟢 Agent B (RAG ON) 지식 검색 응답</span>' if is_rag_on else '<span class="agent-pill off-pill">⚪ Agent A (RAG OFF) 순수 LLM 응답</span>'
                if "최종 PBL" in code_block_type or "활동작성" in code_block_type:
                    badge_class = "rag-on-box"
                    agent_label = '<span class="agent-pill on-pill">🏥 최종 병원 임상 PBL 모의실습 시나리오</span>'
                html_parts.append(
                    f'<div class="response-card {badge_class}">'
                    f'<div class="card-header-bar">{agent_label}</div>'
                    f'<pre><code>{code_content}</code></pre>'
                    f'</div>'
                )
                code_block_lines = []
            else:
                if in_table:
                    html_parts.append(flush_table())
                in_code_block = True
                code_block_lines = []
                code_block_type = lines[i-1] if i > 0 else ""
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            i += 1
            continue

        if line.startswith("|") and line.endswith("|"):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            html_parts.append(flush_table())

        if line.startswith("> "):
            quote_text = line[2:].strip()
            html_parts.append(f'<div class="callout-quote">{inline_fmt(quote_text)}</div>')
            i += 1
            continue

        if not line.strip():
            i += 1
            continue

        if line.strip() == "---":
            html_parts.append('<hr class="section-divider"/>')
            i += 1
            continue

        if line.startswith("# "):
            title_text = line[2:].strip()
            html_parts.append(
                f'<header class="report-header">'
                f'<div class="badge-tag">🎓 대학원 학술 검증 보고서 (PBL 고도화 실증 분석)</div>'
                f'<h1 class="main-title">{title_text}</h1>'
                f'</header>'
            )
            i += 1
            continue

        if line.startswith("## "):
            h2_text = line[3:].strip()
            html_parts.append(f'<h2 class="section-h2">{h2_text}</h2>')
            i += 1
            continue

        if line.startswith("### "):
            h3_text = line[4:].strip()
            html_parts.append(f'<div class="test-case-wrapper"><h3 class="test-h3"><span class="test-pill">CASE</span> {h3_text}</h3>')
            i += 1
            continue

        if line.startswith("#### "):
            h4_text = line[5:].strip()
            if "Agent A" in h4_text or "RAG OFF" in h4_text:
                html_parts.append(f'<div class="agent-title agent-off-title"><span class="agent-icon">⚪</span> {inline_fmt(h4_text)}</div>')
            elif "Agent B" in h4_text or "RAG ON" in h4_text:
                html_parts.append(f'<div class="agent-title agent-on-title"><span class="agent-icon">🟢</span> {inline_fmt(h4_text)}</div>')
            else:
                html_parts.append(f'<h4 class="analysis-h4">{inline_fmt(h4_text)}</h4>')
            i += 1
            continue

        if line.startswith("- **질문**:") or line.startswith("> **질문**:"):
            q_text = re.sub(r'^(\-|\>)\s+\*\*질문\*\*:\s*', '', line).strip()
            html_parts.append(f'<div class="question-box"><span class="q-badge">질문 (Prompt)</span> {inline_fmt(q_text)}</div>')
            i += 1
            continue

        if line.startswith("- **검증 목표") or line.startswith("> **검증 목표"):
            exp_text = re.sub(r'^(\-|\>)\s+\*\*검증 목표( 및 기대 행동)?\*\*:\s*', '', line).strip()
            html_parts.append(f'<div class="expected-box"><span class="exp-badge">검증 목표 & 기대 행동</span> {inline_fmt(exp_text)}</div>')
            i += 1
            continue

        if line.startswith("- ") or line.startswith("* "):
            item_text = line[2:].strip()
            html_parts.append(f'<div class="bullet-item"><span class="bullet-dot">▪</span> {inline_fmt(item_text)}</div>')
            i += 1
            continue

        m_num = re.match(r'^(\d+)\.\s+(.*)', line)
        if m_num:
            num = m_num.group(1)
            item_text = m_num.group(2)
            html_parts.append(f'<div class="num-item"><span class="num-badge">{num}</span> {inline_fmt(item_text)}</div>')
            i += 1
            continue

        html_parts.append(f'<p class="general-p">{inline_fmt(line)}</p>')
        i += 1

    if in_table:
        html_parts.append(flush_table())

    body_html = "\n".join(html_parts)

    full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>특성화고 보건간호 AI 보건튜터 PBL 고도화 및 RAG ON vs OFF 종합 실증 보고서</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&family=Noto+Serif+KR:wght@600;700&display=swap');

  @page {{
    size: A4 portrait;
    margin: 15mm 15mm 16mm 15mm;
    @bottom-center {{
      content: "- " counter(page) " -";
      font-size: 8.5pt;
      font-family: 'Pretendard', sans-serif;
      color: #64748b;
    }}
    @top-right {{
      content: "Healthcare-nquiry AI 보건튜터 PBL 고도화 실증 보고서";
      font-size: 7.5pt;
      font-family: 'Pretendard', sans-serif;
      color: #94a3b8;
    }}
  }}

  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  body {{
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Malgun Gothic", sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.65;
    font-size: 9.3pt;
    margin: 0;
    padding: 0;
  }}

  .report-header {{
    text-align: center;
    border-bottom: 3px double #0284c7;
    padding-bottom: 20px;
    margin-bottom: 22px;
    background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%);
    padding: 24px 16px 18px 16px;
    border-radius: 8px;
    border: 1px solid #e0f2fe;
  }}

  .badge-tag {{
    display: inline-block;
    background: #0284c7;
    color: #ffffff;
    font-size: 8.5pt;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 9999px;
    margin-bottom: 12px;
    letter-spacing: 0.5px;
  }}

  .main-title {{
    font-size: 16pt;
    font-weight: 800;
    color: #0f172a;
    margin: 6px 0 0 0;
    line-height: 1.38;
    word-break: keep-all;
  }}

  .callout-quote {{
    background: #f8fafc;
    border-left: 4px solid #0284c7;
    padding: 8px 14px;
    color: #475569;
    font-size: 9.2pt;
    margin: 8px 0 16px 0;
    border-radius: 0 4px 4px 0;
  }}

  .section-h2 {{
    font-size: 12.5pt;
    font-weight: 700;
    color: #0f172a;
    background: #f1f5f9;
    padding: 8px 14px;
    border-left: 5px solid #0284c7;
    border-radius: 4px;
    margin-top: 26px;
    margin-bottom: 14px;
    page-break-after: avoid;
  }}

  .test-case-wrapper {{
    page-break-inside: avoid;
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 22px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
  }}

  .test-h3 {{
    font-size: 11.5pt;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1.5px solid #e2e8f0;
    display: flex;
    align-items: center;
  }}

  .test-pill {{
    background: #0f172a;
    color: #38bdf8;
    font-size: 7.5pt;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 4px;
    margin-right: 8px;
    letter-spacing: 0.5px;
  }}

  .question-box {{
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 4px solid #2563eb;
    padding: 9px 14px;
    border-radius: 4px;
    font-size: 9.3pt;
    color: #1e3a8a;
    margin-bottom: 10px;
    font-weight: 500;
  }}

  .q-badge {{
    background: #2563eb;
    color: white;
    font-size: 7.5pt;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    margin-right: 6px;
  }}

  .expected-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #64748b;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 9pt;
    color: #334155;
    margin-bottom: 14px;
    line-height: 1.55;
  }}

  .exp-badge {{
    background: #64748b;
    color: white;
    font-size: 7.5pt;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    margin-right: 6px;
  }}

  .agent-title {{
    font-size: 9.5pt;
    font-weight: 700;
    margin-top: 14px;
    margin-bottom: 6px;
    padding: 4px 10px;
    border-radius: 4px;
    display: inline-block;
  }}

  .agent-off-title {{
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #cbd5e1;
  }}

  .agent-on-title {{
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
  }}

  .response-card {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    margin-bottom: 12px;
    overflow: hidden;
    page-break-inside: avoid;
  }}

  .card-header-bar {{
    padding: 5px 12px;
    font-size: 8.2pt;
    font-weight: 700;
    border-bottom: 1px solid #e2e8f0;
  }}

  .rag-off-box {{
    border-left: 4.5px solid #64748b;
  }}
  .rag-off-box .card-header-bar {{
    background: #f8fafc;
    color: #475569;
  }}

  .rag-on-box {{
    border-left: 4.5px solid #10b981;
    background: #fafdfb;
  }}
  .rag-on-box .card-header-bar {{
    background: #ecfdf5;
    color: #065f46;
  }}

  .agent-pill {{
    font-size: 8pt;
    font-weight: 700;
  }}

  .response-card pre {{
    margin: 0;
    padding: 10px 14px;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: inherit;
    font-size: 8.8pt;
    line-height: 1.6;
    color: #1e293b;
  }}

  .analysis-h4 {{
    font-size: 10pt;
    font-weight: 700;
    color: #0369a1;
    margin: 16px 0 8px 0;
    page-break-after: avoid;
  }}

  .table-container {{
    margin: 10px 0 16px 0;
    page-break-inside: avoid;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 8.6pt;
    text-align: left;
    border: 1px solid #cbd5e1;
    background: #ffffff;
  }}

  th {{
    background: #f8fafc;
    color: #1e293b;
    font-weight: 700;
    padding: 7px 10px;
    border: 1px solid #cbd5e1;
    font-size: 8.8pt;
  }}

  td {{
    padding: 7px 10px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
    line-height: 1.5;
  }}

  tr:nth-child(even) {{
    background-color: #f8fafc;
  }}

  .section-divider {{
    border: 0;
    border-top: 1.5px dashed #cbd5e1;
    margin: 22px 0;
  }}

  .bullet-item {{
    font-size: 9.2pt;
    margin: 4px 0;
    color: #334155;
    padding-left: 4px;
  }}

  .bullet-dot {{
    color: #0284c7;
    font-weight: bold;
    margin-right: 6px;
  }}

  .num-item {{
    font-size: 9.2pt;
    margin: 6px 0;
    color: #1e293b;
    padding-left: 4px;
  }}

  .num-badge {{
    display: inline-block;
    background: #0284c7;
    color: white;
    font-size: 7.5pt;
    font-weight: bold;
    width: 16px;
    height: 16px;
    text-align: center;
    line-height: 16px;
    border-radius: 50%;
    margin-right: 6px;
  }}

  code {{
    background: #f1f5f9;
    padding: 1.5px 5px;
    border-radius: 3px;
    font-family: Consolas, monospace;
    font-size: 8.5pt;
    color: #0f172a;
    border: 1px solid #e2e8f0;
  }}

  strong {{
    font-weight: 700;
    color: #0f172a;
  }}

  .general-p {{
    margin: 6px 0;
    font-size: 9.3pt;
    line-height: 1.65;
    color: #334155;
  }}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""
    return full_html


# -------------------------------------------------------------
# 2. DOCX & HWP 생성 로직
# -------------------------------------------------------------
def set_cell_background(cell, color_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="CCCCCC"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def build_docx():
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f_run = f_p.add_run("특성화고 보건간호 RAG 실증 보고서 (Healthcare-nquiry AI 보건튜터)")
        f_run.font.name = "맑은 고딕"
        f_run.font.size = Pt(8.5)
        f_run.font.color.rgb = RGBColor(148, 163, 184)

    style = doc.styles['Normal']
    font = style.font
    font.name = '맑은 고딕'
    font.size = Pt(9.5)
    font.color.rgb = RGBColor(30, 41, 59)

    md_text = MD_FILE.read_text(encoding="utf-8")
    lines = md_text.splitlines()

    i = 0
    in_code_block = False
    code_block_lines = []
    code_block_type = ""
    in_table = False
    table_lines = []

    def flush_table():
        nonlocal in_table, table_lines
        if not in_table or not table_lines:
            return
        headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
        num_cols = len(headers)
        if num_cols == 0:
            in_table = False
            table_lines = []
            return

        table = doc.add_table(rows=0, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table, "CBD5E1")

        hdr_row = table.add_row()
        for idx, h_text in enumerate(headers):
            cell = hdr_row.cells[idx]
            set_cell_background(cell, "F1F5F9")
            set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
            cell_p = cell.paragraphs[0]
            cell_p.paragraph_format.space_before = Pt(2)
            cell_p.paragraph_format.space_after = Pt(2)
            run = cell_p.add_run(h_text)
            run.font.name = "맑은 고딕"
            run.font.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(15, 23, 42)

        for r_line in table_lines[2:]:
            cells_text = [c.strip() for c in r_line.split('|')[1:-1]]
            if len(cells_text) < num_cols:
                cells_text += [""] * (num_cols - len(cells_text))
            row = table.add_row()
            for idx, c_text in enumerate(cells_text[:num_cols]):
                cell = row.cells[idx]
                set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
                cell_p = cell.paragraphs[0]
                cell_p.paragraph_format.space_before = Pt(2)
                cell_p.paragraph_format.space_after = Pt(2)
                parts = re.split(r'(\*\*[^*]+\*\*)', c_text)
                for part in parts:
                    if part.startswith("**") and part.endswith("**"):
                        run = cell_p.add_run(part[2:-2])
                        run.font.bold = True
                    else:
                        clean_part = part.replace("`", "")
                        run = cell_p.add_run(clean_part)
                    run.font.name = "맑은 고딕"
                    run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(51, 65, 85)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)
        in_table = False
        table_lines = []

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_content = "\n".join(code_block_lines)
                is_rag_on = "🟢" in code_block_type or "RAG ON" in code_block_type or "최신 PBL" in code_block_type or "활동작성" in code_block_type
                
                box_tbl = doc.add_table(rows=1, cols=1)
                box_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = box_tbl.cell(0, 0)
                bg_color = "ECFDF5" if is_rag_on else "F8FAFC"
                set_cell_background(cell, bg_color)
                set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
                
                cell_p = cell.paragraphs[0]
                tag_label = "[🟢 Agent B (RAG ON) 지식 검색 응답]\n" if is_rag_on else "[⚪ Agent A (RAG OFF) 순수 LLM 응답]\n"
                if "최종 PBL" in code_block_type or "활동작성" in code_block_type:
                    tag_label = "[🏥 최종 병원 임상 PBL 모의실습 시나리오]\n"
                tag_run = cell_p.add_run(tag_label)
                tag_run.font.name = "맑은 고딕"
                tag_run.font.bold = True
                tag_run.font.size = Pt(9)
                tag_run.font.color.rgb = RGBColor(6, 95, 70) if is_rag_on else RGBColor(71, 85, 105)

                body_run = cell_p.add_run(code_content)
                body_run.font.name = "맑은 고딕"
                body_run.font.size = Pt(8.8)
                body_run.font.color.rgb = RGBColor(30, 41, 59)

                doc.add_paragraph().paragraph_format.space_after = Pt(4)
                code_block_lines = []
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_block_lines = []
                code_block_type = lines[i-1] if i > 0 else ""
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        if line.startswith("|") and line.endswith("|"):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            flush_table()

        if not line.strip():
            i += 1
            continue

        if line.strip() == "---":
            i += 1
            continue

        if line.startswith("# "):
            title_text = line[2:].strip().replace("🩺 ", "")
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(title_text)
            run.font.name = "맑은 고딕"
            run.font.bold = True
            run.font.size = Pt(15.5)
            run.font.color.rgb = RGBColor(15, 23, 42)
            i += 1
            continue

        if line.startswith("> "):
            sub_text = line[2:].replace("**부제**:", "").strip().replace("**", "")
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(14)
            run = p.add_run(f"부제: {sub_text}")
            run.font.name = "맑은 고딕"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(100, 116, 139)
            i += 1
            continue

        if line.startswith("## "):
            h2_text = line[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(h2_text)
            run.font.name = "맑은 고딕"
            run.font.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(2, 132, 199)
            i += 1
            continue

        if line.startswith("### "):
            h3_text = line[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(h3_text)
            run.font.name = "맑은 고딕"
            run.font.bold = True
            run.font.size = Pt(10.5)
            run.font.color.rgb = RGBColor(15, 23, 42)
            i += 1
            continue

        if line.startswith("#### "):
            h4_text = line[5:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(h4_text)
            run.font.name = "맑은 고딕"
            run.font.bold = True
            run.font.size = Pt(10)
            if "Agent B" in h4_text or "RAG ON" in h4_text:
                run.font.color.rgb = RGBColor(5, 150, 105)
            elif "Agent A" in h4_text or "RAG OFF" in h4_text:
                run.font.color.rgb = RGBColor(100, 116, 139)
            else:
                run.font.color.rgb = RGBColor(3, 105, 161)
            i += 1
            continue

        if line.startswith("- **질문**:") or line.startswith("> **질문**:"):
            q_text = re.sub(r'^(\-|\>)\s+\*\*질문\*\*:\s*', '', line).strip()
            q_box = doc.add_table(rows=1, cols=1)
            q_box.alignment = WD_TABLE_ALIGNMENT.CENTER
            c = q_box.cell(0, 0)
            set_cell_background(c, "EFF6FF")
            set_cell_margins(c, top=80, bottom=80, left=140, right=140)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r_tag = p.add_run("질문 (Prompt): ")
            r_tag.font.bold = True
            r_tag.font.color.rgb = RGBColor(37, 99, 235)
            r_txt = p.add_run(q_text)
            r_txt.font.color.rgb = RGBColor(30, 58, 138)
            doc.add_paragraph().paragraph_format.space_after = Pt(3)
            i += 1
            continue

        if line.startswith("- **검증 목표") or line.startswith("> **검증 목표"):
            exp_text = re.sub(r'^(\-|\>)\s+\*\*검증 목표( 및 기대 행동)?\*\*:\s*', '', line).strip()
            e_box = doc.add_table(rows=1, cols=1)
            e_box.alignment = WD_TABLE_ALIGNMENT.CENTER
            c = e_box.cell(0, 0)
            set_cell_background(c, "F8FAFC")
            set_cell_margins(c, top=80, bottom=80, left=140, right=140)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r_tag = p.add_run("검증 목표 & 기대 행동: ")
            r_tag.font.bold = True
            r_tag.font.color.rgb = RGBColor(71, 85, 105)
            r_txt = p.add_run(exp_text)
            r_txt.font.color.rgb = RGBColor(51, 65, 85)
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
            i += 1
            continue

        if line.startswith("- ") or line.startswith("* "):
            item_text = line[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            parts = re.split(r'(\*\*[^*]+\*\*)', item_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.font.bold = True
                else:
                    r = p.add_run(part.replace("`", ""))
                r.font.name = "맑은 고딕"
                r.font.size = Pt(9.2)
            i += 1
            continue

        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        parts = re.split(r'(\*\*[^*]+\*\*)', line)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                r = p.add_run(part[2:-2])
                r.font.bold = True
            else:
                r = p.add_run(part.replace("`", ""))
            r.font.name = "맑은 고딕"
            r.font.size = Pt(9.2)
            r.font.color.rgb = RGBColor(51, 65, 85)
        i += 1

    if in_table:
        flush_table()

    doc.save(DOCX_FILE)
    print(f"🎉 Word 문서 생성 완료: {DOCX_FILE} ({DOCX_FILE.stat().st_size:,} bytes)")
    if DOWNLOADS_DIR.exists():
        shutil.copy(DOCX_FILE, DOWNLOADS_DIR / DOCX_FILE.name)
        print(f"📁 사용자 다운로드 폴더로 복사 완료: {DOWNLOADS_DIR / DOCX_FILE.name}")


def main():
    if not MD_FILE.exists():
        print(f"오류: {MD_FILE}을 찾을 수 없습니다.")
        return

    # 1. HTML 생성
    print("1. 학술 인쇄용 HTML 변환 중...")
    md_text = MD_FILE.read_text(encoding="utf-8")
    html_content = markdown_to_academic_html(md_text)
    HTML_FILE.write_text(html_content, encoding="utf-8")
    print(f"   -> HTML 생성 완료: {HTML_FILE}")

    # 2. PDF 변환 (Chrome Headless)
    browser_exe = None
    chrome_path = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
    edge_path = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if chrome_path.exists():
        browser_exe = str(chrome_path)
    elif edge_path.exists():
        browser_exe = str(edge_path)

    if browser_exe:
        print(f"2. 헤드리스 브라우저({Path(browser_exe).stem})를 통해 PDF 렌더링 중...")
        abs_html = HTML_FILE.resolve().as_uri()
        cmd = [
            browser_exe,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--run-all-compositor-stages-before-draw",
            f"--print-to-pdf={PDF_FILE.resolve()}",
            "--no-pdf-header-footer",
            abs_html
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and PDF_FILE.exists():
            print(f"   🎉 PDF 파일 생성 완료: {PDF_FILE} ({PDF_FILE.stat().st_size:,} bytes)")
            if DOWNLOADS_DIR.exists():
                shutil.copy(PDF_FILE, DOWNLOADS_DIR / PDF_FILE.name)
                print(f"   📁 사용자 다운로드 폴더로 복사 완료: {DOWNLOADS_DIR / PDF_FILE.name}")
        else:
            print("   PDF 변환 실패:", res.stderr.decode('utf-8', errors='ignore'))

    # 3. DOCX 생성
    print("3. 편집용 Word(.docx) 문서 생성 중...")
    build_docx()

    # 4. HWP 호환 문서 생성
    if HTML_FILE.exists():
        print("4. 편집용 한글(.hwp) 문서 생성 중...")
        HWP_FILE.write_bytes(HTML_FILE.read_bytes())
        print(f"   🎉 HWP 파일 생성 완료: {HWP_FILE} ({HWP_FILE.stat().st_size:,} bytes)")
        if DOWNLOADS_DIR.exists():
            shutil.copy(HWP_FILE, DOWNLOADS_DIR / HWP_FILE.name)
            print(f"   📁 사용자 다운로드 폴더로 복사 완료: {DOWNLOADS_DIR / HWP_FILE.name}")

if __name__ == "__main__":
    main()
