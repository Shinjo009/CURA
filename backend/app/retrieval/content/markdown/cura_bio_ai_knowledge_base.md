# CURA Knowledge Base — Understanding Bio-AI and Risk Scores

**Document ID:** `cura.kb.bio_ai.explainer`  
**Version:** 1.0  
**Updated:** 2026-11-18  
**Audience:** CURA end users and the CURA answer-generation system  
**Purpose:** Explain Bio-AI and interpret the user's own Bio-AI report in everyday language.  
**Scope:** SuperShyft Bio-AI / MetSights metabolic health reports. This document explains the supplied report format; it is not an independent validation of the underlying model.

---

## 1. The short answer: What is Bio-AI?

**Bio-AI is a health risk assessment system that looks at your blood test results and information about your lifestyle to estimate which health conditions may need more attention.**

Your blood tests show measurements such as blood sugar, cholesterol and liver-related markers. Your lifestyle questionnaire adds context about habits such as food, movement, sleep and stress. Bio-AI looks at these pieces of information together to identify patterns associated with health risks.

Think of it as an **early health warning system**: it helps highlight possible problems worth checking or preventing, even if you feel fine. **It cannot confirm that you have a disease or predict with certainty what will happen to you.**

### One-sentence explanation

> Bio-AI uses your blood results and lifestyle information to highlight possible health risks, so you can understand what deserves attention and what steps may help.

### What Bio-AI is not

- It is **not** a diagnosis.
- It is **not** a replacement for a doctor, physical examination or diagnostic tests.
- It does **not** mean that a high-risk condition is definitely present or will definitely develop.
- A score out of 100 is **not automatically a percentage probability** of disease.
- A low score does **not** guarantee that you have no disease.

---

## 2. What information goes into Bio-AI?

### 2.1 Blood test results

Blood tests measure substances and cells in your body. These measurements are often called **blood biomarkers**. Examples include:

| Blood marker or group | In simple words | Why it may be relevant |
|---|---|---|
| Fasting glucose | Sugar in your blood after fasting | Blood sugar regulation |
| HbA1c | An estimate of average blood sugar over roughly 2–3 months | Diabetes-related assessment |
| LDL, HDL, total cholesterol, triglycerides | Different types of fats in your blood | Cholesterol and heart-related health |
| ALT, AST and other liver markers | Blood measurements related to liver function or injury | Liver assessment; they do not alone diagnose fatty liver |
| Creatinine and eGFR | Measures related to kidney function | Kidney health context |
| TSH and thyroid hormones | Measures related to thyroid activity | Thyroid assessment |
| hs-CRP | A marker that can rise with inflammation | Additional health context; nonspecific |

**Important:** These are illustrative biomarkers seen in the supplied blood/Bio-AI material, **not a verified feature list or weighting formula** for each disease score. CURA must not claim that a particular marker is used in a specific model unless that information is available from the actual report or approved engine documentation.

### 2.2 Lifestyle questionnaire

The supplied questionnaire includes questions about food choices and eating frequency (fruit, vegetables, sugary foods and drinks, salt, and other dietary habits). SuperShyft's supplied material also describes activity, sleep, stress, and medical history as relevant context.

A questionnaire is based on the information provided by the user. Incomplete or inaccurate answers may affect the usefulness of the assessment. **Do not assume a lifestyle variable was collected for this user unless it is actually present in their data.**

### 2.3 How the information is combined

In simple terms:

1. Your blood tests provide measured health information.
2. Your questionnaire adds context about daily habits and other reported factors.
3. The Bio-AI engine analyzes patterns across the available information.
4. It assigns a score and risk category for supported health conditions.
5. The report may also show a lifestyle contribution indicator, a comparison percentile, and suggested areas to improve.

**Technical boundary:** The supplied reports describe the categories of inputs and the outputs, but do not disclose a validated formula, feature weights, training population, calibration, prediction time horizon or model performance. CURA must not invent those details. Some individual disease pages mention “genetic factors,” but the provided material does not establish that a genetic test was collected or used for every person. Do not claim genetic testing was performed.

---

## 3. What is a Bio-AI risk score?

A **Bio-AI risk score** is a number from **0 to 100** used by the supplied MetSights report to describe how strongly a person's health data aligns with the engine's risk patterns for a particular condition.

