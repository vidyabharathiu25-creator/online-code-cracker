import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# =========================================================
# TRAINING DATA
# =========================================================

data = {

    "correct": [
        0, 1, 2, 3, 4,
        5, 6, 7, 8, 9, 10,
        2, 4, 6, 7, 8, 9,
        1, 3, 5, 7, 9
    ],

    "wrong": [
        10, 9, 8, 7, 6,
        5, 4, 3, 2, 1, 0,
        7, 5, 3, 2, 1, 0,
        9, 7, 5, 3, 1
    ],

    "skipped": [
        0, 1, 2, 1, 2,
        1, 0, 1, 0, 0, 0,
        1, 1, 0, 1, 0, 0,
        2, 1, 1, 0, 0
    ],

    "time_taken": [
        300, 280, 250, 230, 210,
        190, 170, 150, 120, 100, 80,
        260, 220, 180, 160, 130, 90,
        290, 240, 200, 150, 100
    ],

    "performance": [

        "Needs Improvement",
        "Needs Improvement",
        "Needs Improvement",

        "Average",
        "Average",
        "Average",

        "Good",
        "Good",

        "Excellent",
        "Excellent",
        "Excellent",

        "Needs Improvement",
        "Average",
        "Good",
        "Good",
        "Excellent",
        "Excellent",

        "Needs Improvement",
        "Average",
        "Average",
        "Good",
        "Excellent"

    ]

}


df = pd.DataFrame(data)


# =========================================================
# FEATURES
# =========================================================

FEATURES = [

    "correct",
    "wrong",
    "skipped",
    "time_taken"

]


X = df[FEATURES]

y = df["performance"]


# =========================================================
# MACHINE LEARNING MODEL
# =========================================================

performance_model = Pipeline(

    [

        (

            "scaler",

            StandardScaler()

        ),

        (

            "model",

            RandomForestClassifier(

                n_estimators=200,

                max_depth=8,

                random_state=42

            )

        )

    ]

)


performance_model.fit(X, y)


# =========================================================
# CREATE INPUT DATA
# =========================================================

def create_input(

    correct,

    wrong,

    skipped,

    time_taken

):

    return pd.DataFrame(

        [[

            correct,

            wrong,

            skipped,

            time_taken

        ]],

        columns=FEATURES

    )


# =========================================================
# ML PERFORMANCE PREDICTION
# =========================================================

def predict_performance(

    correct,

    wrong,

    skipped,

    time_taken=100

):

    input_data = create_input(

        correct,

        wrong,

        skipped,

        time_taken

    )


    prediction = performance_model.predict(

        input_data

    )


    return prediction[0]


# =========================================================
# ML PREDICTION PROBABILITY
# =========================================================

def get_prediction_probability(

    correct,

    wrong,

    skipped,

    time_taken=100

):

    input_data = create_input(

        correct,

        wrong,

        skipped,

        time_taken

    )


    probabilities = performance_model.predict_proba(

        input_data

    )[0]


    model = performance_model.named_steps["model"]


    classes = model.classes_


    result = {}


    for label, probability in zip(

        classes,

        probabilities

    ):

        result[label] = round(

            probability * 100,

            2

        )


    return result


# =========================================================
# PERFORMANCE SCORE
# =========================================================

def calculate_performance_score(

    correct,

    wrong,

    skipped,

    total

):

    if total == 0:

        return 0


    accuracy_score = (

        correct / total

    ) * 100


    wrong_penalty = wrong * 1.5

    skipped_penalty = skipped * 2


    score = (

        accuracy_score

        - wrong_penalty

        - skipped_penalty

    )


    return round(

        max(0, min(100, score)),

        2

    )


# =========================================================
# ACCURACY
# =========================================================

def calculate_accuracy(

    correct,

    total

):

    if total == 0:

        return 0


    return round(

        (correct / total) * 100,

        2

    )


# =========================================================
# ATTEMPT RATE
# =========================================================

def calculate_attempt_rate(

    correct,

    wrong,

    skipped,

    total

):

    if total == 0:

        return 0


    attempted = correct + wrong


    return round(

        (attempted / total) * 100,

        2

    )


# =========================================================
# COGNITIVE LEVEL
# =========================================================

def calculate_cognitive_level(

    correct,

    wrong,

    skipped,

    total

):

    if total == 0:

        return "Not Available"


    accuracy = (

        correct / total

    ) * 100


    attempt_rate = (

        (correct + wrong) / total

    ) * 100


    if accuracy >= 80 and skipped <= 1:

        return "Excellent Cognitive Level"


    elif accuracy >= 60 and attempt_rate >= 70:

        return "Good Cognitive Level"


    elif accuracy >= 40:

        return "Average Cognitive Level"


    else:

        return "Needs Improvement"


# =========================================================
# ADAPTIVE DIFFICULTY RECOMMENDATION
# =========================================================

