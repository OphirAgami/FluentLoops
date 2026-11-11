import random
from database import get_connection, initialize_database

# Pack size of 10 gives 3 clean packs per level for live demos (change to 100 for full dictionary)
PACK_SIZE = 8
SHUFFLE_SEED = 42

# 24 curated words per CEFR level (sorted alphabetically before our deterministic shuffle)
VOCAB_BY_LEVEL: dict[str, list[tuple[str, str, str]]] = {
    "A1": [
        ("afraid", "מפחד / חושש", "I am not afraid to ask questions in English."),
        ("agree", "להסכים", "I agree with your idea for the project."),
        ("arrive", "להגיע", "We usually arrive at the office at nine."),
        ("borrow", "לשאול (חפץ)", "Can I borrow your charger for ten minutes?"),
        ("busy", "עסוק", "Today is a very busy day at work."),
        ("choose", "לבחור", "Which course did you choose this semester?"),
        ("comfortable", "נוח", "This chair is very comfortable for studying."),
        ("decide", "להחליט", "We need to decide where to eat lunch."),
        ("early", "מוקדם", "I wake up early before my classes."),
        ("explain", "להסביר", "Can you explain this word again, please?"),
        ("forget", "לשכוח", "Do not forget to save your file."),
        ("helpful", "מועיל / עוזר", "The mentor gave me very helpful advice."),
        ("important", "חשוב", "Clear communication is important in every team."),
        ("improve", "לשפר", "I practice every day to improve my speaking."),
        ("invite", "להזמין", "Let's invite Dana to join our study group."),
        ("listen", "להקשיב", "I listen to short podcasts on the bus."),
        ("mistake", "טעות", "Making a mistake is a normal part of learning."),
        ("neighbor", "שכן", "My neighbor works as a software engineer."),
        ("polite", "מנומס", "It is polite to thank the interviewer."),
        ("prepare", "להכין / להתכונן", "I need two days to prepare for the test."),
        ("promise", "להבטיח", "I promise to send you the notes tonight."),
        ("quiet", "שקט", "I prefer a quiet room when I read code."),
        ("remember", "לזכור", "Do you remember the name of that café?"),
        ("share", "לשתף", "Let me share my screen with you."),
    ],
    "A2": [
        ("achieve", "להשיג", "Small daily habits help you achieve big goals."),
        ("advice", "עצה", "She gave me great advice before my interview."),
        ("allow", "לאפשר / להרשות", "This app does not allow empty passwords."),
        ("attend", "להשתתף / להיות נוכח", "I plan to attend the tech meetup tomorrow."),
        ("avoid", "להימנע מ-", "Good naming helps you avoid confusing bugs."),
        ("compare", "להשוות", "Let's compare the two solutions side by side."),
        ("confident", "בטוח בעצמו", "Speaking aloud makes me feel more confident."),
        ("connect", "לחבר / להתחבר", "The backend needs to connect to the database."),
        ("consider", "לשקול", "We should consider a simpler design first."),
        ("curious", "סקרן", "Good engineers stay curious about how things work."),
        ("depend", "להיות תלוי ב-", "The final score will depend on accuracy."),
        ("describe", "לתאר", "Can you describe a project you built recently?"),
        ("develop", "לפתח", "I want to develop strong backend skills."),
        ("effort", "מאמץ", "Consistent effort matters more than talent."),
        ("encourage", "לעודד", "Good feedback can encourage learners to keep going."),
        ("experience", "ניסיון / חוויה", "Building a real app gives you practical experience."),
        ("familiar", "מוכר", "Are you familiar with how cookies work?"),
        ("goal", "מטרה", "My main goal is to speak fluently in interviews."),
        ("manage", "לנהל / להצליח", "How do you manage your time during exams?"),
        ("notice", "להבחין / לשים לב", "Did you notice any error in the terminal?"),
        ("opportunity", "הזדמנות", "This internship is a wonderful opportunity for me."),
        ("patient", "סבלני", "You have to be patient when learning a new language."),
        ("schedule", "לוח זמנים", "My schedule is pretty flexible this week."),
        ("solve", "לפתור", "Let's break the problem down and solve it step by step."),
    ],
    "B1": [
        ("accurate", "מדויק", "The transcript was surprisingly accurate."),
        ("adapt", "להסתגל / להתאים", "The system can adapt to each learner's mistakes."),
        ("approach", "גישה", "I chose a simple approach that I fully understand."),
        ("assume", "להניח", "Never assume the input from the user is valid."),
        ("challenge", "אתגר", "Explaining technical ideas in English was my biggest challenge."),
        ("collaborate", "לשתף פעולה", "Engineers collaborate closely with product designers."),
        ("commit", "להתחייב", "I decided to commit one hour a day to speaking."),
        ("convince", "לשכנע", "Clear examples will convince the interviewer."),
        ("deadline", "מועד אחרון (דדליין)", "We finished the prototype two days before the deadline."),
        ("determine", "לקבוע", "Error frequency helps determine what to practice next."),
        ("efficient", "יעיל", "An index makes database lookups much more efficient."),
        ("emphasize", "להדגיש", "I want to emphasize what I learned from this bug."),
        ("evaluate", "להעריך", "We evaluate both vocabulary usage and grammar."),
        ("essential", "חיוני / הכרחי", "Testing edge cases is essential before deployment."),
        ("feature", "פיצ'ר / תכונה", "Voice recording was my favorite feature to build."),
        ("gradually", "בהדרגה", "My vocabulary expanded gradually over two months."),
        ("hesitate", "להסס", "Do not hesitate to ask for clarification."),
        ("impact", "השפעה", "Foundational mistakes have a big impact on fluency."),
        ("maintain", "לתחזק / לשמור על", "Clean code is much easier to maintain."),
        ("overcome", "להתגבר על", "Short daily sessions helped me overcome speaking anxiety."),
        ("priority", "עדיפות", "Fixing recurring grammar errors is our top priority."),
        ("reluctant", "מהסס / חסר רצון", "At first I was reluctant to speak English out loud."),
        ("relevant", "רלוונטי", "Focus on words that are relevant to your daily life."),
        ("struggle", "להתקשות / להיאבק", "Many students struggle with irregular past verbs."),
    ],
    "B2": [
        ("acknowledge", "להכיר ב- / להודות", "It is smart to acknowledge trade-offs in your design."),
        ("ambiguous", "דו-משמעי / עמום", "When requirements are ambiguous, I ask clarifying questions."),
        ("Bottleneck".lower(), "צוואר בקבוק", "Database queries can become a bottleneck without indexes."),
        ("coherent", "קוהרנטי / ברור ורציף", "Practice helps you give coherent answers under pressure."),
        ("comprehensive", "מקיף", "We wrote a comprehensive plan before coding."),
        ("constraint", "אילוץ / מגבלה", "Time was our main constraint during the two-week sprint."),
        ("crucial", "קריטי / מכריע", "Data validation is crucial for backend security."),
        ("deliberate", "מכוון / מודע", "Deliberate practice targets your weakest skills first."),
        ("distinguish", "להבחין / להבדיל", "Learners often struggle to distinguish similar words."),
        ("elaborate", "לפרט / להרחיב", "Could you elaborate on how your priority queue works?"),
        ("feasible", "בר-ביצוע / ישים", "We kept the architecture simple and feasible for one developer."),
        ("fundamental", "בסיסי / יסודי", "Graphs and heaps are fundamental computer science structures."),
        ("inevitable", "בלתי נמנע", "Bugs are inevitable, so good error messages matter."),
        ("insight", "תובנה", "User testing gave me a valuable insight into the flow."),
        ("justify", "להצדיק / לנמק", "Be ready to justify every architectural decision you made."),
        ("mitigate", "למתן / לצמצם סיכון", "Hashing session tokens helps mitigate database leaks."),
        ("obstacle", "מכשול", "Fear of making mistakes is the biggest obstacle to fluency."),
        ("persistent", "מתמיד / עיקש (וגם נשמר בקביעות)", "PostgreSQL keeps user progress persistent across sessions."),
        ("prerequisite", "תנאי קדם", "Past participle mastery is a prerequisite for present perfect."),
        ("resilient", "עמיד / חסין", "A resilient system handles unexpected errors gracefully."),
        ("retain", "לשמר / לזכור לאורך זמן", "Using a word in speech helps you retain it much longer."),
        ("severity", "חומרה", "We rank grammar mistakes by frequency and severity."),
        ("subtle", "עדין / דק", "There is a subtle difference between these two expressions."),
        ("trade-off", "פשרה הנדסית (טרייד-אוף)", "Every architecture involves a trade-off between speed and simplicity."),
    ],
    "C1": [
        ("articulate", "רהוט / לבטא בבהירות", "She was able to articulate complex ideas effortlessly."),
        ("candid", "כן / גלוי לב", "I appreciate candid feedback from my code reviewers."),
        ("cognitive", "קוגניטיבי / הכרתי", "Shuffling similar words reduces cognitive interference."),
        ("compelling", "משכנע / סוחף", "A live working demo makes a compelling impression."),
        ("consolidate", "לגבש / לחזק ולבסס", "Follow-up questions consolidate newly learned vocabulary."),
        ("deteriorate", "להידרדר / להיחלש", "Without practice, active speaking skills quickly deteriorate."),
        ("discrepancy", "פער / אי-התאמה", "We noticed a discrepancy between self-assessment and actual speech."),
        ("empirical", "אמפירי / מבוסס ניסוי", "We adjusted the scoring weights based on empirical testing."),
        ("foster", "לטפח / לעודד", "Short daily streaks foster consistent learning habits."),
        ("heuristic", "כלל אצבע חישובי (היוריסטיקה)", "Our priority queue uses a transparent scoring heuristic."),
        ("implication", "השלכה / משמעות נגזרת", "Every schema change has an implication for query speed."),
        ("inherent", "טבוע / מובנה מטבעו", "Ambiguity is inherent in natural human conversation."),
        ("intricate", "מורכב / מסועף", "Even simple rules can form an intricate dependency graph."),
        ("leverage", "למנף / לנצל בחוכמה", "We leverage browser speech recognition to avoid server lag."),
        ("meticulous", "קפדני / מדוקדק", "Security code requires meticulous attention to detail."),
        ("nuance", "ניואנס / דקות משמעות", "Advanced speakers pick up on subtle nuances in tone."),
        ("paradigm", "תפיסה / פרדיגמה", "Adaptive learning shifts away from the one-size-fits-all paradigm."),
        ("pragmatic", "פרגמטי / מעשי", "Choosing a monolith for an MVP is a pragmatic decision."),
        ("proficient", "מיומן / שולט היטב", "Consistent speaking practice makes you proficient faster."),
        ("redundant", "מיותר / כפול", "Composite primary keys prevent redundant rows in the graph."),
        ("rigorous", "קפדני / יסודי", "Rigorous input validation keeps the API predictable."),
        ("scrutinize", "לבחון בדקדקנות", "Interviewers often scrutinize projects listed on a resume."),
        ("Seamless".lower(), "חלק / ללא חיכוך", "We designed a seamless transition from swiping to speaking."),
        ("substantiate", "לבסס / לגבות בהוכחות", "Metrics in the dashboard substantiate the learner's progress."),
    ],
    "C2": [
        ("ubiquitous", "נפוץ בכל מקום", "REST APIs have become ubiquitous in modern web software."),
        ("ephemeral", "חולף / זמני", "Browser memory is ephemeral, whereas database storage is durable."),
        ("idempotent", "אידמפוטנטי (הרצה חוזרת נותנת אותה תוצאה)", "Our seed script is idempotent and safe to run multiple times."),
        ("quintessential", "המובהק ביותר / התמציתי", "Priority queues are the quintessential structure for scheduling."),
        ("juxtapose", "להעמיד זה לצד זה להשוואה", "The feedback card juxtaposes your sentence with the corrected form."),
        ("unequivocal", "חד-משמעי / מוחלט", "Passing an end-to-end test gives unequivocal proof it works."),
        ("convoluted", "מסובך / מפותל מדי", "We refactored a convoluted query into two readable steps."),
        ("fastidious", "קפדן מאוד בפרטים", "Fastidious error handling prevents cryptic crashes."),
        ("rudimentary", "בסיסי / ראשוני", "Even a rudimentary prototype can validate the core loop."),
        ("salient", "בולט / העיקרי ביותר", "Highlight the three most salient decisions in your README."),
        ("tenuous", "רופף / קלוש", "Memorizing word lists creates only a tenuous grasp of usage."),
        ("transient", "זמני / בר-חלוף", "Retry logic can recover from transient network glitches."),
        ("ubiquity", "נוכחות בכל מקום", "The ubiquity of English in tech makes speaking practice vital."),
        ("unprecedented", "חסר תקדים", "Modern speech tools offer unprecedented accessibility for learners."),
        ("viable", "בר-קיימא / מעשי", "A focused MVP is the fastest path to a viable product."),
        ("succinct", "תמציתי ומדויק", "Interviewers appreciate succinct explanations of your architecture."),
        ("pervasive", "רווח / מתפשט בכל חלק", "Async patterns are pervasive across modern web frameworks."),
        ("ostensibly", "לכאורה / על פניו", "Two words may look ostensibly similar yet carry distinct meanings."),
        ("methodical", "שיטתי / מסודר", "A methodical debugging process saves hours of guesswork."),
        ("lucid", "בהיר / צלול להבנה", "Draw a lucid diagram before writing complex SQL."),
        ("imperative", "הכרחי / צו השעה", "Protecting user credentials is imperative in any web app."),
        ("exemplify", "להדגים / להוות דוגמה ל-", "These ten rules exemplify how grammar skills build on one another."),
        ("detrimental", "מזיק / פוגע", "Cramming similar words together can be detrimental to recall."),
        ("ameliorate", "לשפר / להקל על בעיה", "Targeted follow-ups ameliorate recurring grammatical slips."),
    ],
}

