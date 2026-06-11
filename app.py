import streamlit as st
import pandas as pd
import json
import re
import requests

# --- JSONBin Configuration ---
# Securely pulls your API key from Streamlit's dashboard secrets
JSONBIN_API_KEY = st.secrets["JSONBIN_API_KEY"] 
WORKOUT_BIN_ID = "6a2b09def5f4af5e29e1925d"
MAPPING_BIN_ID = "6a2b099bda38895dfeb00e71"

BASE_URL = "https://api.jsonbin.io/v3/b/"
HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

# Your full historical mapping dictionary
INITIAL_MAPPING = {
    "20 lb Superset": "Arms, Shoulders",
    "45 degree glute hyper": "Glutes, Hamstrings",
    "45-Degree Glute Hyper": "Glutes/Hamstrings",
    "45-Degree Glute Hypers": "Glutes/Hamstrings",
    "45° Glute Hyper": "Glutes, Hamstrings",
    "Ab Wheel": "Core",
    "Abduction Machine": "Glutes",
    "Arm Pyramid": "Arms",
    "B-Stance DB RDL": "Hamstrings, Glutes",
    "Back Squat": "Quads, Glutes",
    "Banded Frog Pumps": "Glutes",
    "Banded Glute Bridges": "Glutes",
    "Barbell Curl": "Arms",
    "Barbell Hip Thrust": "Glutes",
    "Barbell RDL": "Hamstrings, Glutes",
    "Belted Hip Thrust": "Glutes",
    "Bench Press": "Chest, Shoulders, Arms",
    "Bicep Cable Curl": "Biceps",
    "Bicep Curl": "Biceps",
    "Bicep Curls": "Biceps",
    "Body Weight Lunges": "Quads, Glutes",
    "Bodyweight": "Chest, Back, Arms",
    "Cable Curls": "Arms",
    "Cable Pulldown / Pushdown": "Back, Triceps",
    "Chest Fly": "Chest",
    "Chest Press": "Chest, Shoulders, Arms",
    "Conventional Deadlift": "Glutes, Hamstrings, Back",
    "Crunch Machine": "Core",
    "Curl / Lateral / Press": "Biceps, Shoulders",
    "Curl / Press / Lateral": "Biceps, Shoulders",
    "DB Bent Over Row": "Back, Biceps",
    "DB Bicep Curls": "Biceps",
    "DB Curl": "Biceps",
    "DB Deficit RDL": "Hamstrings, Glutes",
    "DB Deficit SLDL": "Hamstrings, Glutes",
    "DB Floor Press": "Chest, Triceps",
    "DB Overhead Press": "Shoulders, Triceps",
    "DB RDL (75 lb)": "Hamstrings, Glutes",
    "DB RDL (Deficit)": "Hamstrings, Glutes",
    "DB Seated Shoulder Press": "Shoulders, Triceps",
    "DB Shoulder Press": "Shoulders, Triceps",
    "DB Side Laterals": "Shoulders",
    "DB Superset": "Arms, Shoulders",
    "DB Superset (15lb)": "Arms, Shoulders",
    "DB Superset (20lb)": "Arms, Shoulders",
    "Deadlift": "Glutes, Hamstrings, Back",
    "Deadlift (Demo)": "Glutes, Hamstrings, Back",
    "Deadlifts": "Hamstrings/Glutes/Back",
    "Deep Deficit DB RDL": "Hamstrings, Glutes",
    "Deep Deficit Rear Lunge": "Glutes/Quads",
    "Deep Goblet Squat": "Quads/Glutes",
    "Deficit DB RDL": "Hamstrings, Glutes",
    "Deficit Rear Lunges": "Glutes/Quads",
    "Dumbbell Shoulder Press": "Shoulders/Triceps",
    "Dumbbell Sumo Squat": "Glutes, Adductors",
    "Elliptical": "Full Body",
    "FST-7 Glute Machine": "Glutes",
    "Farmer's Walk": "Full Body",
    "GVT Glute Machine": "Glutes",
    "Glute Bias Leg Press": "Quads, Glutes",
    "Glute Bridge": "Glutes",
    "Glute Hypers": "Glutes/Hamstrings",
    "Glute Kickback": "Glutes",
    "Glute Machine": "Glutes",
    "Goblet Squat": "Quads, Glutes",
    "Hack Squat": "Quads, Glutes",
    "Hip Abduction": "Glutes",
    "Hip Abduction Machine": "Glute Medius/Abductors",
    "Hip Abductor": "Glutes",
    "Hip Thrust": "Glutes",
    "Isolation Ladders": "Arms",
    "Kettlebell Step Ups": "Glutes, Quads",
    "Kettlebell Step-Ups": "Glutes, Quads",
    "Lat Pulldown": "Back, Arms",
    "Laying Leg Curl": "Hamstrings",
    "Leg Abduction Machine": "Glute Medius",
    "Leg Extension": "Quads",
    "Leg Extensions": "Quads",
    "Leg Press": "Quads, Glutes",
    "Leg Press (Glute-bias)": "Quads, Glutes",
    "Leg extension": "Quads",
    "Lunges": "Quads, Glutes",
    "Lunges (30 lb)": "Quads, Glutes",
    "Lying Leg Curl": "Hamstrings",
    "MTS Ab Crunch": "Core",
    "Machine Abduction": "Glutes",
    "Machine Crunch": "Core",
    "Machine Kickback": "Glutes",
    "Machine Pec Fly": "Chest",
    "Machine Press": "Chest, Shoulders",
    "Machine Row": "Back, Arms",
    "Pec Fly Machine": "Chest",
    "Preacher Curl": "Biceps",
    "Pull Downs": "Back, Lats",
    "Pull Ups": "Back, Biceps",
    "Pull-Ups": "Back, Arms",
    "Pull-ups": "Back, Arms",
    "Pulldown": "Back, Lats",
    "Push Ups": "Chest, Triceps",
    "Push-ups": "Chest, Shoulders, Arms",
    "RDL": "Hamstrings, Glutes",
    "RDL (Back-off)": "Hamstrings, Glutes",
    "RDL (Barbell)": "Hamstrings, Glutes",
    "RDL (Pump Work)": "Hamstrings, Glutes",
    "RDLs": "Hamstrings, Glutes",
    "Rear Lunge": "Glutes, Quads",
    "Rear Lunges": "Glutes, Quads",
    "Rear lunges": "Glutes, Quads",
    "Rope Tricep Push Down": "Triceps",
    "Row": "Back, Lats",
    "Seated Row": "Back, Arms",
    "Shoulder Press": "Shoulders, Arms",
    "Single Leg Glute Bridge": "Glutes",
    "Skull Crushers": "Triceps",
    "Split Squat": "Quads/Glutes",
    "Squat": "Quads, Glutes",
    "Sumo Squats": "Glutes/Adductors",
    "Superset: DB Bicep Curl": "Biceps",
    "Superset: DB Deficit RDL": "Hamstrings, Glutes",
    "Superset: DB Shoulder Press": "Shoulders/Triceps",
    "Superset: DB Side Lateral": "Shoulders (Lateral Delt)",
    "Superset: DB Sumo Squat": "Glutes, Adductors",
    "Torso Rotation": "Core",
    "Treadmill": "Full Body",
    "Tricep Cable Pushdown": "Triceps",
    "Tricep Press": "Triceps",
    "Tricep Pushdown": "Triceps",
    "Tricep Pushdowns": "Arms",
    "Upper Body Push": "Chest, Shoulders, Arms",
    "Walking Lunge": "Quads, Glutes",
    "Walking Lunges": "Quads, Glutes",
    "Weighted Ab Crunch": "Abs",
    "Weighted Clam Shells": "Glute Medius/Abductors",
    "Weighted Crunch": "Core",
    "Weighted KB Step-Ups": "Glutes, Quads",
    "Weighted Step-Ups": "Glutes, Quads"
}

