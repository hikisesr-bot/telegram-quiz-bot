import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import io
import zipfile
import random
import time
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- Configuration ---
# Securely load the bot token from an environment variable.
# This is essential for deploying on services like Choreo.
API_TOKEN = os.getenv('API_TOKEN')

if not API_TOKEN:
    raise ValueError("No API_TOKEN set. Please set the API_TOKEN environment variable.")

bot = telebot.TeleBot(API_TOKEN)

# In-memory storage for user choices during the generation process
user_data = {}

# --- AURA Engine v5.0 Logic (Ported from JavaScript to Python) ---
# NOTE: The AURA engine logic below is the same as the previous version.
# Only the API_TOKEN handling at the top has been changed for security.

personas = {
    'professor': {
        'intro': lambda term: f"The following analysis provides a comprehensive examination of {term}.",
        'steps': ["Theoretical Framework:", "Empirical Application:", "Scholarly Significance:"],
        'connector': "Furthermore,"
    },
    'tutor': {
        'intro': lambda term: f"Let's break down {term} into simpler, more understandable parts.",
        'steps': ["Step 1: The Basics", "Step 2: A Clear Example", "Step 3: Why It Matters"],
        'connector': "Next,"
    },
    'practitioner': {
        'intro': lambda term: f"From a practical standpoint, here is how {term} is applied in the real world.",
        'steps': ["Core Function:", "Case Study:", "Business Impact:"],
        'connector': "In practice,"
    }
}

citations = {
    'business': ['(ref: Porter, M. E., "Competitive Strategy", 1980)'],
    'history': ['(Source: Tuchman, B. W., "The Guns of August", 1962)'],
    'psychology': ['(ref: Festinger, L., "A Theory of Cognitive Dissonance", 1957)'],
    'medical_subjects': ['(Source: "Gray\'s Anatomy for Students")'],
    'geek_mythology': ['(ref: Hamilton, E., "Mythology: Timeless Tales of Gods and Heroes")']
}

question_templates = {
    'interdisciplinary': {
        'business-history': [
            lambda: {
                'type': 'case_study', 'title': 'The Dutch East India Company (VOC)',
                'scenario': 'The Dutch East India Company (VOC), founded in 1602, is often considered the world\'s first multinational corporation...',
                'questions': [
                    {'q': 'From a (Business) perspective, identify two key competitive advantages the VOC possessed.', 'a': 'Monopolistic control and a vertically integrated supply chain.'},
                    {'q': 'From a (History) perspective, explain how the VOC\'s actions impacted the political landscape of Southeast Asia.', 'a': 'It established colonial rule and altered regional power structures.'},
                    {'q': 'Analyze the primary internal (Business) factor that led to the VOC\'s decline.', 'a': 'Widespread corruption and private trading by employees.'}
                ],
                's': lambda p, c: f"{p['intro']('the VOC case study')}\n**Business Advantages:** The VOC's government-granted **monopoly** eliminated competition. {c}\n**Historical Impact:** The VOC used its military power to violently displace rivals. {c}\n**Internal Decline:** The company was plagued by **corruption**. {c}"
            }
        ],
        'medical_subjects-psychology': [
             lambda: {
                'type': 'case_study', 'title': 'The Placebo Effect in Clinical Trials',
                'scenario': 'In a double-blind clinical trial for a new antidepressant, 40% of patients in the control group... reported significant symptom reduction.',
                'questions': [
                    {'q': 'From a (Psychology) perspective, define the phenomenon observed.', 'a': 'The Placebo Effect.'},
                    {'q': 'From a (Medical) perspective, why is a placebo control group necessary?', 'a': 'To differentiate the drug\'s true pharmacological effects from patient expectations.'},
                    {'q': 'Analyze the (Psychology) mechanism of \'expectancy theory\' in this case.', 'a': 'Patients\' belief in a treatment can trigger real physiological and psychological changes.'}
                ],
                's': lambda p, c: f"{p['intro']('the placebo effect')}\n**Psychological Definition:** This is a classic example of the **Placebo Effect**. {c}\n**Medical Necessity:** Placebo controls are the gold standard to isolate a drug\'s specific biochemical effects. {c}\n**Expectancy Theory:** This theory suggests a patient\'s expectations are a major driver of the placebo response. {c}"
            }
        ]
    }
}