# 10 interconnected grammar skills (Nodes in our Skill Graph)
# Tuple: (code, name, cefr_level, severity, meaning_he, example_sentence)
GRAMMAR_SKILLS: list[tuple[str, str, str, int, str, str]] = [
    (
        "grammar_be_present",
        "Verb 'to be' (am / is / are)",
        "A1",
        3,
        "התאמת am / is / are לגוף במשפט בהווה",
        "She is confident, and they are ready for the interview.",
    ),
    (
        "grammar_present_simple",
        "Present Simple & 3rd-Person -s",
        "A1",
        3,
        "הווה פשוט ותוספת s לפועל בגוף שלישי יחיד (he / she / it)",
        "He practices English every morning and writes clean code.",
    ),
    (
        "grammar_articles",
        "Articles (a / an / the)",
        "A2",
        2,
        "שימוש נכון ב-a לפני עיצור, an לפני תנועה, ו-the לדבר ספציפי",
        "It was an exciting opportunity to join the engineering team.",
    ),
    (
        "grammar_prepositions",
        "Prepositions (in / on / at / to)",
        "A2",
        2,
        "מילות יחס נכונות לזמן, מקום ופעלים נפוצים",
        "I arrived at the office on Monday morning.",
    ),
    (
        "grammar_past_simple",
        "Past Simple & Irregular Verbs",
        "A2",
        3,
        "עבר פשוט ופעלים יוצאי דופן (למשל went במקום goed)",
        "Yesterday I went over my notes and solved two bugs.",
    ),
    (
        "grammar_modals",
        "Modal Verbs (can / should / would)",
        "B1",
        2,
        "אחרי פועל עזר (can / should / would) הפועל תמיד בצורת הבסיס בלי to ובלי s",
        "You should focus on clarity when explaining your code.",
    ),
    (
        "grammar_past_participle",
        "Past Participle Forms (V3)",
        "B1",
        2,
        "הצורה השלישית של הפועל (gone, written, taken) כבסיס לזמנים מתקדמים",
        "I have taken several courses in algorithms.",
    ),
    (
        "grammar_present_perfect",
        "Present Perfect (have / has + V3)",
        "B1",
        3,
        "חיבור פעולה מהעבר להווה בעזרת have/has + צורה שלישית (V3)",
        "I have built a full-stack application with FastAPI.",
    ),
    (
        "grammar_passive_voice",
        "Passive Voice (be + V3)",
        "B2",
        2,
        "משפט סביל: שימוש בפועל be מותאם לזמן + צורה שלישית (V3)",
        "User progress is stored securely in PostgreSQL.",
    ),
    (
        "grammar_conditionals",
        "Conditionals (If + Past / would)",
        "B2",
        3,
        "משפטי תנאי היפותטיים: If + עבר פשוט בחלק הראשון, ו-would בחלק השני",
        "If I had more time, I would add automated voice scoring.",
    ),
]

