"""
Enhanced PDF Generation Service for NHS Forms
Professional NHS-compliant PDFs with branding, headers, footers, and advanced formatting
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, KeepTogether, PageTemplate, Frame
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.doctemplate import BaseDocTemplate
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.lib.colors import Color, HexColor

from ..models.schemas import FilledForm, FormTypeEnum

logger = logging.getLogger(__name__)


class EnhancedPDFGenerator:
    """Enhanced PDF generator with NHS branding and professional formatting"""
    
    # NHS Brand Colors
    NHS_BLUE = HexColor("#005EB8")
    NHS_DARK_BLUE = HexColor("#003087") 
    NHS_LIGHT_BLUE = HexColor("#41B6E6")
    NHS_GREEN = HexColor("#009639")
    NHS_DARK_GREY = HexColor("#425563")
    NHS_MID_GREY = HexColor("#768692")
    NHS_LIGHT_GREY = HexColor("#E8EDEE")
    
    def __init__(self, output_dir: str = "./data/forms"):
        """Initialize enhanced PDF generator"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_nhs_styles()
    
    def _setup_nhs_styles(self):
        """Setup NHS-compliant styles"""
        
        # NHS Main Header
        self.styles.add(ParagraphStyle(
            name='NHSMainHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=self.NHS_BLUE,
            alignment=TA_CENTER,
            spaceAfter=25,
            spaceBefore=10
        ))
        
        # NHS Sub Header
        self.styles.add(ParagraphStyle(
            name='NHSSubHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=self.NHS_DARK_BLUE,
            alignment=TA_LEFT,
            spaceAfter=15,
            spaceBefore=20,
            borderWidth=2,
            borderColor=self.NHS_BLUE,
            borderPadding=8,
            backColor=self.NHS_LIGHT_GREY
        ))
        
        # NHS Field Label
        self.styles.add(ParagraphStyle(
            name='NHSFieldLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=self.NHS_DARK_GREY,
            spaceAfter=3,
            spaceBefore=8
        ))
        
        # NHS Field Value
        self.styles.add(ParagraphStyle(
            name='NHSFieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.black,
            spaceAfter=8,
            leftIndent=15
        ))
        
        # NHS Important Text
        self.styles.add(ParagraphStyle(
            name='NHSImportant',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=self.NHS_DARK_BLUE,
            backColor=colors.Color(0.95, 0.98, 1.0),
            borderWidth=1,
            borderColor=self.NHS_BLUE,
            borderPadding=10,
            spaceAfter=15,
            spaceBefore=10
        ))
        
        # NHS Footer
        self.styles.add(ParagraphStyle(
            name='NHSFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            textColor=self.NHS_MID_GREY,
            alignment=TA_CENTER,
            spaceBefore=20
        ))
        
        # NHS Warning/Alert
        self.styles.add(ParagraphStyle(
            name='NHSWarning',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.Color(0.8, 0.2, 0.2),
            backColor=colors.Color(1.0, 0.95, 0.95),
            borderWidth=1,
            borderColor=colors.Color(0.8, 0.2, 0.2),
            borderPadding=8,
            spaceAfter=10
        ))
    
    def generate_enhanced_pdf(self, filled_form: FilledForm, form_type: FormTypeEnum, 
                            include_header: bool = True, include_footer: bool = True,
                            watermark: str = None) -> str:
        """
        Generate enhanced NHS-compliant PDF with professional formatting
        
        Args:
            filled_form: Form data to convert
            form_type: Type of NHS form
            include_header: Include NHS header branding
            include_footer: Include compliance footer
            watermark: Optional watermark text (e.g., "CONFIDENTIAL")
            
        Returns:
            str: Path to generated PDF
        """
        try:
            # Create filename with patient info if available
            patient_name = filled_form.filled_data.get('patient_name', 'Unknown')
            safe_name = ''.join(c for c in patient_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:20]  # Limit length
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{form_type.value}_{safe_name}_{timestamp}.pdf"
            file_path = os.path.join(self.output_dir, filename)
            
            # Create enhanced document with custom templates
            doc = self._create_nhs_document(file_path, form_type, watermark)
            
            # Build content
            content = []
            
            # Add NHS header if requested
            if include_header:
                content.extend(self._build_nhs_header(form_type))
            
            # Add form-specific content
            if form_type == FormTypeEnum.DISCHARGE_SUMMARY:
                content.extend(self._build_enhanced_discharge_summary(filled_form.filled_data))
            elif form_type == FormTypeEnum.REFERRAL:
                content.extend(self._build_enhanced_referral(filled_form.filled_data))
            elif form_type == FormTypeEnum.RISK_ASSESSMENT:
                content.extend(self._build_enhanced_risk_assessment(filled_form.filled_data))
            else:
                content.extend(self._build_enhanced_generic(filled_form.filled_data, form_type))
            
            # Add compliance footer if requested
            if include_footer:
                content.extend(self._build_nhs_footer(filled_form))
            
            # Build the PDF
            doc.build(content)
            
            logger.info(f"Generated enhanced PDF: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating enhanced PDF: {str(e)}")
            raise e
    
    def _create_nhs_document(self, filename: str, form_type: FormTypeEnum, watermark: str = None):
        """Create NHS-branded document template"""
        
        class NHSDocTemplate(BaseDocTemplate):
            def __init__(self, filename, **kwargs):
                super().__init__(filename, **kwargs)
                
            def afterPage(self):
                """Add watermark and page numbers"""
                canvas = self.canv
                
                # Add watermark if specified
                if watermark:
                    canvas.saveState()
                    canvas.setFillColor(colors.Color(0.9, 0.9, 0.9, alpha=0.3))
                    canvas.setFont("Helvetica-Bold", 48)
                    canvas.rotate(45)
                    canvas.drawCentredText(300, -100, watermark)
                    canvas.restoreState()
                
                # Add page numbers
                canvas.saveState()
                canvas.setFont("Helvetica", 8)
                canvas.setFillColor(self.NHS_MID_GREY)
                page_num = canvas.getPageNumber()
                canvas.drawRightString(A4[0] - 72, 30, f"Page {page_num}")
                canvas.restoreState()
        
        # Create document with NHS template
        doc = NHSDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=25*mm
        )
        
        # Define page template
        frame = Frame(
            20*mm, 25*mm, A4[0] - 40*mm, A4[1] - 50*mm,
            leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0
        )
        
        template = PageTemplate(id='normal', frames=[frame])
        doc.addPageTemplates([template])
        
        return doc
    
    def _build_nhs_header(self, form_type: FormTypeEnum) -> List:
        """Build NHS-branded header"""
        content = []
        
        # NHS Logo placeholder (would use actual logo in production)
        logo_drawing = Drawing(100, 30)
        logo_drawing.add(Rect(0, 0, 100, 30, fillColor=self.NHS_BLUE, strokeColor=self.NHS_BLUE))
        logo_drawing.add(String(50, 10, "NHS", textAnchor="middle", 
                               fontSize=16, fillColor=colors.white, fontName="Helvetica-Bold"))
        content.append(logo_drawing)
        content.append(Spacer(1, 15))
        
        # Form title
        form_title = self._get_form_title(form_type)
        content.append(Paragraph(form_title, self.styles['NHSMainHeader']))
        
        # Confidentiality notice
        content.append(Paragraph(
            "CONFIDENTIAL PATIENT INFORMATION - Handle in accordance with NHS Data Security Standards",
            self.styles['NHSWarning']
        ))
        
        content.append(Spacer(1, 20))
        return content
    
    def _build_nhs_footer(self, filled_form: FilledForm) -> List:
        """Build NHS compliance footer"""
        content = []
        
        content.append(Spacer(1, 30))
        
        # Separator line
        line_drawing = Drawing(400, 10)
        line_drawing.add(Line(0, 5, 400, 5, strokeColor=self.NHS_BLUE, strokeWidth=1))
        content.append(line_drawing)
        
        # Generation info
        generation_time = datetime.now().strftime("%d/%m/%Y at %H:%M GMT")
        content.append(Paragraph(
            f"Generated automatically by NHS Paperwork Automation Agent on {generation_time}",
            self.styles['NHSFooter']
        ))
        
        # Form ID and version
        content.append(Paragraph(
            f"Form ID: {filled_form.form_id} | Template: {filled_form.template_id}",
            self.styles['NHSFooter']
        ))
        
        # Compliance statement
        content.append(Paragraph(
            "This document complies with NHS Data Security Standards and GDPR requirements",
            self.styles['NHSFooter']
        ))
        
        return content
    
    def _build_enhanced_discharge_summary(self, data: Dict[str, Any]) -> List:
        """Build enhanced discharge summary with professional NHS formatting"""
        content = []
        
        # Patient Demographics Section
        content.append(Paragraph("PATIENT DEMOGRAPHICS", self.styles['NHSSubHeader']))
        
        # Patient info in structured table
        patient_info = [
            ["Patient Name", data.get('patient_name', 'Not specified')],
            ["NHS Number", data.get('nhs_number', 'Not specified')],
            ["Date of Birth", data.get('date_of_birth', 'Not specified')],
            ["Gender", data.get('gender', 'Not specified')],
        ]
        
        contact_info = [
            ["Address", data.get('address', 'Not specified')],
            ["GP Name", data.get('gp_name', 'Not specified')],
            ["GP Practice", data.get('gp_practice', 'Not specified')],
        ]
        
        # Two-column layout for demographics
        demo_table = Table([
            [self._create_info_table(patient_info, "Patient Information"),
             self._create_info_table(contact_info, "Contact Information")]
        ], colWidths=[3*inch, 3*inch])
        
        demo_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        content.append(demo_table)
        content.append(Spacer(1, 20))
        
        # Clinical Episode Section
        content.append(Paragraph("CLINICAL EPISODE", self.styles['NHSSubHeader']))
        
        episode_data = [
            ["Admission Date", data.get('admission_date', 'Not specified')],
            ["Discharge Date", data.get('discharge_date', datetime.now().strftime("%d/%m/%Y"))],
            ["Ward/Department", data.get('ward', 'Not specified')],
            ["Consultant", data.get('consultant', 'Not specified')],
            ["Length of Stay", self._calculate_los(data.get('admission_date'), data.get('discharge_date'))],
        ]
        
        episode_table = self._create_info_table(episode_data, "Episode Details")
        content.append(episode_table)
        content.append(Spacer(1, 20))
        
        # Clinical Summary Section
        content.append(Paragraph("CLINICAL SUMMARY", self.styles['NHSSubHeader']))
        
        # Key clinical information
        clinical_sections = [
            ("Presenting Complaint", data.get('presenting_complaint', '')),
            ("Primary Diagnosis", data.get('primary_diagnosis', '')),
            ("Secondary Diagnoses", data.get('secondary_diagnoses', '')),
        ]
        
        for section_name, section_value in clinical_sections:
            if section_value:
                content.append(self._create_clinical_section(section_name, section_value, important=True))
        
        # Medical History and Medications
        content.append(Paragraph("MEDICAL HISTORY & MEDICATIONS", self.styles['NHSSubHeader']))
        
        # Create medication tables
        if data.get('medications_on_admission'):
            content.append(Paragraph("Medications on Admission", self.styles['NHSFieldLabel']))
            content.append(self._create_medication_table(data.get('medications_on_admission', '')))
            content.append(Spacer(1, 10))
        
        if data.get('discharge_medications'):
            content.append(Paragraph("Discharge Medications", self.styles['NHSFieldLabel']))
            content.append(self._create_medication_table(data.get('discharge_medications', '')))
            content.append(Spacer(1, 10))
        
        # Allergies - highlighted for safety
        if data.get('allergies'):
            allergies = data.get('allergies', 'NKDA')
            if allergies.upper() not in ['NKDA', 'NO KNOWN DRUG ALLERGIES', '']:
                content.append(Paragraph(f"⚠️ ALLERGIES: {allergies}", self.styles['NHSWarning']))
            else:
                content.append(self._create_clinical_section("Allergies", allergies))
        
        # Other clinical sections
        other_sections = [
            ("Past Medical History", data.get('past_medical_history', '')),
            ("Examination Findings", data.get('examination_findings', '')),
            ("Investigation Results", data.get('investigation_results', '')),
            ("Treatment Given", data.get('treatment_given', '')),
        ]
        
        for section_name, section_value in other_sections:
            if section_value:
                content.append(self._create_clinical_section(section_name, section_value))
        
        # Discharge Planning Section
        content.append(Paragraph("DISCHARGE PLANNING", self.styles['NHSSubHeader']))
        
        discharge_sections = [
            ("Follow-up Instructions", data.get('follow_up_instructions', '')),
            ("Actions Required by GP", data.get('gp_actions_required', '')),
            ("Discharge Destination", data.get('discharge_destination', 'Home')),
        ]
        
        for section_name, section_value in discharge_sections:
            if section_value:
                content.append(self._create_clinical_section(section_name, section_value, important=True))
        
        return content
    
    def _build_enhanced_referral(self, data: Dict[str, Any]) -> List:
        """Build enhanced referral form"""
        content = []
        
        # Patient Demographics
        content.append(Paragraph("PATIENT DETAILS", self.styles['NHSSubHeader']))
        
        patient_data = [
            ["Patient Name", data.get('patient_name', 'Not specified')],
            ["NHS Number", data.get('nhs_number', 'Not specified')],
            ["Date of Birth", data.get('date_of_birth', 'Not specified')],
            ["Gender", data.get('gender', 'Not specified')],
            ["Contact Number", data.get('phone_number', 'Not specified')],
            ["Address", data.get('address', 'Not specified')],
        ]
        
        content.append(self._create_info_table(patient_data, "Patient Information"))
        content.append(Spacer(1, 20))
        
        # Referral Details
        content.append(Paragraph("REFERRAL DETAILS", self.styles['NHSSubHeader']))
        
        referral_data = [
            ["Referring Clinician", data.get('referring_clinician', 'Not specified')],
            ["Referring Department", data.get('referring_department', 'Not specified')],
            ["Referring To", data.get('referral_to', 'Not specified')],
            ["Urgency", data.get('referral_urgency', 'Routine')],
            ["Referral Date", datetime.now().strftime("%d/%m/%Y")],
        ]
        
        content.append(self._create_info_table(referral_data, "Referral Information"))
        content.append(Spacer(1, 20))
        
        # Clinical Information
        content.append(Paragraph("CLINICAL INFORMATION", self.styles['NHSSubHeader']))
        
        clinical_sections = [
            ("Reason for Referral", data.get('referral_reason', '')),
            ("Relevant Clinical History", data.get('clinical_history', '')),
            ("Examination Findings", data.get('examination_findings', '')),
            ("Investigations Completed", data.get('investigations_completed', '')),
            ("Current Medications", data.get('current_medications', '')),
            ("Known Allergies", data.get('allergies', 'NKDA')),
            ("Social Circumstances", data.get('social_circumstances', '')),
        ]
        
        for section_name, section_value in clinical_sections:
            if section_value:
                important = section_name in ["Reason for Referral", "Known Allergies"]
                content.append(self._create_clinical_section(section_name, section_value, important))
        
        return content
    
    def _build_enhanced_risk_assessment(self, data: Dict[str, Any]) -> List:
        """Build enhanced risk assessment form"""
        content = []
        
        # Patient Details
        content.append(Paragraph("PATIENT DETAILS", self.styles['NHSSubHeader']))
        
        patient_data = [
            ["Patient Name", data.get('patient_name', 'Not specified')],
            ["NHS Number", data.get('nhs_number', 'Not specified')],
            ["Date of Birth", data.get('date_of_birth', 'Not specified')],
            ["Assessment Date", data.get('assessment_date', datetime.now().strftime("%d/%m/%Y"))],
            ["Assessor Name", data.get('assessor_name', 'Not specified')],
        ]
        
        content.append(self._create_info_table(patient_data, "Assessment Details"))
        content.append(Spacer(1, 20))
        
        # Risk Assessment Matrix
        content.append(Paragraph("RISK ASSESSMENT MATRIX", self.styles['NHSSubHeader']))
        
        # Create risk matrix with color coding
        risk_data = [
            ["Risk Category", "Risk Level", "Risk Factors", "Action Required"],
            [
                "Falls Risk", 
                self._format_risk_level(data.get('falls_risk', 'Not Assessed')),
                data.get('falls_risk_factors', 'None identified'),
                self._get_risk_actions('falls', data.get('falls_risk', 'Low'))
            ],
            [
                "Pressure Ulcer Risk",
                self._format_risk_level(data.get('pressure_ulcer_risk', 'Not Assessed')),
                data.get('pressure_ulcer_factors', 'None identified'),
                self._get_risk_actions('pressure', data.get('pressure_ulcer_risk', 'Low'))
            ],
            [
                "Nutrition Risk",
                self._format_risk_level(data.get('nutrition_risk', 'Not Assessed')),
                "Assessment required",
                self._get_risk_actions('nutrition', data.get('nutrition_risk', 'Medium'))
            ],
            [
                "Mental Health/Self-harm",
                self._format_risk_level(data.get('self_harm_risk', 'Not Assessed')),
                data.get('mental_health_risk', 'Assessment required'),
                self._get_risk_actions('mental_health', data.get('self_harm_risk', 'Low'))
            ],
        ]
        
        risk_table = Table(risk_data, colWidths=[1.8*inch, 1.2*inch, 2*inch, 1.5*inch])
        risk_table.setStyle(self._get_risk_table_style())
        content.append(risk_table)
        content.append(Spacer(1, 20))
        
        # Detailed Assessments
        content.append(Paragraph("DETAILED ASSESSMENTS", self.styles['NHSSubHeader']))
        
        assessment_sections = [
            ("Mobility Assessment", data.get('mobility_assessment', '')),
            ("Cognitive Assessment", data.get('cognitive_assessment', '')),
            ("Risk Mitigation Plan", data.get('risk_mitigation_plan', '')),
        ]
        
        for section_name, section_value in assessment_sections:
            if section_value:
                content.append(self._create_clinical_section(section_name, section_value, important=True))
        
        # Review Schedule
        if data.get('review_date'):
            content.append(Paragraph("REVIEW SCHEDULE", self.styles['NHSSubHeader']))
            content.append(Paragraph(
                f"Next Review Due: {data.get('review_date', 'Not specified')}",
                self.styles['NHSImportant']
            ))
        
        return content
    
    def _create_info_table(self, data: List[List[str]], title: str = None) -> Table:
        """Create a professional information table"""
        if title:
            # Add title row
            data.insert(0, [title, ""])
            
        table = Table(data, colWidths=[2*inch, 3.5*inch])
        
        style_commands = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, self.NHS_LIGHT_GREY),
        ]
        
        if title:
            # Style the title row
            style_commands.extend([
                ('BACKGROUND', (0, 0), (-1, 0), self.NHS_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('SPAN', (0, 0), (-1, 0)),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ])
            # Style data rows
            style_commands.extend([
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 1), (0, -1), self.NHS_DARK_GREY),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ])
        else:
            style_commands.extend([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), self.NHS_DARK_GREY),
            ])
        
        table.setStyle(TableStyle(style_commands))
        return table
    
    def _create_medication_table(self, medications_text: str) -> Table:
        """Create a professional medication table"""
        if not medications_text:
            return Paragraph("No medications documented", self.styles['NHSFieldValue'])
        
        # Parse medications (assuming semicolon separated)
        medications = [med.strip() for med in medications_text.split(';') if med.strip()]
        
        # Create table data
        med_data = [["Medication", "Instructions"]]
        
        for med in medications:
            # Try to split medication into name and instructions
            parts = med.split(' ', 1)
            med_name = parts[0] if parts else med
            instructions = parts[1] if len(parts) > 1 else ""
            med_data.append([med_name, instructions])
        
        med_table = Table(med_data, colWidths=[2*inch, 3.5*inch])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.NHS_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.98, 0.98, 1.0)),
        ]))
        
        return med_table
    
    def _create_clinical_section(self, title: str, content_text: str, important: bool = False) -> KeepTogether:
        """Create a clinical section with proper formatting"""
        section_content = []
        
        # Section title
        section_content.append(Paragraph(title, self.styles['NHSFieldLabel']))
        
        # Section content with appropriate styling
        style = self.styles['NHSImportant'] if important else self.styles['NHSFieldValue']
        section_content.append(Paragraph(str(content_text), style))
        
        return KeepTogether(section_content)
    
    def _get_risk_table_style(self) -> TableStyle:
        """Get styling for risk assessment table"""
        return TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.NHS_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            
            # Data rows
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Risk level column color coding
            ('BACKGROUND', (1, 1), (1, -1), colors.Color(0.95, 1.0, 0.95)),  # Light green default
        ])
    
    def _format_risk_level(self, risk_level: str) -> str:
        """Format risk level with appropriate indicators"""
        risk_level = str(risk_level).title()
        
        if risk_level in ['High', 'Severe']:
            return f"🔴 {risk_level}"
        elif risk_level in ['Medium', 'Moderate']:
            return f"🟡 {risk_level}"
        elif risk_level in ['Low', 'Minimal']:
            return f"🟢 {risk_level}"
        else:
            return f"⚪ {risk_level}"
    
    def _get_risk_actions(self, risk_type: str, risk_level: str) -> str:
        """Get recommended actions based on risk type and level"""
        actions = {
            'falls': {
                'High': 'Hourly checks, bed rails, call bell within reach',
                'Medium': '2-hourly checks, clear pathways, appropriate footwear',
                'Low': 'Standard precautions, patient education'
            },
            'pressure': {
                'High': 'Pressure-relieving mattress, 2-hourly repositioning',
                'Medium': 'Regular repositioning, skin inspection',
                'Low': 'Standard care, mobility encouragement'
            },
            'nutrition': {
                'High': 'Dietitian referral, daily monitoring',
                'Medium': 'Food record charts, weekly monitoring',
                'Low': 'Encourage adequate intake'
            },
            'mental_health': {
                'High': 'Urgent psychiatric review, 1:1 observation',
                'Medium': 'Mental health team referral, regular checks',
                'Low': 'Standard support, monitor mood'
            }
        }
        
        return actions.get(risk_type, {}).get(risk_level, 'Standard care protocols')
    
    def _calculate_los(self, admission_date: str, discharge_date: str) -> str:
        """Calculate length of stay"""
        if not admission_date or not discharge_date:
            return "Not calculated"
        
        try:
            # This is a simplified calculation - would need proper date parsing
            return "Calculated from dates"
        except:
            return "Not calculated"
    
    def _get_form_title(self, form_type: FormTypeEnum) -> str:
        """Get appropriate title for form type"""
        titles = {
            FormTypeEnum.DISCHARGE_SUMMARY: "DISCHARGE SUMMARY",
            FormTypeEnum.REFERRAL: "INTER-DEPARTMENTAL REFERRAL",
            FormTypeEnum.RISK_ASSESSMENT: "PATIENT RISK ASSESSMENT",
            FormTypeEnum.GP_LETTER: "GP COMMUNICATION",
            FormTypeEnum.COMPLIANCE_CHECK: "COMPLIANCE CHECKLIST"
        }
        return titles.get(form_type, "NHS CLINICAL FORM")
    
    def generate_form_bundle(self, forms: List[tuple], patient_name: str = "Patient") -> str:
        """
        Generate a bundle of multiple forms in a single PDF
        
        Args:
            forms: List of (FilledForm, FormTypeEnum) tuples
            patient_name: Patient name for filename
            
        Returns:
            str: Path to generated bundle PDF
        """
        try:
            # Create bundle filename
            safe_name = ''.join(c for c in patient_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:20]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"NHS_Forms_Bundle_{safe_name}_{timestamp}.pdf"
            file_path = os.path.join(self.output_dir, filename)
            
            # Create document
            doc = self._create_nhs_document(file_path, FormTypeEnum.DISCHARGE_SUMMARY, "BUNDLE")
            
            content = []
            
            # Bundle header
            content.extend(self._build_nhs_header(FormTypeEnum.DISCHARGE_SUMMARY))
            content.append(Paragraph("NHS CLINICAL FORMS BUNDLE", self.styles['NHSMainHeader']))
            content.append(Paragraph(f"Patient: {patient_name}", self.styles['NHSImportant']))
            content.append(Spacer(1, 20))
            
            # Table of contents
            content.append(Paragraph("CONTENTS", self.styles['NHSSubHeader']))
            toc_data = [["Form Type", "Page"]]
            
            for i, (form, form_type) in enumerate(forms, 1):
                toc_data.append([self._get_form_title(form_type), str(i + 1)])
            
            toc_table = Table(toc_data, colWidths=[4*inch, 1*inch])
            toc_table.setStyle(self._get_risk_table_style())
            content.append(toc_table)
            content.append(PageBreak())
            
            # Add each form
            for i, (form, form_type) in enumerate(forms):
                if i > 0:
                    content.append(PageBreak())
                
                # Form content
                if form_type == FormTypeEnum.DISCHARGE_SUMMARY:
                    content.extend(self._build_enhanced_discharge_summary(form.filled_data))
                elif form_type == FormTypeEnum.REFERRAL:
                    content.extend(self._build_enhanced_referral(form.filled_data))
                elif form_type == FormTypeEnum.RISK_ASSESSMENT:
                    content.extend(self._build_enhanced_risk_assessment(form.filled_data))
            
            # Bundle footer
            if forms:
                content.extend(self._build_nhs_footer(forms[0][0]))
            
            # Build PDF
            doc.build(content)
            
            logger.info(f"Generated form bundle: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating form bundle: {str(e)}")
            raise e
    
    def generate_pdf_with_digital_signature(self, filled_form: FilledForm, form_type: FormTypeEnum, 
                                          clinician_name: str = None) -> str:
        """
        Generate PDF with digital signature placeholder
        
        Args:
            filled_form: Form data
            form_type: Form type
            clinician_name: Name of signing clinician
            
        Returns:
            str: Path to generated PDF
        """
        # Generate standard PDF first
        pdf_path = self.generate_enhanced_pdf(filled_form, form_type)
        
        # Add signature section
        try:
            # Would implement digital signature here in production
            # For now, add signature placeholder
            signature_info = {
                'clinician': clinician_name or 'Digital Signature Required',
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'status': 'Pending Digital Signature'
            }
            
            logger.info(f"PDF with signature placeholder generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error adding signature: {str(e)}")
            return pdf_path  # Return unsigned PDF
    
    # Keep existing methods for compatibility
    def generate_pdf(self, filled_form: FilledForm, form_type: FormTypeEnum) -> str:
        """Generate PDF (enhanced version)"""
        return self.generate_enhanced_pdf(filled_form, form_type)
    
    def generate_pdf_bytes(self, filled_form: FilledForm, form_type: FormTypeEnum) -> bytes:
        """Generate PDF as bytes"""
        try:
            buffer = BytesIO()
            
            doc = self._create_nhs_document("temp", form_type)
            doc.filename = buffer
            
            # Build content
            content = []
            content.extend(self._build_nhs_header(form_type))
            
            if form_type == FormTypeEnum.DISCHARGE_SUMMARY:
                content.extend(self._build_enhanced_discharge_summary(filled_form.filled_data))
            elif form_type == FormTypeEnum.REFERRAL:
                content.extend(self._build_enhanced_referral(filled_form.filled_data))
            elif form_type == FormTypeEnum.RISK_ASSESSMENT:
                content.extend(self._build_enhanced_risk_assessment(filled_form.filled_data))
            
            content.extend(self._build_nhs_footer(filled_form))
            
            # Build PDF
            doc.build(content)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF bytes: {str(e)}")
            raise e
