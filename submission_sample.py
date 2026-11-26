"""Generate the identity-free workbook offered by the submission page."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill


def sample_workbook() -> bytes:
    return _worksheet("제출 테스트", [
        ["항목", "예시 내용"],
        ["용도", "HEALTH QUEST Excel 첨부와 교사 열람을 확인하는 테스트입니다."],
        ["개인 별명", "백합"],
        ["모둠 별명", "햇살"],
        ["예시 답안", "상황에서 확인한 단서를 정리하고 선택한 판단의 근거를 설명했습니다."],
    ])


def alias_worksheet(learner_alias: str, team_alias: str) -> bytes:
    return _worksheet("별명 학습지", [
        ["항목", "작성 내용"],
        ["개인 별명", learner_alias],
        ["모둠 별명", team_alias or "미편성"],
        ["학습 주제", ""],
        ["관찰한 단서", ""],
        ["판단과 수업 근거", ""],
        ["해결안과 성찰", ""],
    ])


def _worksheet(title: str, rows: list[list[str]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title
    for values in rows:
        sheet.append(values)
        for cell in sheet[sheet.max_row]:
            if cell.data_type == "f":
                cell.data_type = "s"
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor="233D73")
        cell.font = Font(bold=True, color="FFFFFF")
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        sheet.row_dimensions[row[0].row].height = 28
    sheet.column_dimensions["A"].width = 18
    sheet.column_dimensions["B"].width = 78
    sheet.freeze_panes = "B2"
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
