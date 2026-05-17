"""
Professional PDF Generator Tool
Uses ReportLab to create structured learning summaries with color-coded sections.
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from typing import Dict, Any

class PDFGenerator:
    """Generates professional learning reports for the Agentic AI system"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    def generate_learning_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a comprehensive PDF report including chat history, summary, and quiz results.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"learning_report_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=26,
                textColor=colors.HexColor("#4c1d95"), # Purple
                alignment=1,
                spaceAfter=30
            )
            
            h2_style = ParagraphStyle(
                'H2Style',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=colors.HexColor("#2563eb"), # Blue
                spaceBefore=20,
                spaceAfter=10
            )
            
            h3_style = ParagraphStyle(
                'H3Style',
                parent=styles['Heading3'],
                fontSize=14,
                textColor=colors.HexColor("#1e293b"),
                spaceBefore=12,
                spaceAfter=6
            )
            
            body_style = styles['BodyText']
            body_style.fontSize = 11
            body_style.leading = 14
            
            elements = []
            
            # Header Section
            elements.append(Paragraph("AI Learning Assistant Pro", title_style))
            elements.append(Paragraph(f"Session Report • {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # 1. Current Summary (from new summary generation)
            summary_content = ""
            if data.get('chats'):
                # Extract summary from the first chat's summary section
                for chat in data['chats']:
                    if chat.get('summary'):
                        summary_content = chat['summary']
                        break
            
            if summary_content:
                # Create a highlighted summary section
                summary_style = ParagraphStyle(
                    'SummaryStyle',
                    parent=body_style,
                    fontSize=12,
                    textColor=colors.HexColor("#059669"), # Green color for summary
                    backColor=colors.HexColor("#f0fdf4"), # Light green background
                    spaceBefore=15,
                    spaceAfter=15,
                    leftIndent=20,
                    rightIndent=20,
                    borderWidth=1,
                    borderColor=colors.HexColor("#059669"),
                    borderRadius=6
                )
                elements.append(Paragraph("🟡 Summary", h2_style))
                elements.append(Paragraph(summary_content, summary_style))
                elements.append(Spacer(1, 20))
            
            # 2. Learning Summary (legacy format)
            if data.get('summary') and isinstance(data['summary'], list):
                elements.append(Paragraph("Learning Summary", h2_style))
                for item in data['summary']:
                    elements.append(Paragraph(item['topic'], h3_style))
                    elements.append(Paragraph(item['definition'], body_style))
                    elements.append(Paragraph(f"<b>Key Points:</b> {', '.join(item['key_points'])}", body_style))
                    elements.append(Spacer(1, 10))
            
            # 2. Career Path
            if data.get('careerPath'):
                elements.append(Paragraph("Career Roadmap", h2_style))
                cp = data['careerPath']
                elements.append(Paragraph(f"Target Role: {cp['goal']}", h3_style))
                roadmap_steps = [[f"{i+1}. {step}"] for i, step in enumerate(cp['roadmap'])]
                t = Table(roadmap_steps, colWidths=[400])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                    ('PADDING', (0, 0), (-1, -1), 10),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

            # 3. Quiz Results
            if data.get('quizzes'):
                elements.append(Paragraph("Assessment Performance", h2_style))
                quiz_data = [["Topic", "Level", "Score", "Result"]]
                for q in data['quizzes']:
                    quiz_data.append([q['topic'], q['level'], f"{q['score']}/{q['total']}", q['result']])
                
                t = Table(quiz_data, colWidths=[100, 100, 80, 100])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f1f5f9")),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

            # 4. Resume Analysis
            if data.get('resumeAnalysis'):
                elements.append(Paragraph("Resume Feedback", h2_style))
                ra = data['resumeAnalysis']
                elements.append(Paragraph(ra['summary'], body_style))
                elements.append(Paragraph(f"<b>Technical Score:</b> {ra['technical_score']}/100", body_style))
                elements.append(Paragraph(f"<b>Creativity Score:</b> {ra['creativity_score']}/100", body_style))
                elements.append(Paragraph(f"<b>Missing Skills:</b> {', '.join(ra['missing_skills'])}", body_style))
                elements.append(Spacer(1, 10))
            
            # 5. Chat Logs (Optional/Summary)
            elements.append(PageBreak())
            elements.append(Paragraph("💬 Conversation", h2_style))
            
            # Extract messages from chats
            conversation_count = 1
            if data.get('chats'):
                for chat in data['chats']:
                    if chat.get('messages'):
                        elements.append(Paragraph(f"Chat: {chat.get('title', 'Untitled')}", h3_style))
                        for msg in chat['messages']:
                            if msg['role'] in ['user', 'bot']:
                                role = f"Q{conversation_count}" if msg['role'] == 'user' else f"A{conversation_count}"
                                color = colors.HexColor("#4c1d95") if msg['role'] == 'bot' else colors.black
                                elements.append(Paragraph(f"<b>{role}:</b>", ParagraphStyle('Role', parent=body_style, textColor=color)))
                                # Clean HTML from bot messages for PDF
                                content = msg['content']
                                if isinstance(content, str):
                                    # Remove HTML tags for clean PDF content
                                    clean_content = content.replace('<br>', '\n').replace('<strong>', '').replace('</strong>', '')
                                    clean_content = content.replace('<em>', '').replace('</em>', '')
                                    clean_content = content.replace('<code>', '').replace('</code>', '')
                                    clean_content = content.replace('<pre>', '').replace('</pre>', '')
                                    clean_content = content.replace('<div>', '').replace('</div>', '')
                                    clean_content = content.replace('<p>', '').replace('</p>', '')
                                    # Remove common HTML patterns
                                    import re
                                    clean_content = re.sub(r'<[^>]+>', '', clean_content)
                                    elements.append(Paragraph(clean_content, body_style))
                                elements.append(Spacer(1, 8))
                                if msg['role'] == 'bot':
                                    conversation_count += 1
                        elements.append(Spacer(1, 15))
            
            # Fallback to old history format if available
            elif data.get('history'):
                for msg in data['history']:
                    if msg['role'] in ['user', 'bot']:
                        role = f"Q{conversation_count}" if msg['role'] == 'user' else f"A{conversation_count}"
                        color = colors.HexColor("#4c1d95") if msg['role'] == 'bot' else colors.black
                        elements.append(Paragraph(f"<b>{role}:</b>", ParagraphStyle('Role', parent=body_style, textColor=color)))
                        # Clean HTML from bot messages for PDF
                        content = msg['content']
                        if isinstance(content, str):
                            clean_content = content.replace('<br>', '\n').replace('<strong>', '').replace('</strong>', '')
                            elements.append(Paragraph(clean_content, body_style))
                        elements.append(Spacer(1, 8))
                        if msg['role'] == 'bot':
                            conversation_count += 1

            doc.build(elements)
            
            return {
                "success": True,
                "pdf_path": filepath,
                "filename": filename
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
