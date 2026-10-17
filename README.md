# CareLens — AI Healthcare Assistant

CareLens is a Streamlit app for health education and symptom tracking. It combines a small, rule-based symptom guide with tools for recording observations and exploring session history. It does not use a trained AI model.

## Features

- Dark-themed interface with a transparent Streamlit header that blends into the app background.
- Select symptoms or describe them in plain language to match entries in the built-in guide.
- View possible explanations, relevant specialties, general guidance, and safe at-home observations.
- Record symptom duration and self-rated severity.
- Explore session statistics, charts, a timeline, and recent checks.
- Ask the local FAQ-style CareLens helper about app features and safe observations.
- Download an individual symptom summary or session history as a PDF.
- Filter the demo doctor directory, optionally load a doctor CSV, or open external directory searches.

## Run locally

You need Python and pip installed.

1. Clone the repository and open its folder:

   ```powershell
   git clone https://github.com/pranshupandey140-collab/Ai-health-assistance.git
   cd Ai-health-assistance
   ```

2. (Optional) Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Install the required packages:

   ```powershell
   python -m pip install streamlit pandas plotly matplotlib reportlab
   ```

4. Start the app:

   ```powershell
   python -m streamlit run app.py
   ```

Streamlit will print a local URL to open in your browser.

The dashboard's symptom word cloud is optional. To enable it, install `wordcloud`:

```powershell
python -m pip install wordcloud
```

## Optional doctor directory data

The doctor finder displays clearly marked demo placeholders unless a local `data/doctors.csv` file is available. Replace the demo data only with a legitimate, current dataset. The CSV must include these columns:

```text
Doctor Name,State,District,Specialty
```

An optional `Verified` column is also supported. Verify clinicians' credentials and availability independently; CareLens does not verify the listings.

## Privacy and medical safety

- CareLens is an educational demo, not a medical device or a substitute for a qualified healthcare professional.
- The symptom guide is limited and rule-based. Its possible explanations are examples, not diagnoses, predictions, or treatment recommendations.
- Do not use the app to rule out an emergency or delay care. For sudden or severe symptoms, contact local emergency services; in India, call **112**.
- The chat is a local FAQ-style helper, not a clinician or an external AI service.
- Symptom history and chat are held in the current Streamlit session and may disappear when that session resets. Do not enter sensitive personal or medical identifiers.
