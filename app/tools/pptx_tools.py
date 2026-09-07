from app.services.pptx_service import generate_sales_pptx


def generate_sales_analysis(output_path=None, target_date=None):
    """
    Generate the daily supermarket sales analysis PowerPoint.
    Defaults to a date-stamped file inside app/config.REPORT_DIR.
    """

    try:
        return generate_sales_pptx(output_path=output_path, target_date=target_date)

    except Exception as e:
        return {"success": False, "message": str(e)}
