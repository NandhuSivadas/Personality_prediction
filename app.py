import json
import joblib
from flask import Flask, render_template, request, redirect, url_for, session, abort
import numpy as np 
import sys
import os
# We no longer need pandas
# import pandas as pd 

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_12345' 

# --- Model and Question Loading ---

# Load the NEW model pipeline
# Correct absolute path for Render & local machine
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.joblib")

print("DEBUG: Trying to load model from:", MODEL_PATH)

try:
    model = joblib.load(MODEL_PATH)
    print("DEBUG: Model loaded successfully!")
except Exception as e:
    model = None
    print("DEBUG: Model failed to load:", e)


# Load all questions from the JSON file
QUESTIONS_PATH = os.path.join(BASE_DIR, "questions.json")

try:
    with open(QUESTIONS_PATH, 'r') as f:
        all_questions = json.load(f)
    print(f"Loaded {len(all_questions)} questions successfully.")
except Exception as e:
    print(f"FATAL ERROR loading questions.json: {e}")
    all_questions = []


# --- Constants ---
QUESTIONS_PER_PAGE = 5
TRAIT_NAMES = ['Extraversion', 'Neuroticism', 'Agreeableness', 'Conscientiousness', 'Openness']

# --- Error Handling & Main Routes ---
@app.before_request
def check_questions_loaded():
    if request.endpoint in ['static', 'load_error']:
        return
    if not all_questions:
        return redirect(url_for('load_error'))
    
@app.route('/load-error')
def load_error():
    message = ("'questions.json' could not be loaded. Please check the server console.")
    return render_template('error.html', error_message=message), 500

# --- Main Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

# --- Test-Taking Routes ---
@app.route('/test/start')
def start_test():
    session['answers'] = {}
    session['current_page'] = 1
    return redirect(url_for('test_page', page_num=1))

@app.route('/test/<int:page_num>', methods=['GET', 'POST'])
def test_page(page_num):
    total_pages = (len(all_questions) + QUESTIONS_PER_PAGE - 1) // QUESTIONS_PER_PAGE
    if page_num < 1 or page_num > total_pages:
        return redirect(url_for('start_test')) 
    start_index = (page_num - 1) * QUESTIONS_PER_PAGE
    end_index = min(page_num * QUESTIONS_PER_PAGE, len(all_questions))
    current_questions = all_questions[start_index:end_index]
    if request.method == 'POST':
        for question in current_questions:
            answer = request.form.get(question['id'])
            if answer:
                session['answers'][question['id']] = int(answer)
        session.modified = True 
        if page_num < total_pages:
            return redirect(url_for('test_page', page_num=page_num + 1))
        else:
            return redirect(url_for('show_result'))
    return render_template(
        'test_page.html',
        page_num=page_num,
        questions=current_questions,
        total_pages=total_pages
    )

@app.route('/result')
def show_result():
    if 'answers' not in session or len(session['answers']) != len(all_questions):
        return redirect(url_for('start_test'))
    if model is None:
        print("DEBUG: Model variable is None!")
        return "Error: Prediction model is not loaded. Cannot provide a prediction.", 500

    model_type = type(model).__name__
    print(f"\n=== DEBUG DIAGNOSTICS ===")
    print(f"1. Model Type Loaded: {model_type}")
    if model_type == 'Pipeline':
        print("   ❌ WARNING: You are still using the OLD Pipeline model!")
    else:
        print("   ✅ SUCCESS: You are using the NEW Raw model!")

    try:
        # 1. This is the correct reverse-scoring list from your Colab notebook
        reverse_scored_keys = [
            "EXT2","EXT4","EXT6","EXT8","EXT10",
            "EST1","EST3","EST5","EST6","EST7","EST8","EST9","EST10",
            "AGR1","AGR3","AGR5","AGR7",
            "CSN2","CSN4","CSN6","CSN8",
            "OPN2","OPN4","OPN6"
        ]

        # 2. This is the correct feature order from your Colab notebook
        COLAB_FEATURE_ORDER = [
            'EXT1','EXT2','EXT3','EXT4','EXT5','EXT6','EXT7','EXT8','EXT9','EXT10',
            'EST1','EST2','EST3','EST4','EST5','EST6','EST7','EST8','EST9','EST10',
            'AGR1','AGR2','AGR3','AGR4','AGR5','AGR6','AGR7','AGR8','AGR9','AGR10',
            'CSN1','CSN2','CSN3','CSN4','CSN5','CSN6','CSN7','CSN8','CSN9','CSN10',
            'OPN1','OPN2','OPN3','OPN4','OPN5','OPN6','OPN7','OPN8','OPN9','OPN10'
        ]

        # 3. Process the answers (reverse-scoring)
        processed_answers = {}
        user_answers = session['answers']
        for q_id in COLAB_FEATURE_ORDER:
            answer = user_answers[q_id]
            # if q_id in reverse_scored_keys:
            #     processed_answers[q_id] = 6 - answer
            # else:
            #     processed_answers[q_id] = answer
            processed_answers[q_id] = answer

        # 4. Build the final features list *in the correct order*
        features = [processed_answers[q_id] for q_id in COLAB_FEATURE_ORDER]

        # 5. Create a simple NumPy array. No more DataFrame.
        features_array = [np.array(features)]
        
    except KeyError as e:
        return f"Error: A question ID was missing from the session: {e}. Please retake the test.", 500
    except Exception as e:
        return f"Error preparing features: {e}", 500

    try:
        # 6. Predict using the pipeline.
        #    The pipeline will *automatically* scale the data (step 1)
        #    and then predict (step 2).
        prediction_scores = model.predict(features_array)[0] 
        print(f"2. Raw Prediction Scores: {prediction_scores}")

        # 7. This is the correct percentage calculation: (score / 5) * 100
        scores_percent = [(score / 5) * 100 for score in prediction_scores]
        print(f"3. Calculated Percentages: {scores_percent}")
        print("=========================\n")
        
        results = list(zip(TRAIT_NAMES, scores_percent))        
        highest_trait = max(results, key=lambda item: item[1])

        session['results'] = results 
        session.modified = True
        
        return render_template(
            'result.html',
            results=results,
            scores_json=json.dumps(scores_percent), 
            labels_json=json.dumps(TRAIT_NAMES),
            highest_trait=highest_trait
        )
    
    except Exception as e:
        # The "feature names" warning will now be GONE
        return f"Error during prediction: {e}. Check your model's expected input shape.", 500