def recommend_level(

    correct,

    wrong,

    skipped

):

    total = correct + wrong + skipped


    if total == 0:

        return "Easy"


    accuracy = (

        correct / total

    ) * 100


    if accuracy >= 80:

        return "Hard"


    elif accuracy >= 50:

        return "Medium"


    else:

        return "Easy"


# =========================================================
# STRENGTH ANALYSIS
# =========================================================

def find_strength(

    correct,

    total

):

    if total == 0:

        return "Not Available"


    accuracy = (

        correct / total

    ) * 100


    if accuracy >= 80:

        return "Excellent Concept Understanding"


    elif accuracy >= 60:

        return "Good Concept Understanding"


    elif accuracy >= 40:

        return "Basic Concept Understanding"


    else:

        return "Needs More Practice"


# =========================================================
# WEAKNESS ANALYSIS
# =========================================================

def find_weakness(

    correct,

    wrong,

    skipped

):

    if skipped >= 3:

        return "Time Management"


    elif wrong > correct:

        return "Concept Understanding"


    elif correct < 5:

        return "Basic Knowledge"


    elif wrong >= 2:

        return "Answer Accuracy"


    else:

        return "No Major Weakness"


# =========================================================
# LEARNING PROFILE
# =========================================================

def get_learning_profile(

    correct,

    wrong,

    skipped,

    total

):

    if total == 0:

        return "Unknown Learner"


    accuracy = (

        correct / total

    ) * 100


    if accuracy >= 80:

        return "Advanced Learner"


    elif accuracy >= 60:

        return "Fast Learner"


    elif accuracy >= 40:

        return "Developing Learner"


    else:

        return "Beginner Learner"


# =========================================================
# AI CONFIDENCE SCORE
# =========================================================

def calculate_confidence(

    probability

):

    if not probability:

        return 0


    confidence = max(

        probability.values()

    )


    return round(

        confidence,

        2

    )


# =========================================================
# PERSONALIZED RECOMMENDATION
# =========================================================

def generate_recommendation(

    correct,

    wrong,

    skipped,

    total

):

    if total == 0:

        return (

            "Attempt more questions to generate "

            "a personalized AI recommendation."

        )


    accuracy = (

        correct / total

    ) * 100


    if accuracy >= 80:

        return (

            "Excellent performance! The AI model "

            "predicts strong conceptual understanding. "

            "You are ready for advanced-level questions."

        )


    elif accuracy >= 60:

        return (

            "Good performance! Continue practicing "

            "medium and hard questions to improve "

            "your accuracy further."

        )


    elif accuracy >= 40:

        return (

            "Average performance. Revise important "

            "concepts and practice regularly to improve "

            "your understanding."

        )


    else:

        return (

            "Needs improvement. Start with basic concepts "

            "and easy-level questions before moving "

            "to higher difficulty levels."

        )


# =========================================================
# RESPONSE TIME ANALYSIS
# =========================================================

def analyze_response_time(

    time_taken,

    total

):

    if total == 0:

        return 0


    average_time = time_taken / total


    return round(

        average_time,

        2

    )


# =========================================================
# COMPLETE AI/ML ANALYSIS
# =========================================================

def complete_ai_analysis(

    correct,

    wrong,

    skipped,

    total,

    time_taken=100

):

    prediction = predict_performance(

        correct,

        wrong,

        skipped,

        time_taken

    )


    probability = get_prediction_probability(

        correct,

        wrong,

        skipped,

        time_taken

    )


    performance_score = calculate_performance_score(

        correct,

        wrong,

        skipped,

        total

    )


    accuracy = calculate_accuracy(

        correct,

        total

    )


    attempt_rate = calculate_attempt_rate(

        correct,

        wrong,

        skipped,

        total

    )


    cognitive_level = calculate_cognitive_level(

        correct,

        wrong,

        skipped,

        total

    )


    recommended_level = recommend_level(

        correct,

        wrong,

        skipped

    )


    strength = find_strength(

        correct,

        total

    )


    weakness = find_weakness(

        correct,

        wrong,

        skipped

    )


    learning_profile = get_learning_profile(

        correct,

        wrong,

        skipped,

        total

    )


    average_response_time = analyze_response_time(

        time_taken,

        total

    )


    confidence = calculate_confidence(

        probability

    )


    recommendation = generate_recommendation(

        correct,

        wrong,

        skipped,

        total

    )


    return {

        "prediction": prediction,

        "probability": probability,

        "confidence": confidence,

        "performance_score": performance_score,

        "accuracy": accuracy,

        "attempt_rate": attempt_rate,

        "cognitive_level": cognitive_level,

        "recommended_level": recommended_level,

        "strength": strength,

        "weakness": weakness,

        "learning_profile": learning_profile,

        "average_response_time": average_response_time,

        "recommendation": recommendation

    }