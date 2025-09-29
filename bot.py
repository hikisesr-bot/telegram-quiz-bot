import random
import io
import uuid
import zipfile
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# --- AURA Engine v22.0 Data Structures (Ported from Quiz.html) ---

def select_random(arr):
    """Selects a random element from a list."""
    return random.choice(arr)

# 1. Personas for answer introductions
PERSONAS = {
    'professor': {'intro': lambda term: f"The following analysis provides a comprehensive examination of {term}."},
    'tutor': {'intro': lambda term: f"Let's break down {term} into simpler, more understandable parts."}
}

# 2. Unit Plans for structure
UNIT_PLANS = {
    'psychology': [{
        'objective': "analyze the principles of classical and operant conditioning.",
        'keyTerms': ["Unconditioned Stimulus", "Conditioned Response", "Reinforcement", "Punishment"],
        'outline': ["I. Introduction to Behaviorism", "  A. John B. Watson", "II. Classical Conditioning (Ivan Pavlov)", "  A. Key Components (UCS, UCR, CS, CR)", "III. Operant Conditioning (B.F. Skinner)", "  A. Reinforcement vs. Punishment"],
        'activity': {'title': "Identifying Conditioning", 'scenario': "A dog learns to salivate at the sound of a bell because the bell has been repeatedly paired with food.", 'questions': [{'q': "Which scenario is an example of classical conditioning?", 'a': "Scenario 1"}]}
    }],
    'medical_subjects': [{
        'objective': "examine the anatomy and primary functions of the human cardiovascular system.",
        'keyTerms': ["Atrium", "Ventricle", "Aorta", "Pulmonary Artery", "Myocardium"],
        'outline': ["I. The Heart: A Four-Chambered Pump", "  A. Right Atrium & Ventricle", "II. Major Blood Vessels", "  A. Arteries & Veins", "III. The Cardiac Cycle", "  A. Systole & Diastole"],
        'activity': {'title': "Tracing a Blood Cell", 'scenario': "Imagine you are a red blood cell starting in the right atrium.", 'questions': [{'q': "What is the first valve you must pass through?", 'a': "The tricuspid valve."}]}
    }],
    'business': [{
        'objective': "analyze core marketing principles.",
        'keyTerms': ["SWOT Analysis", "Target Market", "Marketing Mix (4 Ps)", "Brand Equity"],
        'outline': ["I. The Marketing Concept", "  A. Needs and Wants", "II. Strategic Planning", "  A. SWOT Analysis", "III. The Marketing Mix"],
        'activity': {'title': "Applying the Marketing Mix", 'scenario': "A startup is launching a new brand of premium, eco-friendly coffee beans.", 'questions': [{'q': "Suggest a 'Place' strategy for this company.", 'a': "Online direct-to-consumer sales and partnerships."}]}
    }],
    'geek_mythology': [{
        'objective': "analyze the archetype of the 'hero's journey'.",
        'keyTerms': ["The Call to Adventure", "The Mentor", "The Abyss", "The Return"],
        'outline': ["I. The Monomyth", "  A. Joseph Campbell", "II. Key Stages of the Journey", "  A. Departure", "  B. Initiation", "  C. Return"],
        'activity': {'title': "Identifying the Hero's Journey", 'scenario': "In 'The Lion King,' a young lion prince named Simba is destined to rule.", 'questions': [{'q': "What event represents Simba's 'Call to Adventure'?", 'a': "The birth ceremony establishing his destiny."}]}
    }]
}

# 3. Content Matrix for question generation
CONTENT_MATRIX = {
    'psychology': {
        'concepts': [{'name': "Cognitive Dissonance"}, {'name': "Classical Conditioning"}, {'name': "Operant Conditioning"}, {'name': "Confirmation Bias"}, {'name': "The Bystander Effect"}],
        'scenarios': ["a student justifying cheating", "a person overcoming a phobia", "training a new pet", "evaluating news sources"]
    },
    'medical_subjects': {
        'concepts': [{'name': "the Atrium"}, {'name': "the Ventricle"}, {'name': "the Aorta"}, {'name': "a Neuron"}, {'name': "an Alveolus"}],
        'scenarios': ["tracing the path of a blood cell", "the reflex arc of a knee-jerk", "the process of digestion"]
    },
    'business': {
        'concepts': [{'name': "SWOT Analysis"}, {'name': "Return on Investment (ROI)"}, {'name': "Market Segmentation"}, {'name': "The 4 Ps of Marketing"}],
        'scenarios': ["launching a new tech startup", "a coffee shop improving sales", "a non-profit increasing donations"]
    },
    'geek_mythology': {
        'concepts': [{'name': "The Hero's Journey"}, {'name': "the archetype of the Mentor"}, {'name': "the concept of Hubris"}, {'name': "the Ragnarok prophecy"}],
        'scenarios': ["the story of King Arthur", "the character arc of Harry Potter", "the plot of Star Wars: A New Hope"]
    }
}

