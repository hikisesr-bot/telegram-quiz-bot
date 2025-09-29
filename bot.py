import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import io
import zipfile
import random
import time
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

# --- Configuration ---
# Securely load the bot token from an environment variable.
API_TOKEN = os.getenv('API_TOKEN')

if not API_TOKEN:
    raise ValueError("No API_TOKEN set. Please set the API_TOKEN environment variable.")

bot = telebot.TeleBot(API_TOKEN)
user_data = {}

# --- AURA Engine v22.0 Logic (Ported from JavaScript to Python) ---
# NOTE: This section contains the same quiz generation logic as the previous version.
# The main changes are in the bot handler section to add the loading screen.

personas = {
    'professor': {'intro': lambda term: f"The following analysis provides a comprehensive examination of {term}."},
    'tutor': {'intro': lambda term: f"Let's break down {term} into simpler, more understandable parts."}
}

unit_plans = {
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

content_matrix = {
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

question_templates = {
    'remembering': lambda subject, concept: f"What is the definition and primary function of {concept['name']} in the context of {subject}?",
    'applying': lambda subject, concept, scenario: f"How would you apply the principle of {concept['name']} to the scenario involving {scenario}?",
    'analyzing': lambda subject, concept1, concept2: f"Analyze the key differences between {concept1['name']} and {concept2['name']} within the field of {subject}.",
    'evaluating': lambda subject, concept, scenario: f"Evaluate the effectiveness of using {concept['name']} as a framework for understanding {scenario}."
}

all_subjects = ['psychology', 'medical_subjects', 'business', 'geek_mythology']

def generate_single_unique_question(subject, used_questions):
    q_text = ""
    attempts = 0
    while attempts < 200:
        skill = random.choice(['remembering', 'applying', 'analyzing', 'evaluating'])
        concepts = content_matrix[subject]['concepts']
        scenarios = content_matrix[subject]['scenarios']
        concept1 = random.choice(concepts)
        
        if skill == 'applying':
            q_text = question_templates['applying'](subject, concept1, random.choice(scenarios))
        elif skill == 'analyzing':
            concept2 = random.choice(concepts)
            while concept2['name'] == concept1['name']:
                concept2 = random.choice(concepts)
            q_text = question_templates['analyzing'](subject, concept1, concept2)
        elif skill == 'evaluating':
            q_text = question_templates['evaluating'](subject, concept1, random.choice(scenarios))
        else:
            q_text = question_templates['remembering'](subject, concept1)
        
        if q_text not in used_questions:
            used_questions.add(q_text)
            return {'q': q_text, 'a': "A detailed, multi-sentence answer.", 'type': skill, 'subject': subject}
        attempts += 1
    return None

def generate_study_packet(subject, level, persona, used_questions):
    plan = random.choice(unit_plans[subject])
    blueprints = [
        {'name': "Exam Prep", 'sections': ['intro', 'assessment_30', 'activity'], 'introText': f"This exam preparation packet for the unit on **{plan['objective'].split(' ')[2]}** is designed for rigorous self-assessment."},
        {'name': "Study Guide", 'sections': ['intro', 'outline', 'key_terms', 'assessment_15'], 'introText': f"This study guide provides a comprehensive thematic outline and key terminology for the unit on **{plan['objective'].split(' ')[2]}**."},
        {'name': "Activity Module", 'sections': ['intro', 'activity', 'outline', 'assessment_10'], 'introText': f"This activity module focuses on the practical application of concepts related to the unit on **{plan['objective'].split(' ')[2]}**."}
    ]
    blueprint = random.choice(blueprints)
    question_count = {'Exam Prep': 30, 'Study Guide': 15, 'Activity Module': 10}.get(blueprint['name'], 10)
    questions = []
    for _ in range(question_count):
        q = generate_single_unique_question(subject, used_questions)
        if q:
            q['s'] = f"{persona['intro']('the concept in question')} This is a detailed, multi-sentence explanation that fully addresses the prompt."
            questions.append(q)
    return {'blueprint': blueprint, 'plan': plan, 'questions': questions}

def add_styled_text(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        if i % 2 == 1:
            paragraph.add_run(part).bold = True
        else:
            paragraph.add_run(part)

def create_docx(subject_name, packet, unique_id):
    document = Document()
    style = document.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(12)
    header = document.sections[0].header
    header.paragraphs[0].text = "Dudai's Academy"
    header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer = document.sections[0].footer
    footer.paragraphs[0].text = f"GenID: {unique_id} | Page #"
    footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph("Name: ____________________________").bold = True
    document.add_paragraph(f"Subject: {subject_name}").bold = True
    document.add_paragraph("School: Dudai's Academy", style='Intense Quote').paragraph_format.space_after = Pt(18)
    plan = packet['plan']
    blueprint = packet['blueprint']
    document.add_heading(f"Professor's Introduction: {plan['objective']}", level=1)
    p_intro = document.add_paragraph()
    add_styled_text(p_intro, blueprint['introText'])
    p_intro.paragraph_format.space_after = Pt(12)
    solution_paragraphs = []
    for section in blueprint['sections']:
        if section == 'outline':
            document.add_heading("Part I: Thematic Outline", level=2)
            for i, line in enumerate(plan['outline']):
                p = document.add_paragraph(line.strip())
                if line.startswith('  '):
                     p.style = 'List Bullet 2'
                else:
                     p.style = 'List Bullet'
        elif section == 'key_terms':
            document.add_heading("Part II: Key Terminology", level=2)
            table = document.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Term'
            hdr_cells[1].text = 'Definition'
            for term in plan['keyTerms']:
                row_cells = table.add_row().cells
                row_cells[0].text = term
                row_cells[1].text = f"Definition for {term}."
        elif section == 'activity':
            document.add_heading("Part III: Application Activity", level=2)
            document.add_paragraph(plan['activity']['scenario'], style='Quote')
            for q in plan['activity']['questions']:
                document.add_paragraph(q['q'], style='List Paragraph')
            solution_paragraphs.append(document.add_heading("Activity Solutions:", level=3))
            for q in plan['activity']['questions']:
                p_sol = document.add_paragraph()
                p_sol.add_run(f"{q['q']} ").bold = True
                p_sol.add_run(f"Answer: {q['a']}")
        elif section.startswith('assessment'):
            document.add_page_break()
            document.add_heading("Part IV: Practice Assessment", level=2)
            for i, q in enumerate(packet['questions']):
                document.add_paragraph(f"{i + 1}. {q['q']}", style='List Number')
            solution_paragraphs.append(document.add_heading("Assessment Solutions:", level=3))
            for i, q in enumerate(packet['questions']):
                p_sol = document.add_paragraph()
                p_sol.add_run(f"Answer {i + 1}: ").bold = True
                add_styled_text(p_sol, q['s'])
    document.add_page_break()
    document.add_heading("Solutions & Explanations", level=1)
    f = io.BytesIO()
    document.save(f)
    f.seek(0)
    return f

# --- Bot Handlers ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the Dudai's Academy Packet Generator!\nUse /gen <number> to start.")

@bot.message_handler(commands=['gen'])
def handle_generation_command(message):
    try:
        count = int(message.text.split()[1])
        if not 1 <= count <= 30:
            bot.reply_to(message, "Please choose a number between 1 and 30.")
            return
        user_id = message.from_user.id
        user_data[user_id] = {'count': count, 'subjects': []}
        markup = InlineKeyboardMarkup(row_width=2)
        buttons = [InlineKeyboardButton(s.replace("_", " ").title(), callback_data=f"subject_{s}") for s in all_subjects]
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("DONE - Continue", callback_data="subjects_done"))
        bot.send_message(message.chat.id, "Step 1: Select subjects, then press DONE.", reply_markup=markup)
    except (IndexError, ValueError):
        bot.reply_to(message, "Please provide a number. Example: `/gen 5`")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if user_id not in user_data:
        bot.answer_callback_query(call.id, "Request expired. Start over with /gen.")
        return

    action, value = call.data.split('_', 1)

    if action == 'subject':
        if value in user_data[user_id]['subjects']:
            user_data[user_id]['subjects'].remove(value)
        else:
            user_data[user_id]['subjects'].append(value)
        bot.answer_callback_query(call.id, f"Toggled {value.replace('_', ' ').title()}")

    elif action == 'subjects' and value == 'done':
        if not user_data[user_id]['subjects']:
            bot.answer_callback_query(call.id, "Please select at least one subject.")
            return
        bot.answer_callback_query(call.id, "Subjects saved!")
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton("Undergraduate", callback_data="level_undergraduate"),
                   InlineKeyboardButton("Advanced", callback_data="level_advanced"))
        bot.edit_message_text("Step 2: Select a level.", chat_id=chat_id, message_id=message_id, reply_markup=markup)

    elif action == 'level':
        user_data[user_id]['level'] = value
        bot.answer_callback_query(call.id, f"Level set to {value.title()}!")
        
        try:
            # --- NEW: Loading Screen Logic ---
            count = user_data[user_id]['count']
            last_reported_percent = -1
            
            # Initial loading message
            bot.edit_message_text(f"⏳ Preparing generation... 0%", chat_id=chat_id, message_id=message_id)

            subjects = user_data[user_id]['subjects']
            level = user_data[user_id]['level']
            
            zip_buffer = io.BytesIO()
            used_questions_batch = set()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i in range(count):
                    # --- Update percentage and message ---
                    percent_done = int(((i + 1) / count) * 100)
                    if percent_done > last_reported_percent:
                        try:
                            # Use a simple progress bar
                            progress_bar = '█' * (percent_done // 10) + '░' * ((100 - percent_done) // 10)
                            bot.edit_message_text(f"⏳ Generating packets...\n[{progress_bar}] {percent_done}%", chat_id=chat_id, message_id=message_id)
                            last_reported_percent = percent_done
                        except Exception as e:
                            # Ignore if message is not modified, which can happen on rapid updates
                            pass

                    # --- Original file generation logic ---
                    subject = random.choice(subjects)
                    persona = random.choice(list(personas.values()))
                    packet = generate_study_packet(subject, level, persona, used_questions_batch)
                    unique_id = f"{int(time.time())}-{random.randint(100,999)}"
                    subject_name_for_doc = subject.replace('_', ' ').title()
                    doc_stream = create_docx(subject_name_for_doc, packet, unique_id)
                    filename = f"DudaisPacket_{subject}_{level[0].upper()}_{i+1}.docx"
                    zipf.writestr(filename, doc_stream.read())
            
            bot.edit_message_text("📦 Compressing files into a ZIP...", chat_id=chat_id, message_id=message_id)
            
            zip_buffer.seek(0)
            user = call.from_user
            mention = f"@{user.username}" if user.username else user.first_name
            caption = f"Here are your {count} study packets, {mention}!"
            
            bot.send_document(chat_id, zip_buffer, visible_file_name="Dudais_Academy_Packets.zip", caption=caption)
            bot.edit_message_text("✅ Generation complete!", chat_id=chat_id, message_id=message_id)

        except Exception as e:
            print(f"An error occurred: {e}")
            bot.edit_message_text(f"An error occurred during generation. Please try again.", chat_id=chat_id, message_id=message_id)
        
        finally:
            del user_data[user_id]

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()