# --- Static (non-AI) Suggestion Routes ---
@app.route('/career-suggestions')
def career_suggestions():
    # 1. Safety Check: Make sure they have results
    if 'results' not in session:
        return redirect(url_for('index'))
    
    results = session['results'] 
    scores = dict(results)

    # 2. Find the highest trait
    # 'results' is a list of tuples: [('Openness', 81.0), ('Extraversion', 67.3)...]
    high_trait_name, high_score = max(results, key=lambda item: item[1])

    # 3. The "Persona Database" - Fully written content
    persona_db = {
        "Openness": {
            "title": "The Innovator",
            "description": "You thrive on new ideas, creativity, and abstract thinking. You dislike routine and prefer environments that allow you to explore possibilities and solve complex problems.",
            "careers": ["UX/UI Designer", "Research Scientist", "Creative Director", "Entrepreneur", "Architect", "Writer/Author"]
        },
        "Conscientiousness": {
            "title": "The Strategist",
            "description": "You are organized, dependable, and disciplined. You excel in roles that require attention to detail, planning, and execution. You are the one who gets things done on time and to a high standard.",
            "careers": ["Project Manager", "Accountant/Auditor", "Software Engineer", "Surgeon", "Legal Counsel", "Operations Manager"]
        },
        "Extraversion": {
            "title": "The Connector",
            "description": "You draw energy from interacting with others. You are persuasive, enthusiastic, and action-oriented. You excel in dynamic environments where communication and leadership are key.",
            "careers": ["Sales Manager", "Public Relations Specialist", "Event Planner", "Politician", "Teacher/Educator", "Recruiter"]
        },
        "Agreeableness": {
            "title": "The Diplomat",
            "description": "You are cooperative, empathetic, and people-oriented. You value harmony and are driven to help others. You thrive in supportive roles where emotional intelligence is a superpower.",
            "careers": ["Human Resources Manager", "Social Worker", "Nurse/Healthcare", "Counselor/Therapist", "Non-Profit Manager", "Customer Success"]
        },
        "Neuroticism": {
            "title": "The Sentinel",
            "description": "You are sensitive to risks and details that others miss. While you may experience stress more intensely, this makes you excellent at spotting errors, anticipating problems, and ensuring quality.",
            "careers": ["Quality Assurance Analyst", "Risk Manager", "Archivist/Librarian", "Data Analyst", "Safety Inspector", "Editor"]
        },
        "Balanced": {
            "title": "The Adaptable Professional",
            "description": "Your personality is well-balanced, meaning you can adapt to a wide variety of situations. You can be social when needed but focus deeply when required. You are a versatile asset to any team.",
            "careers": ["General Manager", "Consultant", "Administrator", "Product Manager", "Communications Officer"]
        }
    }

    # 4. Determine the Persona
    # If the score is high enough (> 65%), use that trait. Otherwise, they are "Balanced".
    HIGH_SCORE_THRESHOLD = 65.0
    
    if high_score >= HIGH_SCORE_THRESHOLD:
        # FIX: We use 'high_trait_name' directly (e.g., "Openness"), NOT 'high_trait_name[0]'
        persona = persona_db.get(high_trait_name, persona_db["Balanced"])
    else:
        persona = persona_db["Balanced"]

    return render_template(
        'suggestions.html', 
        persona_title=persona["title"], 
        persona_description=persona["description"], 
        career_list=persona["careers"], 
        scores=scores
    )


