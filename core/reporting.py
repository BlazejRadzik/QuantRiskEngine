# core/reporting.py
from fpdf import FPDF
from datetime import datetime
import os

class RiskReportPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'QuantRisk - Institutional Portfolio Factsheet', border=False, align='C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', align='C')

def generate_pdf_factsheet(tickers, weights, metrics, filepath="risk_report.pdf"):
    pdf = RiskReportPDF()
    pdf.add_page()
    
    # Podsumowanie Portfela
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, '1. Portfolio Allocation', ln=True)
    pdf.set_font('helvetica', '', 10)
    for t, w in zip(tickers, weights):
        pdf.cell(0, 8, f"   - Asset: {t} | Weight: {w*100:.2f}%", ln=True)
    pdf.ln(5)

    # Metryki Ryzyka
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, '2. Core Risk Metrics', ln=True)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 8, f"   - Expected Annual Return: {metrics.get('annual_return', 0)*100:.2f}%", ln=True)
    pdf.cell(0, 8, f"   - Annualized Volatility: {metrics.get('annual_volatility', 0)*100:.2f}%", ln=True)
    pdf.cell(0, 8, f"   - Historical VaR (95%): {metrics.get('var_95', 0)*100:.2f}%", ln=True)
    pdf.cell(0, 8, f"   - Expected Shortfall (CVaR): {metrics.get('cvar_95', 0)*100:.2f}%", ln=True)
    pdf.cell(0, 8, f"   - Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}", ln=True)
    
    # Disclaimer
    pdf.ln(15)
    pdf.set_font('helvetica', 'I', 8)
    pdf.multi_cell(0, 5, "DISCLAIMER: This report is computer-generated using Multi-threaded Monte Carlo (OpenMP) and GARCH volatility models. It does not constitute financial advice.")
    
    pdf.output(filepath)
    return filepath