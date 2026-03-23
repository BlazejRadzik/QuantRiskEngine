from datetime import datetime

from fpdf import FPDF

class RiskReportPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "QuantRisk - Institutional Portfolio Factsheet", border=False, align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

def generate_pdf_factsheet(tickers, weights, metrics, filepath="risk_report.pdf"):
    pdf = RiskReportPDF()
    pdf.add_page()

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "1. Portfolio Allocation", ln=True)
    pdf.set_font("helvetica", "", 10)
    for t, w in zip(tickers, weights):
        pdf.cell(0, 8, f"   - Asset: {t} | Weight: {w*100:.2f}%", ln=True)
    pdf.ln(5)

    var_95 = float(metrics.get("var_95", metrics.get("historical_var", 0.0) or 0.0))
    cvar_95 = float(metrics.get("cvar_95", metrics.get("historical_es", 0.0) or 0.0))

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "2. Core Risk Metrics", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f"   - Expected Annual Return: {float(metrics.get('annual_return', 0.0))*100:.2f}%", ln=True)
    pdf.cell(0, 8, f"   - Annualized Volatility: {float(metrics.get('annual_volatility', 0.0))*100:.2f}%", ln=True)
    pdf.cell(0, 8, f"   - Historical VaR (95%): {var_95*100:.2f}%", ln=True)
    pdf.cell(0, 8, f"   - Expected Shortfall (CVaR): {cvar_95*100:.2f}%", ln=True)
    pdf.cell(0, 8, f"   - Sortino Ratio: {float(metrics.get('sortino_ratio', 0.0)):.2f}", ln=True)

    pdf.ln(15)
    pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(
        0,
        5,
        "DISCLAIMER: This report is computer-generated using multi-threaded Monte Carlo (OpenMP), "
        "GARCH-enhanced volatility and LSTM adjustment. It does not constitute financial advice.",
    )

    pdf.output(filepath)
    return filepath
