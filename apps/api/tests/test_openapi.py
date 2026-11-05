from main import app


def test_openapi_exports_new_surfaces():
    paths = app.openapi()["paths"]
    for path in (
        "/dashboard/heatmap",
        "/overlaps",
        "/institutions/{institution_id}/intel",
        "/reports/{report_type}",
        "/agents/dossiers/{institution_id}",
    ):
        assert path in paths
