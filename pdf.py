import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch


PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
styles = getSampleStyleSheet()

page_info = "Generated using ReportLab platypus"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))


def first_page(canvas, doc):
    canvas.saveState()
    canvas.setFont('DejaVu', 16)
    canvas.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 108, ' ')
    canvas.setFont('DejaVu', 10)
    canvas.drawString(inch, 0.75 * inch, '')
    canvas.restoreState()


def later_pages(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman', 9)
    canvas.drawString(inch, 0.75 * inch, '')
    canvas.restoreState()
    
    
def generate_pdf(recipe_list, filename) -> str:
    file_path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(file_path)
    story = [Spacer(1, 2 * inch)]
    style = styles['Normal']
    
    title_style = ParagraphStyle(
            name='TitleStyle',
            parent=style,
            fontName='DejaVu',
            fontSize=20,
            fontWeight='bold',
            spaceAfter=15,
            keepWithNext=True)
    
    ingredients_style = ParagraphStyle(
            name='IngredientsStyle',
            parent=style,
            fontName='DejaVu',
            spaceAfter=12
    )
    
    for name, ingredient in recipe_list:
        title = Paragraph(name.capitalize(), title_style)
        ingredients = Paragraph(ingredient, ingredients_style)
        story.append(title)
        story.append(ingredients)
        story.append(Spacer(1, 0.2 * inch))
        
    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
    
    return file_path