# 4. Question Templates
QUESTION_TEMPLATES = {
    'remembering': lambda subject, concept: f"What is the definition and primary function of {concept['name']} in the context of {subject.replace('_', ' ')}?",
    'applying': lambda subject, concept, scenario: f"How would you apply the principle of {concept['name']} to the scenario involving {scenario}?",
    'analyzing': lambda subject, concept1, concept2: f"Analyze the key differences between {concept1['name']} and {concept2['name']} within the field of {subject.replace('_', ' ')}.",
    'evaluating': lambda subject, concept, scenario: f"Evaluate the effectiveness of using {concept['name']} as a framework for understanding {scenario}.",
}

# ------------------- Generation Logic Functions -------------------

def generate_single_unique_question(subject, used_questions):
    """Generates one unique question for a given subject, ensuring uniqueness within the current batch."""
    q_text = ""
    attempts = 0
    
    while True:
        skill = select_random(['remembering', 'applying', 'analyzing', 'evaluating'])
        concepts = CONTENT_MATRIX[subject]['concepts']
        scenarios = CONTENT_MATRIX[subject]['scenarios']
        concept1 = select_random(concepts)
        
        if skill == 'applying':
            q_text = QUESTION_TEMPLATES['applying'](subject, concept1, select_random(scenarios))
        elif skill == 'analyzing':
            c2 = select_random(concepts)
            while c2['name'] == concept1['name']:
                c2 = select_random(concepts)
            q_text = QUESTION_TEMPLATES['analyzing'](subject, concept1, c2)
        elif skill == 'evaluating':
            q_text = QUESTION_TEMPLATES['evaluating'](subject, concept1, select_random(scenarios))
        else: # remembering
            q_text = QUESTION_TEMPLATES['remembering'](subject, concept1)
        
        if q_text not in used_questions:
            break
        
        attempts += 1
        if attempts > 200: # Safety break to prevent infinite loops if concepts run out
            break

    question_data = {'q': q_text, 'a': "A detailed, multi-sentence answer.", 'type': skill, 'subject': subject}
    used_questions.add(q_text)
    return question_data

def generate_study_packet(subject, level, persona_name, used_questions):
    """Generates a complete study packet structure with questions and solutions."""
    
    plan = select_random(UNIT_PLANS[subject])
    persona = PERSONAS[persona_name]
    
    blueprints = [
        {'name': "Exam Prep", 'sections': ['assessment_30', 'activity'], 'introText': f"This exam preparation packet for the unit on **{plan['objective'].split(' ')[-1]}** is designed for rigorous self-assessment."},
        {'name': "Study Guide", 'sections': ['outline', 'key_terms', 'assessment_15'], 'introText': f"This study guide provides a comprehensive thematic outline and key terminology for the unit on **{plan['objective'].split(' ')[-1]}**."},
        {'name': "Activity Module", 'sections': ['activity', 'outline', 'assessment_10'], 'introText': f"This activity module focuses on the practical application of concepts related to the unit on **{plan['objective'].split(' ')[-1]}**."}
    ]
    blueprint = select_random(blueprints)

    question_count = 0
    if 'assessment_30' in blueprint['sections']:
        question_count = 30
    elif 'assessment_15' in blueprint['sections']:
        question_count = 15
    else: # assessment_10
        question_count = 10
    
    # Simple level scaling
    if level == 'advanced':
        question_count = min(30, question_count + 5) # Increase count slightly for Advanced level

    questions = []
    while len(questions) < question_count:
        questions.append(generate_single_unique_question(subject, used_questions))
    
    processed_questions = []
    for q in questions:
        # Generate dynamic solution text
        solution = f"{persona['intro']('the concept in question')} This is a detailed, multi-sentence explanation that fully addresses the prompt, written to feel like original human work."
        processed_questions.append({**q, 's': solution})

    return {'blueprint': blueprint, 'plan': plan, 'questions': processed_questions}

# ------------------- DOCX Utility Functions -------------------

def add_paragraph_with_bold_text(document, text, style='Normal', space_after=Pt(12)):
    """Helper to handle basic **bold** markdown in Python-docx."""
    p = document.add_paragraph(style=style)
    p.paragraph_format.space_after = space_after
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = p.add_run(part)
        if i % 2 == 1:
            run.bold = True
    return p