# Directed edges (child_skill_code, prerequisite_skill_code)
# Meaning: to master child_skill, learner must first understand prerequisite_skill
GRAMMAR_PREREQUISITES: list[tuple[str, str]] = [
    ("grammar_present_simple", "grammar_be_present"),
    ("grammar_past_simple", "grammar_present_simple"),
    ("grammar_modals", "grammar_present_simple"),
    ("grammar_past_participle", "grammar_past_simple"),
    ("grammar_present_perfect", "grammar_past_participle"),
    ("grammar_passive_voice", "grammar_be_present"),
    ("grammar_passive_voice", "grammar_past_participle"),
    ("grammar_conditionals", "grammar_past_simple"),
    ("grammar_conditionals", "grammar_modals"),
]

# Speaking prompts tailored by goal and optional grammar target ({word} gets filled dynamically)
SPEAKING_PROMPTS: list[tuple[str, str, str | None, str]] = [
    # General / Daily goals
    ("A1", "daily", None, "Say one simple sentence about your day using the word '{word}'."),
    ("A2", "daily", None, "Tell me about something in your routine using the word '{word}'."),
    ("B1", "daily", None, "Share a short personal example from real life using '{word}'."),
    ("B2", "daily", None, "Explain your opinion on a daily habit while naturally using '{word}'."),
    ("C1", "daily", None, "Reflect on a personal experience in 1-2 sentences using '{word}'."),
    ("C2", "daily", None, "Formulate a nuanced observation about everyday life using '{word}'."),
    # Job Interview goals
    ("A1", "interviews", None, "Introduce something about your studies or work using '{word}'."),
    ("A2", "interviews", None, "Tell an interviewer one sentence about yourself using '{word}'."),
    ("B1", "interviews", None, "Answer an interviewer: how does '{word}' relate to working on a project?"),
    ("B2", "interviews", None, "In a job interview, explain a technical decision you made using '{word}'."),
    ("C1", "interviews", None, "Pitch a strength or engineering lesson to an interviewer using '{word}'."),
    ("C2", "interviews", None, "Articulate an architectural trade-off in an interview using '{word}'."),
    # Academic / Studies goals
    ("A1", "academic", None, "Say one short sentence about studying or classes using '{word}'."),
    ("A2", "academic", None, "Describe a course or homework task using the word '{word}'."),
    ("B1", "academic", None, "Explain how '{word}' connects to learning computer science."),
    ("B2", "academic", None, "Summarize an idea from university or research using '{word}'."),
    ("C1", "academic", None, "Present an analytical point as if in a seminar using '{word}'."),
    ("C2", "academic", None, "Synthesize a formal academic argument in one sentence using '{word}'."),
    # Targeted Grammar Follow-up Prompts (used by Adaptive Priority Queue!)
    ("A1", "general", "grammar_be_present", "Use '{word}' in a present-tense sentence with am, is, or are."),
    ("A1", "general", "grammar_present_simple", "Describe what a teammate or friend regularly does, using '{word}' (watch the -s ending!)."),
    ("A2", "general", "grammar_articles", "Say a sentence with '{word}' and pay close attention to a, an, and the."),
    ("A2", "general", "grammar_prepositions", "Describe when or where something happened using '{word}' (check in / on / at)."),
    ("A2", "general", "grammar_past_simple", "Tell me about something that happened last week using '{word}' in the Past Simple."),
    ("B1", "general", "grammar_modals", "Give a piece of advice using 'should' or 'can' together with '{word}'."),
    ("B1", "general", "grammar_past_participle", "Use have/has with a correct V3 verb form in a sentence that includes '{word}'."),
    ("B1", "general", "grammar_present_perfect", "Share something you have done recently (have/has + V3) while using '{word}'."),
    ("B2", "general", "grammar_passive_voice", "Describe how something is built or handled (Passive Voice) using '{word}'."),
    ("B2", "general", "grammar_conditionals", "Start with 'If I...' to describe a hypothetical situation using '{word}'."),
]


