from routers.reports import _csv, _pdf


def test_report_csv_and_pdf_export():
    rows = [{"bureau": "RB", "n": 2}]
    assert _csv(rows).startswith(b"bureau")
    pdf = _pdf("bureau", rows)
    assert pdf.startswith(b"%PDF")