**A higher number means the engine flags more concern for that condition.** A lower number means the engine flags less concern based on the information assessed. This is a model-generated indicator, not a direct laboratory measurement.

### 3.1 Score categories in the supplied report

| Score | Report label | CURA's simple explanation |
|---|---|---|
| **0–25** | **Healthy** | The engine found a lower level of concern for this condition based on the available data. This does not rule the condition out. |
| **26–50** | **Increased Risk** | Some patterns may need attention. Consider the findings alongside your actual measurements and habits. |
| **51–75** | **High Risk** | The engine flags this condition as an important area to review. Check relevant results and discuss follow-up with a clinician as appropriate. |
| **76–100** | **Very High Risk** | The engine flags a particularly strong concern. This warrants timely review of the actual findings and whether further evaluation is needed; it is not proof of disease. |

**These ranges come from the example MetSights report (risk assessment overview, page 7).** If production reports use different thresholds, labels or model versions, the current user's report and approved configuration take priority.

### 3.2 The most important distinction: Score ≠ probability

**If your score is 75/100, it does not necessarily mean you have a 75% chance of developing that disease.**

It means your report has assigned a **risk indicator score of 75 out of 100**, which falls in the **High Risk** category in the supplied scoring system.

Do not say:
- “You have a 75% chance of diabetes.”
- “Your heart is 75% damaged.”
- “You will develop this disease.”
- “You already have this condition.”

Instead say:
- “Your score is **75/100 (High Risk)**. This means Bio-AI has flagged patterns associated with this condition. It is a signal to review your health information, not a diagnosis or a 75% probability.”

### 3.3 Is 100/100 the same as definitely having a disease?

**No.** A score of 100/100 is the highest value on this engine's scale. It is not proof of disease, not a 100% probability, and not a measure of how much of an organ is damaged.

### 3.4 Does 0/100 mean there is no risk?

**No.** A low score only reflects the model's assessment using the information it had. Symptoms, family history, examination, imaging or other tests may still matter.

### 3.5 Can scores from different conditions be compared?

The report shows them on the same 0–100 scale, but **do not assume the difference between two scores represents a comparable difference in real-world disease probability or severity**. For example, fatty liver 80 and thyroid 40 do not establish that fatty liver is exactly twice as likely.

---

## 4. What is the difference between a risk score, percentile, and lifestyle contribution?

These are **three different report elements**. Never mix them up.

### 4.1 Risk score (for example, 70/100)

The engine's numerical risk indicator for a specific condition. It belongs to one of the report's score categories.

### 4.2 Health rank or percentile (for example, 82nd percentile)

A comparison with a reference group, described in the sample report as people of similar age and gender.

**Simple explanation:** “Your report places your result around the 82nd percentile compared with the group used for comparison.” If the report's percentile is explicitly a *risk* percentile, this generally indicates a higher modeled risk ranking than about 82 out of 100 people in that comparison group, subject to the provider's definition.

**Do not say:** “You have an 82% chance of disease.” The exact comparison population, statistical method and direction of ranking are not independently documented in the supplied materials. When those details are unavailable, explain the comparison cautiously.

### 4.3 Lifestyle contribution

The sample report shows a separate lifestyle contribution scale (Low, Moderate, Increased, High, Very High). This indicates how strongly lifestyle factors are flagged **within the engine's assessment**. It is not the disease risk score, a percentage, or proof that a habit caused the result.

**Simple explanation:** “Your report suggests that your daily habits may be contributing to this risk. We can look at the habits recorded in your questionnaire to see what changes may help.”

### 4.4 Overall metabolic risk score

The sample report also includes an overall metabolic risk score. Explain this as the report's **combined indicator of metabolic health concern**, rather than as the chance of getting one particular disease. Do not claim it is the arithmetic average of the individual scores: no formula was supplied.

### 4.5 Metabolic age

The sample report includes “metabolic age,” described as a comparison of metabolism with people of the same chronological age. Explain it as an **estimate produced by the model**, not the person's actual biological age, a medical diagnosis, or a proven measurement of how long they will live.

---

## 5. Which health conditions are covered?

The example MetSights report contains **nine condition-specific areas**. Availability can vary by report version, sex, and engine configuration. Only describe a risk as measured for a user when it appears in that user's report.

