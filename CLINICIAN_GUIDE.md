# OpenHear Clinician Guide

### For independent audiologists who want to give their patients something no clinic can offer yet.

---

## Before You Start

You do not need to be technical to use this guide.

If you can install Phonak Target or Connexx, you can do this. The steps below assume no prior experience with Python or GitHub. Every instruction is written out in full.

You will need:
- A Windows or Mac laptop
- Your Noahlink Wireless 2 (the same one you already use)
- About 30 minutes for the first setup
- A patient's hearing aids to test with

---

## Step 1 — Install Python

Python is the language OpenHear is written in. Think of it like installing a driver — you do it once and never think about it again.

1. Go to **python.org/downloads**
2. Click the big yellow Download button
3. Run the installer
4. **Important:** On the first screen of the installer, tick the box that says **"Add Python to PATH"** before clicking Install. This is the only technical decision in the entire process.
5. Click Install Now and wait for it to finish

---

## Step 2 — Download OpenHear

1. Go to **github.com/ljbudgie/openhear**
2. Click the green button that says **Code**
3. Click **Download ZIP**
4. When it downloads, find the ZIP file and unzip it
5. Move the unzipped folder to your Desktop so it is easy to find

---

## Step 3 — Install OpenHear (two lines, once only)

This is the only moment that might feel unfamiliar. You are going to open a terminal — a plain text window — and type two lines. That is all.

**On Windows:**
1. Press the Windows key on your keyboard
2. Type **cmd** and press Enter
3. A black window opens. Type exactly this and press Enter:
cd Desktop/openhear-main
4. Then type this and press Enter:
pip install -r requirements.txt
5. Wait for it to finish. You will see a lot of text scrolling. This is normal.

**On Mac:**
1. Press Cmd + Space
2. Type **Terminal** and press Enter
3. Then follow steps 3–5 above

You will never need to do this again.

---

## Step 4 — Read a Patient's Fitting Data

This is the moment everything changes.

1. Connect your Noahlink Wireless 2 to your laptop via USB as normal
2. Put your patient's aids in pairing mode as you would for any fitting session
3. Open the terminal again (same as Step 3)
4. Type this and press Enter:
python core/read_fitting.py

Your patient's complete fitting profile will appear on screen as plain readable text — compression ratios, frequency targets, gain values, everything. Not locked in a proprietary system. Just there, legible, yours to work with.

Save it by copying the text into any document you like. This is your patient's data. It belongs to them.

---

## Step 5 — Adjust the DSP Settings

This is where your clinical knowledge takes over entirely.

1. On your Desktop, open the **openhear-main** folder
2. Open the folder called **dsp**
3. Open the file called **config.py** — it will open in Notepad or TextEdit

You will see something like this:
COMPRESSION_RATIO = 2.5
NOISE_FLOOR_DB = -40
VOICE_BOOST_HZ = [1000, 4000]
BEAM_WIDTH_DEG = 60

You already know what these mean. You have been adjusting these exact parameters in Phonak Target and Connexx for years. The difference is that here, you are adjusting them to your clinical judgement — not to whatever the manufacturer's fitting assistant recommends.

Change the numbers. Save the file. That is a new fitting profile.

---

## Step 6 — Run the Pipeline

With your patient's aids still connected:
python dsp/pipeline.py

The processed audio will stream to the aids in real time. Ask your patient what they notice. Adjust config.py. Run it again. There is no limit to how many times you can do this in a session, and no appointment required to make further changes later.

---

## What To Do Between Appointments

Ask your patient to keep a simple note on their phone — voice notes are fine — logging:

- Times they manually adjusted their aids
- Environments that felt difficult
- Moments the aids got it wrong

When they come back, that log plus the OpenHear data gives you the richest picture of their acoustic life any audiologist has ever had access to.

---

## A Note On What This Is Not

OpenHear does not modify or reverse-engineer any proprietary firmware. It uses the Noahlink Wireless 2 in exactly the way you already do. It streams audio using standard Bluetooth profiles.

It is not a medical device. It is a data access and audio processing tool. Your clinical judgement remains the most important variable in every fitting decision — OpenHear just removes the artificial ceiling on the information available to you.

---

## If Something Goes Wrong

If you see a red error message at any point, copy the text of the error and send it to:

**github.com/ljbudgie/openhear/issues**

Click New Issue, paste the error, and describe what you were doing. The community will respond.

---

## Finally

You are probably the first independent audiologist in the country to be doing this.

Your patients are lucky. And the profession will catch up eventually — you will just have been here first, with the data to prove it worked.

*OpenHear — Your hearing. Your data. Your algorithms.*