all_subjects = ['business', 'history', 'psychology', 'medical_subjects', 'geek_mythology']
for subj in all_subjects:
    question_templates[subj] = {
        'undergraduate': {
            'remembering': [lambda s=subj: {'q': f'Define a key term in {s}.', 'a': "A key term.", 'type': 'remembering', 's': lambda p,c: f"{p['intro']('this term')}...This is a foundational concept. {c}" }],
            'applying': [lambda s=subj: {'q': f'Apply a concept from {s}.', 'a': "An application.", 'type': 'applying', 's': lambda p,c: f"{p['intro']('this concept')}...This demonstrates its practical use. {c}" }]
        },
        'advanced': {
            'analyzing': [lambda s=subj: {'q': f'Analyze a topic in {s}.', 'a': "An analysis.", 'type': 'analyzing', 's': lambda p,c: f"{p['intro']('this topic')}...A deeper look reveals key components. {c}" }],
            'evaluating': [lambda s=subj: {'q': f'Evaluate a statement about {s}.', 'a': "An evaluation.", 'type': 'evaluating', 's': lambda p,c: f"{p['intro']('this statement')}...Assessing its validity requires considering multiple factors. {c}" }]
        }
    }

def generate_unique_question(subjects, level, persona):
    subjects.sort()
    interdisciplinary_key = '-'.join(subjects)
    
    if len(subjects) > 1 and interdisciplinary_key in question_templates['interdisciplinary'] and random.random() > 0.3:
        template = random.choice(question_templates['interdisciplinary'][interdisciplinary_key])
        q_data = template()
        citation = random.choice(citations[subjects[0]])
        return {**q_data, 's': q_data['s'](persona, citation)}

    subject = random.choice(subjects)
    cognitive_skill = random.choice(list(question_templates[subject][level].keys()))
    template = random.choice(question_templates[subject][level][cognitive_skill])
    q_data = template()
    citation = random.choice(citations[subject])
    return {**q_data, 's': q_data['s'](persona, citation)}

def create_docx(subject_name, questions, unique_id):
    document = Document()
    style = document.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(12)
    header = document.sections[0].header
    header_p = header.paragraphs[0]
    header_p.text = "Dudai's Academy - Comprehensive Exam Review"
    header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer = document.sections[0].footer
    footer_p = footer.paragraphs[0]
    footer_p.text = f"GenID: {unique_id} | Page #"
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph(f"Name: ____________________________").bold = True
    document.add_paragraph(f"Subject: {subject_name}").bold = True
    p = document.add_paragraph()
    p.add_run("School: Dudai's Academy").bold = True
    p.paragraph_format.space_after = Pt(18)
    document.add_heading("Introduction", level=1)
    intro_text = f"This document covers key topics in {subject_name}. The questions are designed to test multiple levels of understanding."
    document.add_paragraph(intro_text, style='Intense Quote')
    solutions = []
    question_counter = 1
    for q in questions:
        if q['type'] == 'case_study':
            document.add_heading(f"Case Study {question_counter}: {q['title']}", level=2)
            document.add_paragraph(q['scenario'])
            for i, sq in enumerate(q['questions']):
                document.add_paragraph(f"   {question_counter}.{i+1}. {sq['q']}", style='List Paragraph')
            solutions.append(f"Analysis for Case Study {question_counter}: {q['title']}\n{q['s']}")
            question_counter += len(q['questions'])
        else:
            document.add_paragraph(f"{question_counter}. {q['q']}", style='List Number')
            solutions.append(f"Analysis for Question {question_counter} ({q['type']}):\n{q['s']}")
            question_counter += 1
    document.add_page_break()
    document.add_heading("Solutions & Explanations", level=1)
    for sol in solutions:
        document.add_paragraph(sol)
    f = io.BytesIO()
    document.save(f)
    f.seek(0)
    return f

