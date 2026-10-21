import os
import sys
import re
import shutil
from pathlib import Path

# UTF-8 출력 설정
sys.stdout.reconfigure(encoding="utf-8")

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

MD_FILE = Path("RAG_ON_OFF_비교검증보고서.md")
DOCX_FILE = Path("RAG_ON_OFF_비교검증보고서.docx")
HWP_FILE = Path("RAG_ON_OFF_비교검증보고서.hwp")
DOWNLOADS_DIR = Path("C:/Users/user/Downloads")

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

def build_docx_from_markdown():
    if not MD_FILE.exists():
        print(f"오류: {MD_FILE}을 찾을 수 없습니다.")
        return False

    doc = Document()

    # 페이지 여백 설정 (상하 20mm, 좌우 20mm)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        # 헤더/푸터 설정
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f_run = f_p.add_run("특성화고 보건간호 RAG 실증 보고서 (Healthcare-nquiry AI 보건튜터)")
        f_run.font.name = "맑은 고딕"
        f_run.font.size = Pt(8.5)
        f_run.font.color.rgb = RGBColor(148, 163, 184)

    # 기본 스타일 폰트 설정
    style = doc.styles['Normal']
    font = style.font
    font.name = '맑은 고딕'
    font.size = Pt(10)
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
        
        # 헤더
        headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
        num_cols = len(headers)
        if num_cols == 0:
            in_table = False
            table_lines = []
            return

        table = doc.add_table(rows=0, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table, "CBD5E1")

        # 헤더 행 추가
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

        # 데이터 행 추가
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
                
                # 볼드 인라인 처리
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

        # 코드 블록 처리
        if line.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_content = "\n".join(code_block_lines)
                is_rag_on = "🟢" in code_block_type or "RAG ON" in code_block_type
                
                # 표 1개짜리 카드 박스로 생성
                box_tbl = doc.add_table(rows=1, cols=1)
                box_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = box_tbl.cell(0, 0)
                bg_color = "ECFDF5" if is_rag_on else "F8FAFC"
                set_cell_background(cell, bg_color)
                set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
                
                cell_p = cell.paragraphs[0]
                tag_run = cell_p.add_run("[🟢 Agent B (RAG ON) 지식 검색 응답]\n" if is_rag_on else "[⚪ Agent A (RAG OFF) 순수 LLM 응답]\n")
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

        # 테이블 처리
        if line.startswith("|") and line.endswith("|"):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            flush_table()

        # 빈 줄
        if not line.strip():
            i += 1
            continue

        # 구분선
        if line.strip() == "---":
            i += 1
            continue

        # 메인 타이틀 (# )
        if line.startswith("# "):
            title_text = line[2:].strip().replace("🩺 ", "")
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(title_text)
            run.font.name = "맑은 고딕"
            run.font.bold = True
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor(15, 23, 42)
            i += 1
            continue

        # 부제 (> **부제**:)
        if line.startswith("> "):
            sub_text = line[2:].replace("**부제**:", "").strip().replace("**", "")
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(14)
            run = p.add_run(f"부제: {sub_text}")
            run.font.name = "맑은 고딕"
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(100, 116, 139)
            i += 1
            continue

        # 대제목 (## )
        if line.startswith("## "):
            h2_text = line[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(h2_text)
            run.font.name = "맑은 고딕"
            run.font.bold = True
            run.font.size = Pt(12.5)
            run.font.color.rgb = RGBColor(2, 132, 199)
            i += 1
            continue

        # 중제목 (### [Tx] ...)
        if line.startswith("### "):
            h3_text = line[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(h3_text)
            run.font.name = "맑은 고딕"
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(15, 23, 42)
            i += 1
            continue

        # 소제목 (#### ⚪ / #### 🟢 / #### 📊)
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

        # 질문 상자
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

        # 검증 목표 상자
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

        # 일반 글머리 기호
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
                r.font.size = Pt(9.5)
            i += 1
            continue

        # 일반 문단
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
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(51, 65, 85)
        i += 1

    if in_table:
        flush_table()

    doc.save(DOCX_FILE)
    print(f"🎉 Word 문서 생성 완료: {DOCX_FILE} ({DOCX_FILE.stat().st_size:,} bytes)")

    # Downloads 폴더로 복사
    if DOWNLOADS_DIR.exists():
        target = DOWNLOADS_DIR / DOCX_FILE.name
        shutil.copy(DOCX_FILE, target)
        print(f"📁 사용자 다운로드 폴더로 복사: {target}")

    # HWP 파일 생성
    # 아래아한글은 인쇄용 HTML/MHT/Word 문서를 .hwp 확장자로 저장했을 때 바로 완벽 호환 문서로 인식하고 열 수 있습니다.
    HTML_FILE = Path("RAG_ON_OFF_비교검증보고서.html")
    if HTML_FILE.exists():
        hwp_content = HTML_FILE.read_bytes()
        HWP_FILE.write_bytes(hwp_content)
        print(f"🎉 HWP 문서 생성 완료: {HWP_FILE} ({HWP_FILE.stat().st_size:,} bytes)")
        if DOWNLOADS_DIR.exists():
            shutil.copy(HWP_FILE, DOWNLOADS_DIR / HWP_FILE.name)
            print(f"📁 사용자 다운로드 폴더로 복사: {DOWNLOADS_DIR / HWP_FILE.name}")

    return True

if __name__ == "__main__":
    build_docx_from_markdown()