| Report area | What it means in everyday language | What a high score means — and does not mean |
|---|---|---|
| **Metabolic syndrome** | A group of problems that can occur together, such as high blood sugar, blood pressure, abdominal fat and unhealthy blood fat levels. | The engine flags a concerning metabolic pattern; it does not establish the clinical criteria for metabolic syndrome. |
| **Dyslipidemia** | Unhealthy levels of cholesterol or other fats in the blood. | The engine flags lipid-related concern; confirm actual cholesterol and triglyceride values before stating a lipid disorder is present. |
| **Cardiac health** | Health of the heart and blood vessels. | The engine flags heart-related concern; it does not diagnose blocked arteries, a heart attack, or future cardiac events. |
| **Oxidative stress** | A situation where processes that can damage cells may outweigh the body's protective systems. | This is a modeled indicator; it does not directly measure damage to every cell or diagnose a disease. |
| **Fatty liver / NAFLD** | Fat may build up in the liver. Modern clinical terminology may use MASLD when appropriate. | A high score is not confirmation of fatty liver; imaging and clinical assessment may be needed. |
| **Hypertension** | High blood pressure. | A high score does not establish that blood pressure is high; actual blood pressure measurements are needed. |
| **Obesity** | Excess body fat that may affect health. | A high score does not directly measure body fat or diagnose obesity. |
| **Thyroid health** | How well the thyroid gland, which helps regulate body processes, is functioning. | A high score is not a diagnosis of an underactive or overactive thyroid; assess actual thyroid results and symptoms. |
| **Type 2 diabetes** | A condition in which the body has difficulty keeping blood sugar at healthy levels. | A high score is not a diabetes diagnosis; diagnosis depends on appropriate blood glucose/HbA1c testing and clinical context. |

### Important interpretation rule

A **risk assessment** and a **diagnosis** answer different questions:

- **Risk assessment:** “Is there a pattern suggesting this condition deserves attention?”
- **Diagnosis:** “Does this person meet accepted criteria for having this condition?”

CURA should not turn the first into the second.

---

## 6. Why can my risk be high even when my blood tests are normal?

A blood test and a risk assessment look at health in different ways.

A blood test checks specific measurements at a particular time. Bio-AI may combine several measurements and available lifestyle information to look for broader patterns. A value can be within its lab's reference range while other measurements, habits or combinations of findings still raise concern in the model.

**Example:** Two people may have similar fasting blood sugar today but different activity levels, diets, or other test results. Their modeled risk scores might differ. This example illustrates how a multi-input model can work; it does **not** reveal the actual MetSights formula.

**CURA response:** “Your blood results may look normal individually, but Bio-AI looks at several pieces of information together. Let's review which findings are actually present in your report. A high score does not by itself mean you have the disease.”

---

## 7. Why can my blood tests be abnormal but my Bio-AI risk be low?

The score and a lab result are different outputs. A model can assign a low score even if an individual blood marker is abnormal. That **does not cancel or correct the abnormal lab result**.

Possible reasons include the model considering other inputs or assessing a different target than the lab test. **The exact reason cannot be established without model-specific explanation data.**

**CURA response:** “Your Bio-AI score is low for this condition, but your [marker] is [value and unit], which is [above/below] the reference range shown in your report. The score does not make that result unimportant. We should interpret the blood test separately.”

---

## 8. What can change my risk score?

Some health measurements and daily habits can change over time. Examples of changes worth discussing include regular movement, a balanced eating pattern, adequate sleep, smoking avoidance, weight management when appropriate, and management of blood pressure, blood sugar or cholesterol with a clinician.

**However:** Do not promise that any particular action will lower a Bio-AI score by a specified number, or that a lower score proves disease prevention. Scores may also change because of different inputs, questionnaires, test methods or model versions.

If the user asks “How can I improve my score?”, prioritize **actions that improve established health measures**, not gaming the score.

---

## 9. When should I see a doctor?

Consider medical review when the report flags high or very high risk, when blood markers are significantly abnormal, when there are relevant symptoms, or when there is a strong personal/family history. The urgency depends on the **actual symptoms and clinical findings**, not the score alone.

**Seek urgent medical attention** for severe or concerning symptoms such as chest pain, severe breathlessness, sudden weakness on one side, fainting with concerning symptoms, or confusion. Do not rely on a chatbot score in these situations.

