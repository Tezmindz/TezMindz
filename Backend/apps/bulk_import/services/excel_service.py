import io
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


class ExcelService:
    """
    Handles reading, parsing, template generation, and error reporting for .xlsx workbooks.
    """

    @staticmethod
    def validate_uploaded_file(uploaded_file):
        """
        Validates the uploaded file extension and size.
        Returns (is_valid, error_message).
        """
        if not uploaded_file:
            return False, "No file was uploaded."

        filename = uploaded_file.name.lower()
        if not filename.endswith(".xlsx"):
            return False, f"Unsupported file format '{uploaded_file.name}'. Only Microsoft Excel (.xlsx) files are supported."

        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            size_mb = uploaded_file.size / (1024 * 1024)
            return False, f"Uploaded file is too large ({size_mb:.1f} MB). Maximum allowed size is 15 MB."

        return True, ""

    @staticmethod
    def parse_sheet_rows(uploaded_file):
        """
        Loads the workbook and returns (headers, rows, error).
        rows is a list of dicts: {"row_number": int, "data": {canonical_field: raw_value}}
        """
        try:
            wb = load_workbook(filename=uploaded_file, data_only=True)
        except Exception as e:
            return None, None, f"Failed to parse Excel workbook. The file may be corrupt or encrypted: {str(e)}"

        sheet = wb.active
        if not sheet or sheet.max_row < 1:
            return None, None, "The spreadsheet is empty. Please ensure data is present."

        # Read first row as headers
        raw_headers = []
        for cell in sheet[1]:
            val = str(cell.value or "").strip()
            raw_headers.append(val)

        # Filter out empty trailing header columns
        while raw_headers and not raw_headers[-1]:
            raw_headers.pop()

        if not raw_headers:
            return None, None, "Row 1 must contain column headers, but all cells were empty."

        rows = []
        # Row index starts at 2 (row 1 is header)
        for row_idx in range(2, sheet.max_row + 1):
            row_cells = sheet[row_idx]
            row_dict = {}
            has_data = False
            for col_idx, header in enumerate(raw_headers):
                cell_val = row_cells[col_idx].value if col_idx < len(row_cells) else None
                if cell_val is not None and str(cell_val).strip() != "":
                    has_data = True
                row_dict[header] = cell_val

            # Skip row if row 2 is the instruction/guidance note or completely blank
            if has_data:
                # Check if it's the template guidance row
                first_val = str(list(row_dict.values())[0] or "").strip().lower()
                if first_val.startswith("example:") or first_val.startswith("instruction:") or first_val.startswith("note:"):
                    continue
                rows.append({
                    "row_number": row_idx,
                    "data": row_dict
                })

        return raw_headers, rows, None

    @staticmethod
    def generate_template(import_type: str) -> io.BytesIO:
        """
        Generates a professionally styled .xlsx template for the given import type.
        """
        wb = Workbook()
        ws = wb.active

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        guide_font = Font(name="Calibri", size=10, italic=True, color="64748B")
        guide_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        data_font = Font(name="Calibri", size=11)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0")
        )

        if import_type == "curriculum":
            ws.title = "Curriculum"
            headers = [
                "Grade", "Subject", "Chapter", "Concept",
                "Chapter Order", "Chapter Difficulty", "Chapter Description",
                "Concept Order", "Concept Content"
            ]
            guidance = [
                "Required (e.g. Class 5)", "Required (e.g. Mathematics)", "Required (e.g. Fractions & Decimals)",
                "Required (e.g. Fraction Pizza)", "Optional (e.g. 1)", "Optional: easy, medium, hard",
                "Optional plain text description", "Optional (e.g. 1)", "Optional Markdown / explanation"
            ]
            samples = [
                ["Class 5", "Mathematics", "Number & Operations", "Place Value Systems", 1, "easy", "Mastering Indian and International place value", 1, "Explanation of place value and face value."],
                ["Class 5", "Mathematics", "Number & Operations", "Large Numbers Rounding", 1, "medium", "Mastering Indian and International place value", 2, "Rules for rounding numbers to nearest 10, 100, 1000."],
                ["Class 5", "Science", "Living Organisms & Habitat", "Terrestrial Habitats", 1, "easy", "Ecosystems and adaptations", 1, "Deserts, mountains, and grasslands characteristics."]
            ]

        elif import_type == "questions":
            ws.title = "Questions"
            headers = [
                "Grade", "Subject", "Chapter", "Concept", "Question Prompt",
                "Option A", "Option B", "Option C", "Option D",
                "Correct Answer", "Difficulty", "Marks", "Negative Marks",
                "Explanation", "Allow Multiple Answers", "Hint 1", "Question ID"
            ]
            guidance = [
                "Required (e.g. Class 5)", "Required (e.g. Mathematics)", "Required (e.g. Number & Operations)",
                "Optional (e.g. Place Value Systems)", "Required: question text or prompt",
                "Required: 1st option", "Required: 2nd option", "Optional: 3rd option", "Optional: 4th option",
                "Required: A, B, C, D (or option text)", "Optional: easy, medium, hard (default: easy)",
                "Optional (default: 1)", "Optional (default: 0)", "Optional: shown upon incorrect answer",
                "Optional: TRUE or FALSE (default: FALSE)", "Optional: hint for student",
                "Leave blank for CREATE, or fill existing ID for UPDATE"
            ]
            samples = [
                ["Class 5", "Mathematics", "Number & Operations", "Place Value Systems", "What is the place value of 9 in 492,305?", "9,000", "90,000", "900", "90", "B", "easy", 1, 0, "The digit 9 is in the ten thousands place, representing 90,000.", "FALSE", "Count the positions from the right: Units, Tens, Hundreds, Thousands, Ten Thousands.", ""],
                ["Class 5", "Mathematics", "Number & Operations", "Place Value Systems", "Which number is the greatest?", "45,892", "45,982", "45,829", "45,298", "B", "easy", 1, 0, "Comparing digits from left to right, 45,982 has the highest digit in the hundreds place.", "FALSE", "Compare the hundreds digit of all options.", ""],
                ["Class 5", "Science", "Living Organisms & Habitat", "Terrestrial Habitats", "Which of the following is an adaptation of camels for living in deserts?", "Thick fur", "Hump for fat storage", "Gills for breathing", "Webbed feet", "B", "medium", 1, 0, "Camels store fat in their humps which provides energy when food and water are scarce.", "FALSE", "Think about energy storage in arid climates.", ""]
            ]

        elif import_type == "game_content":
            ws.title = "Game Content"
            headers = [
                "Game Title", "Step Order", "Prompt", "Content Type",
                "Points", "Target Data (JSON)", "Correct Answer (JSON)", "Hints (JSON)"
            ]
            guidance = [
                "Required: Exact title of existing Game", "Required: Step sequence (1, 2, ...)",
                "Required: Challenge prompt or question", "Optional: e.g. standard, read_number, choice",
                "Optional: points awarded (e.g. 10)", 'Optional JSON: e.g. {"target": 45}',
                'Optional JSON: e.g. "45"', 'Optional JSON list: e.g. ["Look at the tens digit"]'
            ]
            samples = [
                ["Dream House Builder 3D", 1, "Solve 45 x 6 to buy foundation cement", "standard", 15, '{"target": 270}', '"270"', '["Multiply 40x6 then 5x6"]'],
                ["Dream House Builder 3D", 2, "Place value of 7 in 74,520 to install structural pillars", "standard", 20, '{"target": 70000}', '"70000"', '["7 is in the ten-thousands place"]'],
                ["Pizza Fraction Challenge", 1, "Serve 3/4 of a mushroom pizza to customer 1", "fraction_slice", 10, '{"slices": 4, "target_num": 3}', '{"num": 3, "den": 4}', '["Select 3 slices out of 4"]']
            ]

        elif import_type == "quizzes":
            ws.title = "Quizzes & Mock Tests"
            headers = [
                "Quiz Title", "Grade", "Subject", "Chapter", "Quiz Duration (Mins)",
                "Question Prompt", "Option A", "Option B", "Option C", "Option D",
                "Correct Answer", "Marks", "Explanation", "Concept"
            ]
            guidance = [
                "Required: Title of Quiz or Mock Test", "Required: Grade", "Required: Subject", "Required: Chapter",
                "Optional: time limit in minutes (e.g. 15)", "Required: question prompt",
                "Required: Option A", "Required: Option B", "Optional: Option C", "Optional: Option D",
                "Required: A, B, C, or D", "Optional: Marks (default: 1)",
                "Optional: explanation", "Optional: Concept"
            ]
            samples = [
                ["Number Systems Olympiad Mock Test 1", "Class 5", "Mathematics", "Number & Operations", 20, "What is 50,000 + 4,000 + 300 + 20 + 1?", "54,321", "54,312", "54,123", "54,231", "A", 1, "Standard place value expansion equals 54,321.", "Place Value Systems"],
                ["Number Systems Olympiad Mock Test 1", "Class 5", "Mathematics", "Number & Operations", 20, "Round 3,456 to the nearest hundred.", "3,400", "3,500", "3,460", "3,000", "B", 1, "The tens digit is 5, so we round up to 3,500.", "Place Value Systems"]
            ]
        else:
            headers = ["Field 1", "Field 2"]
            guidance = ["Notes 1", "Notes 2"]
            samples = []

        # Write Header Row
        ws.append(headers)
        ws.row_dimensions[1].height = 28
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = thin_border

        # Write Guidance Row (Row 2)
        ws.append(guidance)
        ws.row_dimensions[2].height = 22
        for col_num in range(1, len(guidance) + 1):
            cell = ws.cell(row=2, column=col_num)
            cell.font = guide_font
            cell.fill = guide_fill
            cell.alignment = left_align
            cell.border = thin_border

        # Write Sample Rows (Row 3+)
        for sample_row in samples:
            ws.append(sample_row)
            row_idx = ws.max_row
            ws.row_dimensions[row_idx].height = 20
            for col_num in range(1, len(sample_row) + 1):
                cell = ws.cell(row=row_idx, column=col_num)
                cell.font = data_font
                cell.alignment = left_align
                cell.border = thin_border

        # Adjust column widths dynamically
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

        # Freeze the top header rows
        ws.freeze_panes = "A3"

        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        return out

    @staticmethod
    def generate_error_report(job) -> io.BytesIO:
        """
        Generates an Excel error report workbook containing all validation errors for a job.
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Import Errors"

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="DC2626", end_color="DC2626", fill_type="solid") # Red
        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0")
        )

        headers = ["Row Number", "Field / Column", "Error Description", "Provided Value"]
        ws.append(headers)
        ws.row_dimensions[1].height = 26
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        for err in job.error_summary:
            ws.append([
                err.get("row", ""),
                err.get("field", ""),
                err.get("error", ""),
                str(err.get("value", ""))
            ])
            row_idx = ws.max_row
            ws.row_dimensions[row_idx].height = 20
            for col_num in range(1, 5):
                cell = ws.cell(row=row_idx, column=col_num)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="left", vertical="center")

        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 16)

        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        return out
