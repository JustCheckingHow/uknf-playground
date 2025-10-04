from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


EXCEL_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
RID_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
EXCEL_EPOCH = date(1899, 12, 30)
FORM_ID_PATTERN = re.compile(r"^F\d{2}\.\d{2}\.\d{2}(?:\.[a-z])?\Z", re.IGNORECASE)


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"
    sheet: str | None = None
    cell: str | None = None
    expected: str | None = None
    actual: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.sheet:
            payload["sheet"] = self.sheet
        if self.cell:
            payload["cell"] = self.cell
        if self.expected is not None:
            payload["expected"] = self.expected
        if self.actual is not None:
            payload["actual"] = self.actual
        return payload


@dataclass
class ValidationResult:
    status: str
    metadata: dict[str, Any]
    forms: list[dict[str, str]]
    flags: dict[str, Any]
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "metadata": self.metadata,
            "forms": self.forms,
            "flags": self.flags,
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
        }


class WorkbookReader:
    """Lightweight Excel reader tailored for UKNF sprawozdania templates."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Brak pliku sprawozdania: {self.file_path}")
        try:
            with zipfile.ZipFile(self.file_path) as archive:
                self.shared_strings = self._load_shared_strings(archive)
                self.sheet_targets = self._load_sheet_targets(archive)
                self.sheets = {
                    name: self._parse_sheet(archive.read(f"xl/{target}"))
                    for name, target in self.sheet_targets.items()
                }
        except zipfile.BadZipFile:
            self._load_xls_workbook()

    def get(self, sheet: str, cell: str) -> Any:
        return self.sheets.get(sheet, {}).get(cell)

    def get_string(self, sheet: str, cell: str) -> str | None:
        value = self.get(sheet, cell)
        if value is None:
            return None
        if isinstance(value, Decimal):
            if value == value.to_integral():
                return str(int(value))
            return format(value.normalize(), "f")
        if isinstance(value, bool):
            return "Tak" if value else "Nie"
        text = str(value).strip()
        return text or None

    def get_decimal(self, sheet: str, cell: str) -> Decimal | None:
        value = self.get(sheet, cell)
        if isinstance(value, Decimal):
            return value
        if isinstance(value, bool) or value is None:
            return None
        try:
            return Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            return None

    def get_bool(self, sheet: str, cell: str) -> bool | None:
        value = self.get(sheet, cell)
        if isinstance(value, bool):
            return value
        if isinstance(value, Decimal):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"tak", "yes", "true", "1"}:
                return True
            if normalized in {"nie", "no", "false", "0"}:
                return False
        return None

    def get_date(self, sheet: str, cell: str) -> date | None:
        value = self.get_decimal(sheet, cell)
        if value is None:
            return None
        try:
            serial = int(value)
        except (ValueError, TypeError):
            return None
        return EXCEL_EPOCH + timedelta(days=serial)

    def _load_shared_strings(self, archive: zipfile.ZipFile) -> list[str]:
        try:
            payload = archive.read("xl/sharedStrings.xml")
        except KeyError:
            return []
        root = self._parse_xml(payload)
        entries: list[str] = []
        for item in root.findall(f"{EXCEL_NS}si"):
            text_parts: list[str] = []
            for node in item:
                if node.tag == f"{EXCEL_NS}t":
                    text_parts.append(node.text or "")
                elif node.tag == f"{EXCEL_NS}r":
                    run_text = node.find(f"{EXCEL_NS}t")
                    if run_text is not None and run_text.text:
                        text_parts.append(run_text.text)
            if not text_parts:
                text_element = item.find(f"{EXCEL_NS}t")
                if text_element is not None and text_element.text:
                    text_parts.append(text_element.text)
            entries.append("".join(text_parts))
        return entries

    def _load_sheet_targets(self, archive: zipfile.ZipFile) -> dict[str, str]:
        rels_root = self._parse_xml(archive.read("xl/_rels/workbook.xml.rels"))
        relation_targets = {
            node.get("Id"): node.get("Target")
            for node in rels_root.findall(f"{REL_NS}Relationship")
        }
        workbook_root = self._parse_xml(archive.read("xl/workbook.xml"))
        mapping: dict[str, str] = {}
        for sheet in workbook_root.findall(f"{EXCEL_NS}sheets/{EXCEL_NS}sheet"):
            relationship_id = sheet.get(f"{RID_NS}id")
            if not relationship_id:
                continue
            target = relation_targets.get(relationship_id)
            if not target:
                continue
            mapping[sheet.get("name", f"sheet{sheet.get('sheetId', '')}")] = target
        return mapping

    def _parse_sheet(self, payload: bytes) -> dict[str, Any]:
        root = self._parse_xml(payload)
        cells: dict[str, Any] = {}
        for cell in root.findall(f".//{EXCEL_NS}c"):
            reference = cell.get("r")
            if not reference:
                continue
            cell_type = cell.get("t")
            if cell_type == "inlineStr":
                text_node = cell.find(f"{EXCEL_NS}is/{EXCEL_NS}t")
                if text_node is not None:
                    cells[reference] = text_node.text or ""
                continue
            value_node = cell.find(f"{EXCEL_NS}v")
            if value_node is None:
                continue
            raw_value = value_node.text or ""
            if cell_type == "s":
                try:
                    cells[reference] = self.shared_strings[int(raw_value)]
                except (IndexError, ValueError):
                    cells[reference] = ""
                continue
            if cell_type == "b":
                cells[reference] = raw_value == "1"
                continue
            try:
                cells[reference] = Decimal(raw_value)
            except InvalidOperation:
                cells[reference] = raw_value
        return cells

    def _load_xls_workbook(self) -> None:
        try:
            import xlrd
        except ImportError as exc:  # pragma: no cover - defensive fallback
            raise ValueError("Plik XLS nie jest obsługiwany w tym środowisku.") from exc

        workbook = xlrd.open_workbook(self.file_path.as_posix())
        try:
            sheet_names = workbook.sheet_names()
            self.shared_strings = []
            self.sheet_targets = {name: name for name in sheet_names}
            self.sheets = {
                name: self._parse_xls_sheet(workbook.sheet_by_name(name))
                for name in sheet_names
            }
        finally:
            workbook.release_resources()

    def _parse_xls_sheet(self, sheet: Any) -> dict[str, Any]:
        import xlrd

        cells: dict[str, Any] = {}
        for row_index in range(sheet.nrows):
            for column_index in range(sheet.ncols):
                cell = sheet.cell(row_index, column_index)
                value = self._convert_xls_cell(cell)
                if value is None or value == "":
                    continue
                reference = f"{_column_label(column_index)}{row_index + 1}"
                cells[reference] = value
        return cells

    def _convert_xls_cell(self, cell: Any) -> Any:
        import xlrd

        if cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
            return None
        if cell.ctype == xlrd.XL_CELL_TEXT:
            return cell.value
        if cell.ctype == xlrd.XL_CELL_BOOLEAN:
            return bool(cell.value)
        if cell.ctype in (xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_DATE):
            try:
                return Decimal(str(cell.value))
            except InvalidOperation:
                return cell.value
        if cell.ctype == xlrd.XL_CELL_ERROR:
            return None
        return cell.value

    @staticmethod
    def _parse_xml(payload: bytes):
        return ET.fromstring(payload)


def _column_label(index: int) -> str:
    label = ""
    while index >= 0:
        index, remainder = divmod(index, 26)
        label = chr(65 + remainder) + label
        index -= 1
    return label


def _decimal_to_str(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == value.to_integral():
        return str(int(value))
    return format(value.normalize(), "f")


def _extract_forms(workbook: WorkbookReader) -> list[dict[str, str]]:
    info_sheet = workbook.sheets.get("INFO", {})
    forms: list[dict[str, str]] = []
    for reference, value in info_sheet.items():
        if not isinstance(value, str):
            continue
        if not FORM_ID_PATTERN.match(value.strip()):
            continue
        column = re.match(r"([A-Z]+)", reference)
        description = workbook.get_string("INFO", f"{column.group(1)}11") if column else None
        forms.append({
            "id": value.strip(),
            "description": description or "",
        })
    forms.sort(key=lambda entry: entry["id"])
    return forms


def _classify_register(period_start: date | None, period_end: date | None) -> str:
    if not period_start or not period_end:
        return "Nieznany"
    span = (period_end - period_start).days
    if 80 <= span <= 100:
        return "Sprawozdania kwartalne"
    if span >= 360:
        return "Sprawozdania roczne"
    return "Sprawozdania okresowe"


def validate_report_workbook(file_path: str | Path) -> ValidationResult:
    """Validate the uploaded sprawozdanie workbook and return a structured result.

    The function reads metadata from the ``INFO`` worksheet, extracts a list of
    declared formularzy and verifies a handful of core business rules that UKNF
    expects (identifier format, quarter length, cross-sheet totals).
    ``ValidationResult`` aggregates the derived metadata, flags and any
    validation issues so the caller can persist the status on the ``Report``
    model and present the feedback in the UI.
    """
    workbook = WorkbookReader(file_path)
    period_start = workbook.get_date("INFO", "C7")
    period_end = workbook.get_date("INFO", "C8")

    metadata = {
        "taxonomy": workbook.get_string("INFO", "C5"),
        "entity_identifier": workbook.get_string("INFO", "C6"),
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat() if period_end else None,
        "currency": workbook.get_string("INFO", "C9"),
        "form_id": workbook.get_string("INFO", "C10"),
        "form_name": workbook.get_string("INFO", "C11"),
        "entity_name": workbook.get_string("F01.05.02", "C7") or workbook.get_string("F01.00.01", "E8"),
        "register": _classify_register(period_start, period_end),
    }

    flags = {
        "includes_board_members": workbook.get_bool("F01.00.01", "E10"),
        "includes_supervisory_board": workbook.get_bool("F01.00.01", "E11"),
        "includes_procurators": workbook.get_bool("F01.00.01", "E12"),
        "is_correction": workbook.get_bool("F01.00.01", "E13"),
    }

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    entity_identifier = metadata.get("entity_identifier") or ""
    if not re.fullmatch(r"RIP\d{7}", entity_identifier):
        errors.append(
            ValidationIssue(
                code="ENTITY_ID_FORMAT",
                message="Identyfikator jednostki powinien mieć format RIP wraz z siedmioma cyframi.",
                sheet="INFO",
                cell="C6",
                actual=entity_identifier or None,
            )
        )

    if period_start and period_end:
        if period_start >= period_end:
            errors.append(
                ValidationIssue(
                    code="PERIOD_RANGE",
                    message="Data początkowa musi być wcześniejsza niż data końcowa.",
                    sheet="INFO",
                    cell="C7",
                    expected=f"<{period_end.isoformat()}",
                    actual=period_start.isoformat(),
                )
            )
        elif (period_end - period_start).days not in range(80, 101):
            warnings.append(
                ValidationIssue(
                    code="PERIOD_SPAN",
                    message="Zakres okresu sprawozdawczego odbiega od standardowego kwartału.",
                    sheet="INFO",
                    cell="C8",
                    severity="warning",
                    actual=str((period_end - period_start).days),
                )
            )
    else:
        errors.append(
            ValidationIssue(
                code="PERIOD_MISSING",
                message="Brak kompletnych dat okresu sprawozdawczego.",
                sheet="INFO",
                cell="C7",
            )
        )

    currency = metadata.get("currency")
    if currency and currency.upper() != "PLN":
        warnings.append(
            ValidationIssue(
                code="CURRENCY_UNSUPPORTED",
                message="Obsługiwane są wyłącznie sprawozdania w walucie PLN.",
                sheet="INFO",
                cell="C9",
                severity="warning",
                actual=currency,
            )
        )

    loans_count_total = workbook.get_decimal("F01.01.01.a", "D9")
    agreements_count_total = workbook.get_decimal("F01.02.01", "D7")
    if loans_count_total is None or agreements_count_total is None:
        errors.append(
            ValidationIssue(
                code="MISSING_TOTAL_COUNTS",
                message="Brak sumarycznej liczby udzielonych kredytów w formularzach F01.01.01.a oraz F01.02.01.",
                sheet="F01.01.01.a",
            )
        )
    elif loans_count_total != agreements_count_total:
        errors.append(
            ValidationIssue(
                code="TOTAL_COUNT_MISMATCH",
                message="Łączna liczba kredytów powinna być zgodna między tabelami F01.01.01.a oraz F01.02.01.",
                sheet="F01.01.01.a",
                cell="D9",
                expected=_decimal_to_str(loans_count_total),
                actual=_decimal_to_str(agreements_count_total),
            )
        )

    loans_value_total = workbook.get_decimal("F01.01.01.a", "D11")
    agreements_value_total = workbook.get_decimal("F01.02.01", "D8")
    if loans_value_total is None or agreements_value_total is None:
        errors.append(
            ValidationIssue(
                code="MISSING_TOTAL_VALUES",
                message="Brak łącznej wartości udzielonych kredytów w formularzach F01.01.01.a oraz F01.02.01.",
                sheet="F01.01.01.a",
            )
        )
    elif loans_value_total != agreements_value_total:
        errors.append(
            ValidationIssue(
                code="TOTAL_VALUE_MISMATCH",
                message="Łączna wartość kredytów powinna być zgodna między tabelami F01.01.01.a oraz F01.02.01.",
                sheet="F01.01.01.a",
                cell="D11",
                expected=_decimal_to_str(loans_value_total),
                actual=_decimal_to_str(agreements_value_total),
            )
        )

    if agreements_count_total is not None and agreements_count_total <= 0:
        errors.append(
            ValidationIssue(
                code="TOTAL_COUNT_NON_POSITIVE",
                message="Liczba zawartych umów o kredyt musi być dodatnia.",
                sheet="F01.02.01",
                cell="D7",
                actual=_decimal_to_str(agreements_count_total),
            )
        )

    if agreements_value_total is not None and agreements_value_total <= 0:
        errors.append(
            ValidationIssue(
                code="TOTAL_VALUE_NON_POSITIVE",
                message="Łączna wartość zawartych umów o kredyt musi być większa od zera.",
                sheet="F01.02.01",
                cell="D8",
                actual=_decimal_to_str(agreements_value_total),
            )
        )

    status = "validated" if not errors else "validation_errors"

    return ValidationResult(
        status=status,
        metadata=metadata,
        forms=_extract_forms(workbook),
        flags=flags,
        errors=errors,
        warnings=warnings,
    )


__all__ = ["ValidationIssue", "ValidationResult", "validate_report_workbook"]
