import streamlit as st
import pandas as pd
import json
import re
import os

DATA_FILE = "workout_data.json"
MAPPING_FILE = "body_parts_mapping.json"

# A small starter dictionary based on your CSV. The app will add to this over time!
INITIAL_MAPPING = {
    "Walking Lunge": "Glutes/Quads",
    "Hack Squat": "Quads/Glutes",
    "Glute Machine": "Glutes",
    "Leg Extension": "Quads",
    "Hip Abduction": "Glutes",
    "DB RDL (Deficit)": "Hamstrings, Glutes",
    "Rear Lunge": "Glutes/Quads",
    "Push-ups": "Chest, Shoulders, Arms",
    "Pull-ups": "Back, Arms",
    "Ab Wheel": "Core",
    "DB Superset (15lb)": "Arms, Shoulders",
    "Bench Press": "Chest, Shoulders, Arms",
    "Machine Row": "Back, Arms",
    "Deadlift (Demo)": "Glutes, Hamstrings, Back",
    "Arm Pyramid": "Arms"
}

def load_mapping():
    """Loads the exercise-to-body-part mapping, or creates it if it doesn't exist."""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return INITIAL_MAPPING.copy()
    else:
        # Create it for the first time
        with open(MAPPING_FILE, "w") as f:
            json.dump(INITIAL_MAPPING, f, indent=4)
        return INITIAL_MAPPING.copy()

def save_mapping(mapping_dict):
    """Saves the updated mapping dictionary to the JSON file."""
    with open(MAPPING_FILE, "w") as f:
        json.dump(mapping_dict, f, indent=4)

def get_target_body_parts(exercise_name, current_mapping):
    """Finds the body part, or flags it if it's unknown."""
    ex_clean = exercise_name.strip().lower()
    
    # Check for exact matches (case-insensitive)
    for known_ex, body_part in current_mapping.items():
        if known_ex.lower() == ex_clean:
            return body_part
            
    # Check for partial matches (e.g., 'RDL' in 'DB RDL')
    for known_ex, body_part in current_mapping.items():
        if known_ex.lower() in ex_clean or ex_clean in known_ex.lower():
            return body_part

    # If we get here, we don't know it. Prompt the user in the UI.
    return "❓ Needs Mapping"

def parse_workout_text(raw_text, current_mapping):
    records = []
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    # --- SCENARIO 1: Spreadsheet Paste (contains tabs) ---
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
    if any(re.match(r'^\d{2,3}[A-Za-z]', line) for line in lines):
        smashed_pattern = re.compile(
            r'^(\d{1,2})(\d)([A-Za-z\s\-\(\)]+?)((?:\d.*?)?)(\d+)((?:Quads|Glutes|Hamstrings|Chest|Shoulders|Arms|Back|Core)(?:,\s*[A-Za-z]+)*)(.*)$'
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
            
    save_current_exercise()
    return records

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(new_records):
    data = load_data()
    data.extend(new_records)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Streamlit UI ---
st.set_page_config(page_title="Workout Logger", layout="wide")
st.title("🏋️ Workout Data Parser")

# Load our mapping dictionary into memory
current_mapping = load_mapping()

st.markdown("Paste your workout notes below. The app handles **vertical logs**, **spreadsheet pastes**, or **smashed strings**.")

raw_input = st.text_area("Raw Workout Data", height=250)

if st.button("Parse Data"):
    if raw_input:
        parsed_data = parse_workout_text(raw_input, current_mapping)
        if parsed_data:
            st.session_state['parsed_df'] = pd.DataFrame(parsed_data)
            st.success("Data parsed! Review and edit the table below before saving.")
        else:
            st.warning("Could not parse any exercises. Check your formatting.")

if 'parsed_df' in st.session_state:
    st.markdown("### Review & Edit")
    st.info("💡 If you see '❓ Needs Mapping' in the Target Body Parts column, simply type the correct body part into the cell. The app will remember it for next time!")
    
    edited_df = st.data_editor(st.session_state['parsed_df'], num_rows="dynamic", use_container_width=True)
    
    if st.button("Save to JSON"):
        final_records = edited_df.to_dict(orient="records")
        
        # 1. Update our mapping file with any new body parts the user typed in
        mapping_updated = False
        for record in final_records:
            exercise = record["Exercise"].strip()
            body_part = record["Target Body Parts"].strip()
            
            # If it's a valid body part and not already in our dictionary, add it!
            if body_part and body_part != "❓ Needs Mapping" and exercise not in current_mapping:
                current_mapping[exercise] = body_part
                mapping_updated = True
        
        if mapping_updated:
            save_mapping(current_mapping)
            st.toast("🧠 App learned new exercise mappings!")

        # 2. Save the actual workout data
        save_data(final_records)
        st.success(f"Successfully saved {len(final_records)} exercises to {DATA_FILE}!")
        del st.session_state['parsed_df']
        st.rerun()

st.divider()
st.markdown("### Historical Data")
history = load_data()
if history:
    st.dataframe(pd.DataFrame(history), use_container_width=True)
else:
    st.info("No data saved yet.")