def seed_all() -> None:
    initialize_database()

    with get_connection() as conn:
        # 1. Insert vocabulary words (deterministically shuffled per level to prevent lexical interference)
        vocab_count = 0
        for level, words in VOCAB_BY_LEVEL.items():
            sorted_words = sorted(words, key=lambda item: item[0])
            rng = random.Random(f"{SHUFFLE_SEED}_{level}")
            rng.shuffle(sorted_words)

            for index, (word, meaning_he, example) in enumerate(sorted_words):
                pack_number = (index // PACK_SIZE) + 1
                code = f"vocab_{level.lower()}_{word.replace('-', '_')}"
                conn.execute(
                    """
                    INSERT INTO skills (code, name, skill_type, cefr_level, pack_number, meaning_he, example_sentence, severity)
                    VALUES (%s, %s, 'vocab', %s, %s, %s, %s, 1)
                        ON CONFLICT (code) DO UPDATE SET
                        pack_number = EXCLUDED.pack_number,
                                                  meaning_he = EXCLUDED.meaning_he,
                                                  example_sentence = EXCLUDED.example_sentence
                    """,
                    (code, word, level, pack_number, meaning_he, example),
                )
                vocab_count += 1

        # 2. Insert grammar nodes
        for code, name, level, severity, meaning_he, example in GRAMMAR_SKILLS:
            conn.execute(
                """
                INSERT INTO skills (code, name, skill_type, cefr_level, pack_number, meaning_he, example_sentence, severity)
                VALUES (%s, %s, 'grammar', %s, NULL, %s, %s, %s)
                    ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                                              cefr_level = EXCLUDED.cefr_level,
                                              meaning_he = EXCLUDED.meaning_he,
                                              example_sentence = EXCLUDED.example_sentence,
                                              severity = EXCLUDED.severity
                """,
                (code, name, level, meaning_he, example, severity),
            )

        # 3. Insert Skill Graph edges (prerequisite relationships)
        for child_code, prereq_code in GRAMMAR_PREREQUISITES:
            conn.execute(
                """
                INSERT INTO skill_prerequisites (skill_id, prerequisite_skill_id)
                SELECT child.id, prereq.id
                FROM skills AS child, skills AS prereq
                WHERE child.code = %s AND prereq.code = %s
                    ON CONFLICT DO NOTHING
                """,
                (child_code, prereq_code),
            )

        # 4. Refresh speaking prompt templates cleanly
        conn.execute("DELETE FROM practice_prompts")
        for level, goal, grammar_code, template in SPEAKING_PROMPTS:
            conn.execute(
                """
                INSERT INTO practice_prompts (cefr_level, learning_goal, grammar_skill_code, prompt_template)
                VALUES (%s, %s, %s, %s)
                """,
                (level, goal, grammar_code, template),
            )

    print(
        f"Seed complete: {vocab_count} vocab words across A1-C2, "
        f"{len(GRAMMAR_SKILLS)} grammar skills, "
        f"{len(GRAMMAR_PREREQUISITES)} graph edges, "
        f"and {len(SPEAKING_PROMPTS)} speaking prompts!"
    )


if __name__ == "__main__":
    seed_all()