def create_docx(subject_name, packet, unique_id):
    """Generates a DOCX file from the packet data and returns it as bytes."""
    document = Document()
    
    # Set default style for font size (12pt)
    document.styles['Normal'].font.name = 'Calibri'
    document.styles['Normal'].font.size = Pt(12)

    blueprint = packet['blueprint']
    plan = packet['plan']
    questions = packet['questions']
    
    # 1. Header/Footer Setup (Simplified)
    section = document.sections[0]
    
    # Simple Header: Dudai's Academy
    header = section.header
    header.paragraphs[0].text = "Dudai's Academy"
    header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.paragraphs[0].runs[0].font.size = Pt(9)
    header.paragraphs[0].runs[0].italic = True

    # Simple Footer: Page number and GenID
    footer = section.footer
    footer_p = footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_p.add_run(f"GenID: {unique_id} | Page ")
    
    # Adding Page Number field (Requires direct XML manipulation)
    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'begin')
    footer_p._element.append(fldChar)

    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'
    footer_p._element.append(instrText)

    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'end')
    footer_p._element.append(fldChar)
    
    # 2. Main Content
    
    # Info Block
    p = document.add_paragraph()
    p.add_run("Name: ____________________________").bold = True
    document.add_paragraph(f"Subject: {subject_name}").runs[0].bold = True
    document.add_paragraph(f"School: Dudai's Academy").runs[0].bold = True
    document.add_paragraph().paragraph_format.space_after = Pt(24) # Spacing after block

    # Professor's Intro
    p_intro = document.add_paragraph()
    p_intro.add_run(f"Professor's Introduction: {plan['objective']}").bold = True
    p_intro.runs[0].underline = True

    add_paragraph_with_bold_text(document, blueprint['introText'])

    question_counter = 0

    # 3. Sections Content
    for section_name in blueprint['sections']:
        
        if section_name == 'outline':
            document.add_page_break() 
            document.add_heading("Part I: Thematic Outline", level=2)
            
            # Use built-in list styles
            for line in plan['outline']:
                if line.startswith('  '):
                    document.add_paragraph(line.strip(), style='List Bullet 2')
                else:
                    document.add_paragraph(line.strip(), style='List Number')

        elif section_name == 'key_terms':
            document.add_page_break()
            document.add_heading("Part II: Key Terminology", level=2)
            table = document.add_table(rows=len(plan['keyTerms']) + 1, cols=2)
            table.style = 'Table Grid'
            
            # Table Header
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "Term"
            hdr_cells[1].text = "Definition"
            
            # Table Content
            for i, term in enumerate(plan['keyTerms']):
                row_cells = table.rows[i + 1].cells
                row_cells[0].text = term
                row_cells[1].text = f"Definition for {term}."

        elif section_name == 'activity':
            document.add_page_break()
            document.add_heading("Part III: Application Activity", level=2)
            document.add_paragraph(plan['activity']['scenario']).italic = True
            
            for i, q_data in enumerate(plan['activity']['questions']):
                document.add_paragraph(f"{i + 1}. {q_data['q']}", style='List Number')

        elif 'assessment' in section_name:
            document.add_page_break()
            document.add_heading("Part IV: Practice Assessment", level=2)
            
            # Assessment Questions
            for i, q_data in enumerate(questions):
                question_counter += 1
                add_paragraph_with_bold_text(document, f"{question_counter}. {q_data['q']}", style='List Number')

            # Assessment Solutions (Starts on new page)
            document.add_page_break()
            document.add_heading("Solutions & Explanations", level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            document.add_heading("Assessment Solutions:", level=3)
            
            for i, q_data in enumerate(questions):
                # Question Number Header
                p_num = document.add_paragraph(f"Answer {i + 1}:", style='Heading 4')
                p_num.paragraph_format.space_before = Pt(12)
                
                # Detailed Solution
                add_paragraph_with_bold_text(document, q_data['s'])

    # Save to a byte stream
    file_stream = io.BytesIO()
    document.save(file_stream)
    file_stream.seek(0)
    return file_stream.read()


def generate_zip_file(count, selected_subjects, level, telegram_user_id, username=None):
    """
    Main function to orchestrate the generation and return the ZIP file bytes.
    :param count: Number of files to generate (1-30).
    :param selected_subjects: List of subject keys (e.g., ['psychology', 'business']).
    :param level: 'undergraduate' or 'advanced'.
    :param telegram_user_id: User ID for uniqueness.
    :param username: Username to mention in filenames.
    :return: Bytes of the generated ZIP file.
    """
    zip_buffer = io.BytesIO()
    zip_archive = zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED)
    
    used_questions_this_batch = set()
    persona_name = select_random(list(PERSONAS.keys()))
    
    for i in range(count):
        # Choose subject for this specific file
        subject = select_random(selected_subjects)
        packet = generate_study_packet(subject, level, persona_name, used_questions_this_batch)
        
        unique_id = uuid.uuid4().hex[:8]
        subject_name = subject.replace('_', ' ').title()
        
        # Filename construction
        filename = f"DudaisPacket_{subject_name.replace(' ', '')}_{level[0].upper()}_{i + 1}_{unique_id}.docx"
        
        try:
            doc_bytes = create_docx(subject_name, packet, unique_id)
            zip_archive.writestr(filename, doc_bytes)
        except Exception as e:
            # Log error but continue with the next file
            print(f"Error generating DOCX for file {i+1}: {e}")
            continue 

    zip_archive.close()
    zip_buffer.seek(0)
    return zip_buffer.read()