def load_mapping():
    """Loads the exercise mapping from JSONBin."""
    try:
        response = requests.get(BASE_URL + MAPPING_BIN_ID, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get("record", INITIAL_MAPPING)
        else:
            st.error(f"Failed to load mapping. Status: {response.status_code}")
            return INITIAL_MAPPING.copy()
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return INITIAL_MAPPING.copy()

def save_mapping(mapping_dict):
    """Overwrites the mapping bin with the newly learned exercises."""
    try:
        response = requests.put(BASE_URL + MAPPING_BIN_ID, headers=HEADERS, json=mapping_dict)
        if response.status_code != 200:
            st.error(f"Failed to save mapping. Status: {response.status_code}")
    except Exception as e:
        st.error(f"API Connection Error: {e}")

def load_data():
    """Loads the historical workout records from JSONBin."""
    try:
        response = requests.get(BASE_URL + WORKOUT_BIN_ID, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get("record", [])
        else:
            st.error(f"Failed to load workout data. Status: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return []

def save_data(new_records):
    """Pulls existing data, appends the new records, and pushes it back to JSONBin."""
    data = load_data()
    data.extend(new_records)
    
    try:
        response = requests.put(BASE_URL + WORKOUT_BIN_ID, headers=HEADERS, json=data)
        if response.status_code != 200:
            st.error(f"Failed to save workout data. Status: {response.status_code}")
    except Exception as e:
        st.error(f"API Connection Error: {e}")

def get_target_body_parts(exercise_name, current_mapping):
    ex_clean = exercise_name.strip().lower()
    
    # Exact match
    for known_ex, body_part in current_mapping.items():
        if known_ex.lower() == ex_clean:
            return body_part
            
    # Partial match
    for known_ex, body_part in current_mapping.items():
        if known_ex.lower() in ex_clean or ex_clean in known_ex.lower():
            return body_part

    return "❓ Needs Mapping"

def parse_workout_text(raw_text, current_mapping):
    records = []
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    # --- SCENARIO 1: Spreadsheet Paste ---
    if any('\t' in line for line in lines):
        for line in lines:
            cols = line.split('\t')
            if len(cols) >= 3:
                week_day = cols[0]
                week = week_day[:-1] if len(week_day) > 1 else week_day
                day = week_day[-1] if len(week_day) > 1 else "1"
                exercise = cols[1].strip() if len(cols) > 1 else ""
                
                records.append({
                    "Week": week,
                    "Day": day,
                    "Exercise": exercise,
                    "Sets & Reps": cols[2] if len(cols) > 2 else "",
                    "Tonnage (lbs)": cols[3] if len(cols) > 3 else "0",
                    "Target Body Parts": cols[4] if len(cols) > 4 else get_target_body_parts(exercise, current_mapping),
                    "Notes/Assumptions": cols[5] if len(cols) > 5 else ""
                })
        return records

    # --- SCENARIO 2: Smashed Text ---
    # We check if lines look like "11Walking Lunge" (digits + letter)
    # BUT we explicitly ignore lines like "45x10" to stop vertical logs from breaking!
    def is_smashed_line(line):
        starts_like_smashed = re.match(r'^\d{2,3}[A-Za-z]', line)
        is_weight_reps = re.match(r'^\d+(?:\.\d+)?\s*x\s*\d+$', line, re.IGNORECASE)
        return starts_like_smashed and not is_weight_reps

    if any(is_smashed_line(line) for line in lines):
        smashed_pattern = re.compile(
            r'^(\d{1,2})(\d)([A-Za-z\s\-\(\)]+?)((?:\d.*?)?)(\d+)((?:Quads|Glutes|Hamstrings|Chest|Shoulders|Arms|Back|Core|Abs)(?:,\s*[A-Za-z]+)*)(.*)$',
            re.IGNORECASE
        )
        for line in lines:
            match = smashed_pattern.search(line)
            if match:
                records.append({
                    "Week": match.group(1),
                    "Day": match.group(2),
                    "Exercise": match.group(3).strip(),
                    "Sets & Reps": match.group(4).strip(),
                    "Tonnage (lbs)": match.group(5),
                    "Target Body Parts": match.group(6).strip(),
                    "Notes/Assumptions": match.group(7).strip()
                })
            else:
                records.append({"Week": "", "Day": "", "Exercise": line, "Sets & Reps": "", "Tonnage (lbs)": "", "Target Body Parts": "❓ Needs Mapping", "Notes/Assumptions": "FAILED TO PARSE"})
        return records

    # --- SCENARIO 3: Vertical Notes ---
    week, day = "", ""
    current_exercise = None
    current_sets, current_notes = [], []
    current_tonnage = 0.0

    def save_current_exercise():
        if current_exercise:
            records.append({
                "Week": week,
                "Day": day,
                "Exercise": current_exercise,
                "Sets & Reps": ", ".join(current_sets),
                "Tonnage (lbs)": current_tonnage,
                "Target Body Parts": get_target_body_parts(current_exercise, current_mapping),
                "Notes/Assumptions": " ".join(current_notes)
            })

    for line in lines:
        week_day_match = re.search(r'Week\s+(\d+)\s+day\s+(\d+)', line, re.IGNORECASE)
        if week_day_match:
            week, day = week_day_match.group(1), week_day_match.group(2)
            continue

        set_match = re.match(r'^(\d+(?:\.\d+)?)\s*x\s*(\d+)$', line, re.IGNORECASE)
        if set_match:
            weight, reps = float(set_match.group(1)), int(set_match.group(2))
            current_sets.append(f"{weight:g}x{reps}")
            current_tonnage += (weight * reps)
        elif any(keyword in line.lower() for keyword in ["lbs", "sets", "reps", "each hand"]):
            current_notes.append(line)
        else:
            save_current_exercise() 
            current_exercise = line
            current_sets, current_notes = [], []
            current_tonnage = 0.0
            
    # Save the final exercise at the end of the list
    save_current_exercise()
    
    return records


# --- Streamlit UI ---
st.set_page_config(page_title="Workout Logger", layout="wide")
st.title("🏋️ Workout Data Parser (Cloud Connected)")

# Load our mapping dictionary from JSONBin
current_mapping = load_mapping()

st.markdown("Paste your workout notes below.")

raw_input = st.text_area("Raw Workout Data", height=200)

if st.button("Parse Data"):
    if raw_input:
        parsed_data = parse_workout_text(raw_input, current_mapping)
        if parsed_data:
            st.session_state['parsed_df'] = pd.DataFrame(parsed_data)
            st.success("Data parsed! Review and edit the table below before saving to the cloud.")
        else:
            st.warning("Could not parse any exercises. Check your formatting.")

if 'parsed_df' in st.session_state:
    st.markdown("### Review & Edit")
    st.info("💡 If you see '❓ Needs Mapping', type the correct body part. The app will save it to your JSONBin for next time!")
    
    edited_df = st.data_editor(st.session_state['parsed_df'], num_rows="dynamic", use_container_width=True)
    
    if st.button("Save to JSONBin"):
        with st.spinner("Saving to the cloud..."):
            final_records = edited_df.to_dict(orient="records")
            
            # 1. Update mapping in the cloud if needed
            mapping_updated = False
            for record in final_records:
                exercise = record["Exercise"].strip()
                body_part = str(record["Target Body Parts"]).strip()
                
                if body_part and body_part != "❓ Needs Mapping" and exercise not in current_mapping:
                    current_mapping[exercise] = body_part
                    mapping_updated = True
            
            if mapping_updated:
                save_mapping(current_mapping)
                st.toast("🧠 New exercise mapping saved to the cloud!")

            # 2. Save the workout data to the cloud
            save_data(final_records)
            st.success("Successfully saved to JSONBin!")
            del st.session_state['parsed_df']
            st.rerun()

st.divider()

# Display historical data from the cloud
st.markdown("### Historical Data (From JSONBin)")
with st.spinner("Loading history..."):
    history = load_data()
    if history:
        st.dataframe(pd.DataFrame(history), use_container_width=True)
    else:
        st.info("No data saved yet.")
