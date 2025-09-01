"""
PDF Generation Service for NHS Forms
Converts filled form data to professional PDF documents
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, KeepTogether, FrameBreak
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF
from reportlab.platypus.tableofcontents import TableOfContents

from ..models.schemas import FilledForm, FormTypeEnum

logger = logging.getLogger(__name__)


class PDFGeneratorService:
    """Service for generating PDF documents from filled forms"""
    
    def __init__(self, output_dir: str = "./data/forms"):
        """Initialize PDF generator service"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for NHS forms"""
        # NHS Header style
        self.styles.add(ParagraphStyle(
            name='NHSHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.Color(0, 0.2, 0.5),  # NHS Blue
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.Color(0, 0.2, 0.5),
            borderWidth=1,
            borderColor=colors.Color(0, 0.2, 0.5),
            borderPadding=5
        ))
        
        # Field label style
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.Color(0.3, 0.3, 0.3),
            fontName='Helvetica-Bold'
        ))
        
        # Field value style
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8
        ))
    
    def generate_pdf(self, filled_form: FilledForm, form_type: FormTypeEnum) -> str:
        """
        Generate PDF document from filled form data
        
        Args:
            filled_form: FilledForm with data to convert
            form_type: Type of form being generated
            
        Returns:
            str: Path to generated PDF file
        """
        try:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{form_type.value}_{timestamp}.pdf"
            file_path = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            # Build content based on form type
            content = []
            
            if form_type == FormTypeEnum.DISCHARGE_SUMMARY:
                content = self._build_discharge_summary_content(filled_form.filled_data)
            elif form_type == FormTypeEnum.REFERRAL:
                content = self._build_referral_content(filled_form.filled_data)
            elif form_type == FormTypeEnum.RISK_ASSESSMENT:
                content = self._build_risk_assessment_content(filled_form.filled_data)
            else:
                content = self._build_generic_content(filled_form.filled_data, form_type)
            
            # Build PDF
            doc.build(content)
            
            logger.info(f"Generated PDF: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise e
    
    def _build_discharge_summary_content(self, data: Dict[str, Any]) -> list:
        """Build content for NHS Discharge Summary PDF"""
        content = []
        
        # Header
        content.append(Paragraph("NHS DISCHARGE SUMMARY", self.styles['NHSHeader']))
        content.append(Spacer(1, 20))
        
        # Patient demographics section
        content.append(Paragraph("PATIENT DEMOGRAPHICS", self.styles['SectionHeader']))
        
        patient_data = [
            ["Patient Name:", data.get('patient_name', '')],
            ["NHS Number:", data.get('nhs_number', '')],
            ["Date of Birth:", data.get('date_of_birth', '')],
            ["Gender:", data.get('gender', '')],
            ["Address:", data.get('address', '')],
            ["GP Name:", data.get('gp_name', '')],
            ["GP Practice:", data.get('gp_practice', '')],
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(patient_table)
        content.append(Spacer(1, 20))
        
        # Clinical information section
        content.append(Paragraph("CLINICAL INFORMATION", self.styles['SectionHeader']))
        
        clinical_data = [
            ["Admission Date:", data.get('admission_date', '')],
            ["Discharge Date:", data.get('discharge_date', '')],
            ["Ward/Department:", data.get('ward', '')],
            ["Consultant:", data.get('consultant', '')],
        ]
        
        clinical_table = Table(clinical_data, colWidths=[2*inch, 4*inch])
        clinical_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(clinical_table)
        content.append(Spacer(1, 15))
        
        # Clinical details
        clinical_sections = [
            ("Presenting Complaint", data.get('presenting_complaint', '')),
            ("Primary Diagnosis", data.get('primary_diagnosis', '')),
            ("Secondary Diagnoses", data.get('secondary_diagnoses', '')),
            ("Past Medical History", data.get('past_medical_history', '')),
            ("Medications on Admission", data.get('medications_on_admission', '')),
            ("Known Allergies", data.get('allergies', '')),
            ("Clinical Summary", data.get('clinical_summary', '')),
            ("Examination Findings", data.get('examination_findings', '')),
            ("Investigation Results", data.get('investigation_results', '')),
            ("Treatment Given", data.get('treatment_given', '')),
            ("Discharge Medications", data.get('discharge_medications', '')),
            ("Follow-up Instructions", data.get('follow_up_instructions', '')),
            ("Actions Required by GP", data.get('gp_actions_required', '')),
            ("Discharge Destination", data.get('discharge_destination', '')),
        ]
        
        for section_name, section_value in clinical_sections:
            if section_value:
                content.append(Paragraph(section_name, self.styles['FieldLabel']))
                content.append(Paragraph(str(section_value), self.styles['FieldValue']))
                content.append(Spacer(1, 8))
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(Paragraph(
            f"Generated automatically by NHS Paperwork Agent on {datetime.now().strftime('%d/%m/%Y at %H:%M')}",
            self.styles['Normal']
        ))
        
        return content
    
    def _build_referral_content(self, data: Dict[str, Any]) -> list:
        """Build content for NHS Referral PDF"""
        content = []
        
        # Header
        content.append(Paragraph("NHS REFERRAL FORM", self.styles['NHSHeader']))
        content.append(Spacer(1, 20))
        
        # Patient demographics
        content.append(Paragraph("PATIENT DETAILS", self.styles['SectionHeader']))
        
        patient_data = [
            ["Patient Name:", data.get('patient_name', '')],
            ["NHS Number:", data.get('nhs_number', '')],
            ["Date of Birth:", data.get('date_of_birth', '')],
            ["Gender:", data.get('gender', '')],
            ["Contact Number:", data.get('phone_number', '')],
            ["Address:", data.get('address', '')],
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(patient_table)
        content.append(Spacer(1, 20))
        
        # Referral details
        content.append(Paragraph("REFERRAL DETAILS", self.styles['SectionHeader']))
        
        referral_data = [
            ["Referring Clinician:", data.get('referring_clinician', '')],
            ["Referring Department:", data.get('referring_department', '')],
            ["Referring To:", data.get('referral_to', '')],
            ["Urgency:", data.get('referral_urgency', 'Routine')],
        ]
        
        referral_table = Table(referral_data, colWidths=[2*inch, 4*inch])
        referral_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(referral_table)
        content.append(Spacer(1, 15))
        
        # Clinical information sections
        clinical_sections = [
            ("Reason for Referral", data.get('referral_reason', '')),
            ("Relevant Clinical History", data.get('clinical_history', '')),
            ("Examination Findings", data.get('examination_findings', '')),
            ("Investigations Completed", data.get('investigations_completed', '')),
            ("Current Medications", data.get('current_medications', '')),
            ("Known Allergies", data.get('allergies', '')),
            ("Social Circumstances", data.get('social_circumstances', '')),
        ]
        
        for section_name, section_value in clinical_sections:
            if section_value:
                content.append(Paragraph(section_name, self.styles['FieldLabel']))
                content.append(Paragraph(str(section_value), self.styles['FieldValue']))
                content.append(Spacer(1, 8))
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(Paragraph(
            f"Generated automatically by NHS Paperwork Agent on {datetime.now().strftime('%d/%m/%Y at %H:%M')}",
            self.styles['Normal']
        ))
        
        return content
    
    def _build_risk_assessment_content(self, data: Dict[str, Any]) -> list:
        """Build content for NHS Risk Assessment PDF"""
        content = []
        
        # Header
        content.append(Paragraph("NHS RISK ASSESSMENT", self.styles['NHSHeader']))
        content.append(Spacer(1, 20))
        
        # Patient details
        content.append(Paragraph("PATIENT DETAILS", self.styles['SectionHeader']))
        
        patient_data = [
            ["Patient Name:", data.get('patient_name', '')],
            ["NHS Number:", data.get('nhs_number', '')],
            ["Date of Birth:", data.get('date_of_birth', '')],
            ["Assessment Date:", data.get('assessment_date', '')],
            ["Assessor Name:", data.get('assessor_name', '')],
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(patient_table)
        content.append(Spacer(1, 20))
        
        # Risk assessment matrix
        content.append(Paragraph("RISK ASSESSMENT MATRIX", self.styles['SectionHeader']))
        
        risk_data = [
            ["Risk Type", "Level", "Risk Factors"],
            ["Falls Risk", data.get('falls_risk', 'Not Assessed'), data.get('falls_risk_factors', '')],
            ["Pressure Ulcer Risk", data.get('pressure_ulcer_risk', 'Not Assessed'), data.get('pressure_ulcer_factors', '')],
            ["Nutrition Risk", data.get('nutrition_risk', 'Not Assessed'), ""],
            ["Self-harm Risk", data.get('self_harm_risk', 'Not Assessed'), ""],
        ]
        
        risk_table = Table(risk_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(risk_table)
        content.append(Spacer(1, 15))
        
        # Assessment details
        assessment_sections = [
            ("Mental Health Risk", data.get('mental_health_risk', '')),
            ("Mobility Assessment", data.get('mobility_assessment', '')),
            ("Cognitive Assessment", data.get('cognitive_assessment', '')),
            ("Risk Mitigation Plan", data.get('risk_mitigation_plan', '')),
        ]
        
        for section_name, section_value in assessment_sections:
            if section_value:
                content.append(Paragraph(section_name, self.styles['FieldLabel']))
                content.append(Paragraph(str(section_value), self.styles['FieldValue']))
                content.append(Spacer(1, 8))
        
        # Review date
        if data.get('review_date'):
            content.append(Spacer(1, 15))
            content.append(Paragraph("Next Review Date", self.styles['FieldLabel']))
            content.append(Paragraph(data.get('review_date', ''), self.styles['FieldValue']))
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(Paragraph(
            f"Generated automatically by NHS Paperwork Agent on {datetime.now().strftime('%d/%m/%Y at %H:%M')}",
            self.styles['Normal']
        ))
        
        return content
    
    def _build_generic_content(self, data: Dict[str, Any], form_type: FormTypeEnum) -> list:
        """Build generic PDF content for any form type"""
        content = []
        
        # Header
        form_title = form_type.value.replace('_', ' ').title()
        content.append(Paragraph(f"NHS {form_title.upper()}", self.styles['NHSHeader']))
        content.append(Spacer(1, 20))
        
        # Data sections
        content.append(Paragraph("FORM DATA", self.styles['SectionHeader']))
        
        for field_name, field_value in data.items():
            if field_value:
                display_name = field_name.replace('_', ' ').title()
                content.append(Paragraph(display_name, self.styles['FieldLabel']))
                content.append(Paragraph(str(field_value), self.styles['FieldValue']))
                content.append(Spacer(1, 5))
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(Paragraph(
            f"Generated automatically by NHS Paperwork Agent on {datetime.now().strftime('%d/%m/%Y at %H:%M')}",
            self.styles['Normal']
        ))
        
        return content
    
    def generate_pdf_bytes(self, filled_form: FilledForm, form_type: FormTypeEnum) -> bytes:
        """
        Generate PDF as bytes for download/streaming
        
        Args:
            filled_form: FilledForm with data to convert
            form_type: Type of form being generated
            
        Returns:
            bytes: PDF content as bytes
        """
        try:
            # Create in-memory PDF
            buffer = BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            # Build content
            if form_type == FormTypeEnum.DISCHARGE_SUMMARY:
                content = self._build_discharge_summary_content(filled_form.filled_data)
            elif form_type == FormTypeEnum.REFERRAL:
                content = self._build_referral_content(filled_form.filled_data)
            elif form_type == FormTypeEnum.RISK_ASSESSMENT:
                content = self._build_risk_assessment_content(filled_form.filled_data)
            else:
                content = self._build_generic_content(filled_form.filled_data, form_type)
            
            # Build PDF
            doc.build(content)
            
            # Get bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF bytes: {str(e)}")
            raise e
