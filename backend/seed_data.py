import random
from database import get_connection, initialize_database

# 8 words per pack gives 3 equal packs in every CEFR level (change to 100 for a full dictionary)
PACK_SIZE = 8
SHUFFLE_SEED = 42

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
        ("bottleneck", "צוואר בקבוק", "Database queries can become a bottleneck without indexes."),
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
        ("persistent", "מתמיד / נשמר בקביעות", "PostgreSQL keeps user progress persistent across sessions."),
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
        ("seamless", "חלק / ללא חיכוך", "We designed a seamless transition from swiping to speaking."),
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

# 10 standalone grammar rules (name, cefr_level, severity, explanation_he, example, standalone followup_prompt)
GRAMMAR_RULES: list[tuple[str, str, int, str, str, str]] = [
    (
        "Verb 'to be' (am / is / are)",
        "A1",
        3,
        "התאמת am / is / are לגוף במשפט בהווה",
        "She is confident, and they are ready for the interview.",
        "Describe how you and a friend feel today using am, is, or are.",
    ),
    (
        "Present Simple & 3rd-Person -s",
        "A1",
        3,
        "הווה פשוט ותוספת s לפועל בגוף שלישי יחיד (he / she / it)",
        "He practices English every morning and writes clean code.",
        "Describe one daily habit of a friend or family member (remember he/she + verb-s).",
    ),
    (
        "Articles (a / an / the)",
        "A2",
        2,
        "שימוש נכון ב-a לפני עיצור, an לפני תנועה, ו-the לדבר ספציפי",
        "It was an exciting opportunity to join the engineering team.",
        "Describe an object on your desk right now using a, an, and the.",
    ),
    (
        "Prepositions (in / on / at / to)",
        "A2",
        2,
        "מילות יחס נכונות לזמן, מקום ופעלים נפוצים",
        "I arrived at the office on Monday morning.",
        "Say one sentence about when and where you usually study (use in, on, or at).",
    ),
    (
        "Past Simple & Irregular Verbs",
        "A2",
        3,
        "עבר פשוט ופעלים יוצאי דופן (למשל went במקום goed)",
        "Yesterday I went over my notes and solved two bugs.",
        "Tell me one thing you did yesterday using the Past Simple.",
    ),
    (
        "Modal Verbs (can / should / would)",
        "B1",
        2,
        "אחרי פועל עזר (can / should / would) הפועל תמיד בצורת הבסיס בלי to ובלי s",
        "You should focus on clarity when explaining your code.",
        "Give one short tip to a new student using 'should' or 'can'.",
    ),
    (
        "Past Participle Forms (V3)",
        "B1",
        2,
        "הצורה השלישית של הפועל (gone, written, taken) כבסיס לזמנים מתקדמים",
        "I have taken several courses in algorithms.",
        "Mention a movie you have seen or a book you have read recently (have + V3).",
    ),
    (
        "Present Perfect (have / has + V3)",
        "B1",
        3,
        "חיבור פעולה מהעבר להווה בעזרת have/has + צורה שלישית (V3)",
        "I have built a full-stack application with FastAPI.",
        "Share one skill or project you have worked on this year (use have/has + V3).",
    ),
    (
        "Passive Voice (be + V3)",
        "B2",
        2,
        "משפט סביל: שימוש בפועל be מותאם לזמן + צורה שלישית (V3)",
        "User progress is stored securely in PostgreSQL.",
        "Explain in one sentence how data or messages are handled in an app (use Passive Voice).",
    ),
    (
        "Conditionals (If + Past / would)",
        "B2",
        3,
        "משפטי תנאי היפותטיים: If + עבר פשוט בחלק הראשון, ו-would בחלק השני",
        "If I had more time, I would add automated voice scoring.",
        "Answer in one sentence: If you had a free week with no obligations, what would you do?",
    ),
]

# Directed edges in our Grammar Skill Graph: (advanced_rule_name, prerequisite_rule_name)
GRAMMAR_PREREQUISITES: list[tuple[str, str]] = [
    ("Present Simple & 3rd-Person -s", "Verb 'to be' (am / is / are)"),
    ("Past Simple & Irregular Verbs", "Present Simple & 3rd-Person -s"),
    ("Modal Verbs (can / should / would)", "Present Simple & 3rd-Person -s"),
    ("Past Participle Forms (V3)", "Past Simple & Irregular Verbs"),
    ("Present Perfect (have / has + V3)", "Past Participle Forms (V3)"),
    ("Passive Voice (be + V3)", "Verb 'to be' (am / is / are)"),
    ("Passive Voice (be + V3)", "Past Participle Forms (V3)"),
    ("Conditionals (If + Past / would)", "Past Simple & Irregular Verbs"),
    ("Conditionals (If + Past / would)", "Modal Verbs (can / should / would)"),
]


def seed_all() -> None:
    with get_connection() as conn:
        # Clean up yesterday's old hybrid tables if they still exist on disk
        conn.execute(
            "DROP TABLE IF EXISTS practice_prompts, user_skills, skill_prerequisites, skills CASCADE"
        )
        conn.execute("ALTER TABLE IF EXISTS user_grammar_stats DROP COLUMN IF EXISTS last_word_id")

    initialize_database()

    with get_connection() as conn:
        # 1. Seed shuffled vocabulary packs per CEFR level
        for level, words in VOCAB_BY_LEVEL.items():
            sorted_words = sorted(words, key=lambda item: item[0])
            rng = random.Random(f"{SHUFFLE_SEED}_{level}")
            rng.shuffle(sorted_words)

            for index, (word, meaning_he, example) in enumerate(sorted_words):
                pack_number = (index // PACK_SIZE) + 1
                conn.execute(
                    """
                    INSERT INTO words (word, cefr_level, pack_number, meaning_he, example_sentence)
                    VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (cefr_level, word) DO UPDATE SET
                        pack_number = EXCLUDED.pack_number,
                        meaning_he = EXCLUDED.meaning_he,
                        example_sentence = EXCLUDED.example_sentence
                    """,
                    (word, level, pack_number, meaning_he, example),
                )

        # 2. Seed standalone grammar rules
        for name, level, severity, explanation_he, example, followup_prompt in GRAMMAR_RULES:
            conn.execute(
                """
                INSERT INTO grammar_rules (name, cefr_level, severity, explanation_he, example_sentence, followup_prompt)
                VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                    cefr_level = EXCLUDED.cefr_level,
                    severity = EXCLUDED.severity,
                    explanation_he = EXCLUDED.explanation_he,
                    example_sentence = EXCLUDED.example_sentence,
                    followup_prompt = EXCLUDED.followup_prompt
                """,
                (name, level, severity, explanation_he, example, followup_prompt),
            )

        # 3. Seed grammar prerequisite edges (DAG)
        for rule_name, prereq_name in GRAMMAR_PREREQUISITES:
            conn.execute(
                """
                INSERT INTO grammar_prerequisites (rule_id, prerequisite_rule_id)
                SELECT r.id, p.id
                FROM grammar_rules AS r, grammar_rules AS p
                WHERE r.name = %s AND p.name = %s
                    ON CONFLICT DO NOTHING
                """,
                (rule_name, prereq_name),
            )

    print(
        f"Clean schema seeded: 144 words across A1-C2 ({PACK_SIZE} per pack), "
        f"{len(GRAMMAR_RULES)} grammar rules, and {len(GRAMMAR_PREREQUISITES)} graph edges!"
    )


if __name__ == "__main__":
    seed_all()