# --- Bot Command Handlers & Callback Handlers ---
# NOTE: This logic is also unchanged from the previous version.

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Welcome to the Dudai's Academy Quiz Generator Bot!\n\n"
        "To start, use the command: `/gen <number>`\n\n"
        "For example: `/gen 5`\n\n"
        "You can generate between 1 and 30 quiz files at a time."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['gen'])
def handle_generation_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "Please provide a number after the /gen command.\nExample: `/gen 5`")
            return
        count = int(parts[1])
        if not 1 <= count <= 30:
            bot.reply_to(message, "Please choose a number between 1 and 30.")
            return
        user_id = message.from_user.id
        user_data[user_id] = {'count': count, 'subjects': []}
        markup = InlineKeyboardMarkup(row_width=2)
        buttons = [InlineKeyboardButton(s.replace("_", " ").title(), callback_data=f"subject_{s}") for s in all_subjects]
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("DONE - Generate Quizzes", callback_data="subjects_done"))
        bot.send_message(message.chat.id, "Step 1: Select one or more subjects, then press DONE.", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if user_id not in user_data:
        bot.answer_callback_query(call.id, "This request has expired. Please start over with /gen.")
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
            bot.answer_callback_query(call.id, "Error: Please select at least one subject first.")
            return
        bot.answer_callback_query(call.id, "Subjects selected!")
        markup = InlineKeyboardMarkup(row_width=2)
        btn_ug = InlineKeyboardButton("Undergraduate", callback_data="level_undergraduate")
        btn_adv = InlineKeyboardButton("Advanced", callback_data="level_advanced")
        markup.add(btn_ug, btn_adv)
        bot.edit_message_text("Step 2: Select a level.", chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
    elif action == 'level':
        user_data[user_id]['level'] = value
        bot.answer_callback_query(call.id, f"Level set to {value.title()}!")
        try:
            bot.edit_message_text(f"Generating {user_data[user_id]['count']} quiz files... Please wait.", chat_id=chat_id, message_id=call.message.message_id)
            count = user_data[user_id]['count']
            subjects = user_data[user_id]['subjects']
            level = user_data[user_id]['level']
            subject_name_for_doc = ' & '.join([s.replace('_', ' ').title() for s in subjects])
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i in range(count):
                    persona = random.choice(list(personas.values()))
                    questions = []
                    q_count = 0
                    while q_count < 20:
                        q = generate_unique_question(subjects, level, persona)
                        questions.append(q)
                        q_count += len(q.get('questions', [1]))
                    unique_id = f"{int(time.time())}-{random.randint(100,999)}"
                    doc_stream = create_docx(subject_name_for_doc, questions, unique_id)
                    filename = f"DudaisQuiz_{subject_name_for_doc.replace(' & ', '-')}_{level[0].upper()}_{i+1}.docx"
                    zipf.writestr(filename, doc_stream.read())
            zip_buffer.seek(0)
            user = call.from_user
            mention = f"@{user.username}" if user.username else user.first_name
            caption = f"Here are your {count} quiz files, {mention}!"
            bot.send_document(chat_id, zip_buffer, visible_file_name="Dudais_Academy_Quizzes.zip", caption=caption)
            bot.edit_message_text("✅ Generation complete!", chat_id=chat_id, message_id=call.message.message_id)
        except Exception as e:
            bot.edit_message_text(f"Sorry, an error occurred during generation: {e}", chat_id=chat_id, message_id=call.message.message_id)
        finally:
            del user_data[user_id]

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()

