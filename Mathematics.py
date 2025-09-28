import math

def calculate_scores(questions_data, interview_config):
    """
    Calculates candidate interview scores based on a list of question data
    and interview configuration.

    Args:
        questions_data (list): A list of dictionaries, where each dictionary
                               contains the parameters for one question.
        interview_config (dict): A dictionary containing interview-wide
                                 weights and the hint budget.

    Returns:
        dict: A dictionary containing all the calculated scores.
    """
    # Epsilon to prevent division by zero
    epsilon = 1e-6
    
    # Lists to store scores for each question
    ps_scores = []
    code_scores = []
    resilience_scores = []
    
    # Variables for interview-wide calculations
    total_hints_score = 0
    total_difficulty = 0
    num_questions = len(questions_data)

    # --- 1. Calculate scores for each question ---
    for q in questions_data:
        # Problem-Solving Score
        think_ratio_term = math.exp(-((q['T_think'] / q['T_total']) - 0.3)**2)
        score_ps = 10 * (0.6 * (q['E_covered'] / q['E_total']) + 0.4 * min(1, think_ratio_term))
        ps_scores.append(score_ps)
        
        # Coding Proficiency Score
        improvement_numerator = q['C_initial'] - q['C_final']
        improvement_denominator = q['C_initial'] - q['C_target'] + epsilon
        improvement_factor = max(0, min(1, improvement_numerator / improvement_denominator))
        
        keystroke_efficiency = q['K_useful'] / q['K_total'] if q['K_total'] > 0 else 0
        score_code = 10 * (0.5 * improvement_factor + 0.3 * q['S_lint'] + 0.2 * keystroke_efficiency)
        code_scores.append(score_code)

        # Resilience Score
        stuck_ratio = q['T_stuck'] / q['T_total'] if q['T_total'] > 0 else 1
        score_resilience = 10 * ((1 - stuck_ratio) * q['S_sentiment'])
        resilience_scores.append(score_resilience)

        # Accumulate totals for final scores
        total_hints_score += sum(q.get('H_types', []))
        total_difficulty += q['Q_difficulty']

    # --- 2. Calculate average and interview-wide scores ---
    avg_score_ps = sum(ps_scores) / num_questions if num_questions > 0 else 0
    avg_score_code = sum(code_scores) / num_questions if num_questions > 0 else 0
    avg_score_resilience = sum(resilience_scores) / num_questions if num_questions > 0 else 0

    # Autonomy Score (calculated once for the whole interview)
    autonomy_denominator = total_difficulty * interview_config.get('hint_budget', 1.0)
    autonomy_term = 1 - (total_hints_score / autonomy_denominator) if autonomy_denominator > 0 else 1
    score_autonomy = 10 * max(0, autonomy_term)

    # --- 3. Calculate the final Overall Score ---
    w = interview_config['weights']
    base_score_numerator = (w['ps'] * avg_score_ps + w['code'] * avg_score_code +
                            w['resilience'] * avg_score_resilience + w['autonomy'] * score_autonomy)
    base_score_denominator = sum(w.values())
    base_score = base_score_numerator / base_score_denominator

    difficulty_factor = total_difficulty / (3 * num_questions) if num_questions > 0 else 1
    score_overall = base_score * (0.8 + 0.4 * difficulty_factor)

    # --- 4. Compile and return results ---
    return {
        "Problem-Solving Score": round(avg_score_ps, 2),
        "Coding Proficiency Score": round(avg_score_code, 2),
        "Resilience Score": round(avg_score_resilience, 2),
        "Autonomy Score": round(score_autonomy, 2),
        "Overall Score": round(score_overall, 2),
        "Details": {
            "Base Score": round(base_score, 2),
            "Difficulty Factor": round(difficulty_factor, 2)
        }
    }


# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    # Define the parameters for the interview
    # This candidate answered two questions: one medium, one hard.
    candidate_interview_data = [
        {
            # Question 1: Medium
            "T_think": 120, "T_total": 600, "T_stuck": 45,
            "E_covered": 3, "E_total": 4,
            "C_initial": 2.0, "C_final": 1.0, "C_target": 1.0,
            "S_lint": 0.85, "K_useful": 400, "K_total": 550,
            "S_sentiment": 0.8,
            "H_types": [1],  # Required one small "nudge" hint
            "Q_difficulty": 2,
        },
        {
            # Question 2: Hard
            "T_think": 300, "T_total": 1200, "T_stuck": 150,
            "E_covered": 4, "E_total": 6,
            "C_initial": 2.5, "C_final": 1.5, "C_target": 1.5,
            "S_lint": 0.70, "K_useful": 800, "K_total": 1100,
            "S_sentiment": 0.7,
            "H_types": [1, 2],  # Required a nudge and a guide
            "Q_difficulty": 3,
        }
    ]

    # Define the weights and budget for this role
    interview_setup = {
        "weights": {
            "ps": 0.4,
            "code": 0.3,
            "resilience": 0.1,
            "autonomy": 0.2,
        },
        "hint_budget": 1.0 # Standard hint allowance
    }

    # Calculate the scores
    final_scores = calculate_scores(candidate_interview_data, interview_setup)

    # Print the output
    print("--- Candidate Final Scores ---")
    for score_name, score_value in final_scores.items():
        if isinstance(score_value, dict):
            print(f"\n--- {score_name} ---")
            for detail_name, detail_value in score_value.items():
                print(f"{detail_name}: {detail_value}")
        else:
            print(f"{score_name}: {score_value}")