A clinician can decide whether a repeat test, blood pressure measurement, imaging or other evaluation is appropriate.

---

---

## 11. CURA system instructions for retrieving and using this knowledge

Use these instructions alongside CURA's main system prompt; they do not override its privacy, medical-safety or data-access policies.

### 11.1 Retrieval and grounding

- Retrieve this document for queries about `Bio-AI`, `Bio AI`, `MetSights`, `MetFlux`, `risk score`, `disease risk`, `metabolic score`, `metabolic age`, `health rank`, `percentile`, and `lifestyle contribution`.
- For **general explanations**, this knowledge document is sufficient; **do not access a user's health database** merely because they ask “What is Bio-AI?”
- For **personalized explanations**, first retrieve the relevant user's actual Bio-AI assessment and, when needed and authorized, the related blood report and questionnaire.
- Treat the user's **current report's categories and terminology** as authoritative for that report; do not silently apply the example thresholds to a different version.
- If the current report lacks a score, say “I couldn't find a score for that condition in your available report.”
- Do not infer missing blood values, questionnaire answers, genetic data, or model explanations.

### 11.2 Explanation style

- Speak directly to the user in clear, warm, everyday English.
- Explain a medical term immediately when first used.
- Prefer short paragraphs and bullets over long technical explanations.
- **Bold** the score, category, measured biomarker values and units.
- Give the direct answer first, then explain the why and what next.
- Be reassuring without dismissing meaningful abnormalities or high scores.
- Avoid unnecessarily repeating disclaimers; include the essential distinction between risk and diagnosis naturally.
- When discussing a high score, do not automatically use alarming phrases like “immediate danger” or “serious disease.”

### 11.3 Never conflate the following

- `risk_score` versus `disease_probability`
- `risk_score` versus `percentile`
- `risk_score` versus `lifestyle_contribution`
- `overall_metabolic_risk` versus a disease-specific score
- `metabolic_age` versus chronological age or lifespan
- `model risk indicator` versus confirmed diagnosis
- `general medical risk factor` versus a verified feature driving this user's model score
- `normal laboratory reference range` versus zero health risk

### 11.4 Personalization checklist

Before giving a personalized explanation, check:

- Is this the right user and assessment date?
- Is the condition actually present in the report?
- Are the score and risk label copied exactly?
- Is the relevant biomarker available, with its unit, date and lab reference range?
- Are lifestyle details actually documented for this user?
- Does the report explicitly identify possible contributors, or am I explaining general associations?
- Am I making a diagnosis, unsupported causal claim or numerical probability claim?
- Have I given a useful next step without promising a score reduction?

### 11.5 Suggested follow-up questions (maximum four)

Select up to four **relevant, non-repetitive** questions based on the user's request and available data. Examples:

- “Why is my [condition] risk high?”
- “Which of my blood results should I look at?”
- “What can I do to improve my health?”
- “Why is my risk high if my blood tests are normal?”

Do not ask questions whose answers require missing data without first acknowledging that limitation.

---

## 12. Example conversation snippets

**User:** “My diabetes risk is 64/100. Does that mean I have diabetes?”

**CURA:** “No. **64/100 is a High Risk score** in this Bio-AI report. It means the engine found patterns linked to greater diabetes-related concern. It is **not a diabetes diagnosis** or a 64% chance of developing it. To understand your current blood sugar health, we should look at your **HbA1c and fasting glucose** results, if available.”

**User:** “My fatty liver score is 83. Is 83% of my liver fatty?”

**CURA:** “No. **83/100 is a Very High Risk score**, not a measurement of how much fat is in your liver. Bio-AI is flagging fatty liver as an area that deserves attention. A clinician can decide whether imaging or other evaluation is needed.”

**User:** “My cholesterol test is normal, so why is my cardiac risk high?”

**CURA:** “Cholesterol is only one part of heart health. The model may look at several blood and lifestyle factors together. I can check your available results and questionnaire answers, but I can't tell you exactly what caused the model's score unless that explanation is included in your report.”

**User:** “I got a score of 100. Am I definitely sick?”

**CURA:** “No. **100/100 is the highest risk indicator on this scale**, but it does not prove you have the condition. It means this is a priority to review alongside your actual tests and symptoms. Let's look at the relevant findings and whether medical follow-up is needed.”

---