@app.route('/personal-growth')
def personal_growth():
    if 'results' not in session:
        return redirect(url_for('index'))
    
    results = session['results'] 
    
    # 1. The Growth Tips Database
    tips_db = {
        "Openness": {
            "high": "<strong>Your mind is a universe of infinite possibilities.</strong><br>Your challenge is execution. Pick just <em>one</em> of your brilliant ideas and commit to finishing it before starting the next one.",
            "low": "<strong>You are the anchor of reality and tradition.</strong><br>To expand your horizons, break one routine this week. Take a different route to work, watch a documentary on a weird topic, or eat a cuisine you've never tried.",
            "balanced": "<strong>You are the bridge between the visionary and the pragmatist.</strong><br>You have the unique ability to take a radical idea and make it work in the real world. Use this to lead teams effectively."
        },
        "Conscientiousness": {
            "high": "<strong>Your drive for perfection is impressive but exhausting.</strong><br>Remember that 'done' is often better than 'perfect.' Schedule one hour this week specifically for doing absolutely nothing productive.",
            "low": "<strong>You are a master of adaptability and improvisation.</strong><br>To reduce chaos, anchor your day with just one 'keystone habit'—like making your bed every morning—to build a foundation of order.",
            "balanced": "<strong>You have the rare gift of flexible discipline.</strong><br>You can hustle when deadlines approach but know how to relax when the work is done. Keep protecting that work-life boundary."
        },
        "Extraversion": {
            "high": "<strong>You shine brightest when connected to others.</strong><br>However, constant stimulation can mask your inner voice. Spend 30 minutes alone in nature or silence to reconnect with who you are when no one is watching.",
            "low": "<strong>You possess a rich and complex inner world.</strong><br>Don't let your best thoughts stay hidden. Challenge yourself to voice one opinion in a meeting or group chat this week, even if it feels uncomfortable.",
            "balanced": "<strong>You are the ultimate social chameleon (The Ambivert).</strong><br>You can lead a party or enjoy a book. Your growth lies in recognizing your current energy level and honoring it without guilt."
        },
        "Agreeableness": {
            "high": "<strong>Your empathy is a superpower, but don't let it become a weakness.</strong><br>You likely over-commit to help others. Practice the '24-hour rule': Wait one full day before saying 'Yes' to any new request.",
            "low": "<strong>You are a truth-teller who values facts over feelings.</strong><br>Your logic is sound, but delivery matters. Before critiquing someone, start by validating their effort or perspective to ensure they actually hear you.",
            "balanced": "<strong>You are a fair but firm negotiator.</strong><br>You understand people's needs but don't let them walk all over you. You are perfectly suited for conflict resolution and management roles."
        },
        "Neuroticism": {
            "high": "<strong>You feel the world deeply and spot risks others miss.</strong><br>Your anxiety is often just overactive creativity. When you spiral into 'what if' scenarios, force yourself to write down three 'what if things go right' scenarios.",
            "low": "<strong>You are the calm eye of the storm.</strong><br>Your stability is comforting, but be careful not to dismiss others' stress as irrational. Practice saying, 'I can see why that upsets you,' even if you don't feel it yourself.",
            "balanced": "<strong>You possess high emotional intelligence.</strong><br>You are aware of danger and stress, but you don't let it paralyze you. Trust your gut instincts—they are likely calibrated correctly."
        }
    }

    # 2. Process the data for the template
    growth_data = []
    
    for trait, score in results:
        # Determine if the score is High, Low, or Balanced
        if score >= 65:
            level = "high"
            display_level = "High"
        elif score <= 45:
            level = "low"
            display_level = "Low"
        else:
            level = "balanced"
            display_level = "Balanced"
            
        # Get the specific tip
        tip = tips_db.get(trait, {}).get(level, "Keep exploring your potential.")
        
        growth_data.append({
            "trait": trait,
            "score": score,
            "level": display_level, # e.g., "High"
            "level_key": level,     # e.g., "high" (for CSS styling)
            "tip": tip
        })

    return render_template('growth_tips.html', growth_data=growth_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)

    # app.run(debug=True)  # Uncomment for local debugging
