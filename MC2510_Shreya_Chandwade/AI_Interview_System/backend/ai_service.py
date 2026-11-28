import os
import re
import random
from dotenv import load_dotenv

try:
    from backend.api_config import get_openai_client
except ModuleNotFoundError:
    from api_config import get_openai_client

load_dotenv()


def _call_openai(feature: str, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str | None:
    """Call OpenAI for a feature. Returns None if the API is unavailable."""

    client = get_openai_client(feature)
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        content = response.choices[0].message.content
        return content.strip() if content else None
    except Exception as exc:
        print(f"Notice: OpenAI API call failed for {feature}:", exc)
        return None


# =========================================================
# LOCAL INTERVIEW QUESTION BANK
# =========================================================

QUESTION_BANK = {

    "java": [
        "What is Java and what are its main features?",
        "Explain the four main principles of Object-Oriented Programming in Java.",
        "What is the difference between JDK, JRE, and JVM?",
        "What is the difference between method overloading and method overriding?",
        "What is the difference between == and equals() in Java?",
        "What is inheritance in Java? Give an example.",
        "What is an interface in Java?",
        "What is exception handling in Java?",
        "What is the difference between ArrayList and LinkedList?",
        "What is the difference between String, StringBuilder, and StringBuffer?"
    ],

    "python": [
        "What are the main features of Python?",
        "What is the difference between a list and a tuple in Python?",
        "What are dictionaries in Python?",
        "What is the difference between == and is in Python?",
        "What are functions in Python?",
        "Explain inheritance in Python.",
        "What is exception handling in Python?",
        "What are Python modules and packages?",
        "What is a list comprehension?",
        "What is the difference between shallow copy and deep copy?"
    ],

    "sql": [
        "What is SQL and why is it used?",
        "What is a primary key?",
        "What is a foreign key?",
        "What is the difference between DELETE, DROP, and TRUNCATE?",
        "What is a JOIN? Explain different types of JOINs.",
        "What is normalization?",
        "What is the difference between WHERE and HAVING?",
        "What is GROUP BY used for?",
        "What is the difference between INNER JOIN and LEFT JOIN?",
        "What is a subquery?"
    ],

    "data structures": [
        "What is a data structure?",
        "What is the difference between an array and a linked list?",
        "What is a stack and where is it used?",
        "What is a queue and where is it used?",
        "What is a binary tree?",
        "What is a binary search tree?",
        "What is the difference between BFS and DFS?",
        "What is the time complexity of searching in a binary search tree?",
        "What is a hash table?",
        "What is the difference between linear search and binary search?"
    ],

    "dsa": [
        "What is the difference between an array and a linked list?",
        "Explain stack and queue with real-world examples.",
        "What is the time complexity of binary search?",
        "What is recursion?",
        "What is sorting? Explain any two sorting algorithms.",
        "What is a binary search tree?",
        "Explain BFS and DFS.",
        "What is Big-O notation?",
        "How would you find the largest element in an array?",
        "How would you detect a cycle in a linked list?"
    ],

    "machine learning": [
        "What is Machine Learning?",
        "What is the difference between supervised and unsupervised learning?",
        "What is overfitting?",
        "What is underfitting?",
        "What is the difference between classification and regression?",
        "What is a training dataset?",
        "What is a confusion matrix?",
        "What is cross-validation?",
        "What is feature engineering?",
        "What is the difference between accuracy, precision, and recall?"
    ],

    "artificial intelligence": [
        "What is Artificial Intelligence?",
        "What is the difference between AI, Machine Learning, and Deep Learning?",
        "What is Natural Language Processing?",
        "What is Generative AI?",
        "What is an AI model?",
        "What is training data?",
        "What is the difference between supervised and unsupervised learning?",
        "What are some real-world applications of AI?",
        "What is overfitting in Machine Learning?",
        "What are the limitations of Artificial Intelligence?"
    ],

    "html": [
        "What is HTML?",
        "What is the difference between HTML and HTML5?",
        "What are semantic HTML elements?",
        "What is the purpose of forms in HTML?",
        "What is the difference between div and span?"
    ],

    "css": [
        "What is CSS?",
        "What is the CSS box model?",
        "What is the difference between Flexbox and Grid?",
        "What is responsive web design?",
        "What is the difference between class and ID selectors?"
    ]
}


# =========================================================
# GENERAL TECHNICAL QUESTIONS
# =========================================================

GENERAL_TECHNICAL = [
    "Explain an important technical project you have worked on.",
    "What is your approach when solving a difficult programming problem?",
    "How do you debug a program when it produces an unexpected result?",
    "How do you learn a new programming language or technology?",
    "How do you improve the performance of a program?",
    "What is the difference between a compiler and an interpreter?",
    "What is version control and why is Git useful?",
    "How do you handle errors and exceptions in a software application?"
]


# =========================================================
# PROBLEM SOLVING QUESTIONS
# =========================================================

PROBLEM_SOLVING = [
    "You are given an array of numbers. How would you find the largest element efficiently?",
    "A program is running very slowly. What steps would you take to identify and solve the problem?",
    "You are given a string. How would you determine whether it is a palindrome?",
    "How would you find duplicate elements in an array?",
    "If your application suddenly starts producing incorrect results, how would you debug it?",
    "How would you design a solution to count the frequency of each element in an array?"
]


# =========================================================
# HR / BEHAVIORAL QUESTIONS
# =========================================================

HR_QUESTIONS = [
    "Tell me about yourself.",
    "Why are you interested in this job role?",
    "What are your strengths and weaknesses?",
    "Why should we hire you?",
    "Where do you see yourself in the next five years?",
    "Tell me about a challenging project you worked on and how you solved the problem.",
    "How do you handle pressure or deadlines?",
    "How do you work as part of a team?"
]


# =========================================================
# EXPECTED ANSWER KNOWLEDGE
# =========================================================

ANSWER_KNOWLEDGE = {

    # -----------------------------------------------------
    # JAVA
    # -----------------------------------------------------

    "What is Java and what are its main features?": {
        "keywords": [
            ["object", "oriented"],
            ["platform", "independent"],
            ["portable"],
            ["secure"],
            ["robust"],
            ["multithreading"]
        ],
        "answer": (
            "Java is a high-level, object-oriented programming language. "
            "It is platform independent because Java code is compiled into "
            "bytecode that runs on the JVM. Java is known for portability, "
            "security, robustness, automatic memory management, and "
            "multithreading."
        )
    },

    "Explain the four main principles of Object-Oriented Programming in Java.": {
        "keywords": [
            ["encapsulation"],
            ["inheritance"],
            ["polymorphism"],
            ["abstraction"]
        ],
        "answer": (
            "The four main principles of OOP are encapsulation, inheritance, "
            "polymorphism, and abstraction. Encapsulation combines data and "
            "methods and controls access. Inheritance allows a class to "
            "acquire properties and methods from another class. Polymorphism "
            "allows the same interface or method to behave differently. "
            "Abstraction hides implementation details and exposes essential functionality."
        )
    },

    "What is the difference between JDK, JRE, and JVM?": {
        "keywords": [
            ["jdk"],
            ["jre"],
            ["jvm"],
            ["development"],
            ["runtime"],
            ["bytecode"]
        ],
        "answer": (
            "JVM is the Java Virtual Machine that executes Java bytecode. "
            "JRE contains the JVM and libraries required to run Java applications. "
            "JDK contains the JRE plus development tools such as the Java compiler "
            "and debugging tools. Therefore, JDK is used for development, while "
            "JRE is mainly used to run Java applications."
        )
    },

    "What is the difference between method overloading and method overriding?": {
        "keywords": [
            ["overloading"],
            ["overriding"],
            ["same", "method"],
            ["parameters"],
            ["inheritance"],
            ["compile"],
            ["runtime"]
        ],
        "answer": (
            "Method overloading means defining multiple methods with the same "
            "name but different parameter lists in the same class. It is "
            "compile-time polymorphism. Method overriding occurs when a subclass "
            "provides a new implementation of a method inherited from a parent "
            "class. It is runtime polymorphism."
        )
    },

    "What is the difference between == and equals() in Java?": {
        "keywords": [
            ["=="],
            ["equals"],
            ["reference"],
            ["value"],
            ["content"],
            ["object"]
        ],
        "answer": (
            "In Java, == compares primitive values directly and compares object "
            "references when used with objects. The equals() method is generally "
            "used to compare the logical content or value of objects when the "
            "class overrides it."
        )
    },

    "What is inheritance in Java? Give an example.": {
        "keywords": [
            ["inheritance"],
            ["parent"],
            ["child"],
            ["class"],
            ["extends"],
            ["reuse"]
        ],
        "answer": (
            "Inheritance is an OOP mechanism in which a child class acquires "
            "properties and methods of a parent class. In Java, inheritance "
            "between classes is commonly implemented using the extends keyword. "
            "For example, Dog extends Animal allows Dog to inherit accessible "
            "members of Animal."
        )
    },

    "What is an interface in Java?": {
        "keywords": [
            ["interface"],
            ["contract"],
            ["abstract"],
            ["implements"],
            ["class"],
            ["methods"]
        ],
        "answer": (
            "An interface in Java defines a contract that implementing classes "
            "must follow. A class implements an interface using the implements "
            "keyword. Interfaces are commonly used to achieve abstraction and "
            "support multiple inheritance of type."
        )
    },

    "What is exception handling in Java?": {
        "keywords": [
            ["exception"],
            ["try"],
            ["catch"],
            ["finally"],
            ["throw"],
            ["throws"],
            ["error"]
        ],
        "answer": (
            "Exception handling in Java is used to handle abnormal conditions "
            "without abruptly terminating a program. Java provides try, catch, "
            "finally, throw, and throws. Code that may cause an exception can "
            "be placed in try and handled in catch."
        )
    },

    "What is the difference between ArrayList and LinkedList?": {
        "keywords": [
            ["arraylist"],
            ["linkedlist"],
            ["array"],
            ["random", "access"],
            ["insert"],
            ["delete"],
            ["nodes"]
        ],
        "answer": (
            "ArrayList is backed by a dynamic array and provides fast random "
            "access using an index. LinkedList is based on linked nodes and "
            "can be more suitable for frequent insertion and deletion at "
            "known positions. ArrayList is generally preferred for frequent "
            "access operations."
        )
    },

    "What is the difference between String, StringBuilder, and StringBuffer?": {
        "keywords": [
            ["string"],
            ["immutable"],
            ["stringbuilder"],
            ["stringbuffer"],
            ["mutable"],
            ["thread"]
        ],
        "answer": (
            "String objects are immutable, so modifying a String creates another "
            "object. StringBuilder is mutable and is generally faster for repeated "
            "string modifications in single-threaded code. StringBuffer is also "
            "mutable but its methods are synchronized, making it safer for certain "
            "multi-threaded situations with additional synchronization overhead."
        )
    },


    # -----------------------------------------------------
    # PYTHON
    # -----------------------------------------------------

    "What are the main features of Python?": {
        "keywords": [
            ["high-level"],
            ["interpreted"],
            ["object-oriented"],
            ["dynamic"],
            ["readable"],
            ["libraries"]
        ],
        "answer": (
            "Python is a high-level, dynamically typed programming language. "
            "It has simple readable syntax, supports object-oriented and "
            "functional programming, and provides a large standard library "
            "and ecosystem of third-party packages."
        )
    },

    "What is the difference between a list and a tuple in Python?": {
        "keywords": [
            ["list"],
            ["tuple"],
            ["mutable"],
            ["immutable"],
            ["square"],
            ["parentheses"]
        ],
        "answer": (
            "A list is an ordered and mutable collection, usually written with "
            "square brackets. A tuple is ordered but immutable and is usually "
            "written with parentheses. Lists are suitable when data needs to "
            "change, while tuples are useful for fixed collections."
        )
    },

    "What are dictionaries in Python?": {
        "keywords": [
            ["dictionary"],
            ["key"],
            ["value"],
            ["key-value"],
            ["mutable"]
        ],
        "answer": (
            "A Python dictionary stores data as key-value pairs. Keys are used "
            "to access corresponding values. Dictionaries are mutable and are "
            "commonly used when data needs to be accessed by a meaningful key."
        )
    },

    "What is the difference between == and is in Python?": {
        "keywords": [
            ["=="],
            ["is"],
            ["value"],
            ["identity"],
            ["object"]
        ],
        "answer": (
            "In Python, == checks whether two objects have equal values, while "
            "is checks whether two references point to the same object in memory."
        )
    },

    "What are functions in Python?": {
        "keywords": [
            ["function"],
            ["def"],
            ["parameter"],
            ["return"],
            ["reusable"]
        ],
        "answer": (
            "A function is a reusable block of code that performs a specific task. "
            "Python functions are commonly defined using def, can accept parameters, "
            "and can return a value using return."
        )
    },

    "Explain inheritance in Python.": {
        "keywords": [
            ["inheritance"],
            ["parent"],
            ["child"],
            ["class"],
            ["reuse"]
        ],
        "answer": (
            "Inheritance in Python allows a child class to acquire attributes "
            "and methods from a parent class. It promotes code reuse and can be "
            "implemented by passing the parent class when defining the child class."
        )
    },

    "What is exception handling in Python?": {
        "keywords": [
            ["exception"],
            ["try"],
            ["except"],
            ["finally"],
            ["error"]
        ],
        "answer": (
            "Exception handling in Python is used to handle runtime errors "
            "without abruptly terminating the program. The try block contains "
            "code that may fail, except handles the exception, and finally can "
            "be used for cleanup code."
        )
    },

    "What are Python modules and packages?": {
        "keywords": [
            ["module"],
            ["package"],
            ["import"],
            ["code"],
            ["organize"]
        ],
        "answer": (
            "A module is a Python file containing code such as functions, "
            "classes, or variables. A package is a collection of related "
            "modules organized together. They help organize and reuse code."
        )
    },

    "What is a list comprehension?": {
        "keywords": [
            ["list"],
            ["comprehension"],
            ["expression"],
            ["loop"],
            ["condition"]
        ],
        "answer": (
            "List comprehension is a concise Python syntax for creating a list "
            "from an iterable, optionally applying an expression and condition. "
            "For example, [x * 2 for x in numbers] creates a new list containing "
            "each number multiplied by two."
        )
    },

    "What is the difference between shallow copy and deep copy?": {
        "keywords": [
            ["shallow"],
            ["deep"],
            ["copy"],
            ["nested"],
            ["reference"]
        ],
        "answer": (
            "A shallow copy creates a new outer object but references nested "
            "objects from the original. A deep copy recursively creates copies "
            "of nested objects as well, so changes to nested data do not affect "
            "the original structure."
        )
    },


    # -----------------------------------------------------
    # SQL
    # -----------------------------------------------------

    "What is SQL and why is it used?": {
        "keywords": [
            ["sql"],
            ["database"],
            ["query"],
            ["data"],
            ["relational"]
        ],
        "answer": (
            "SQL stands for Structured Query Language. It is used to create, "
            "read, update, and delete data in relational databases. SQL can "
            "also be used to define database structures and retrieve data "
            "using queries."
        )
    },

    "What is a primary key?": {
        "keywords": [
            ["primary"],
            ["key"],
            ["unique"],
            ["identify"],
            ["row"],
            ["null"]
        ],
        "answer": (
            "A primary key is a column or combination of columns that uniquely "
            "identifies each row in a table. Its values must be unique and "
            "cannot normally be NULL."
        )
    },

    "What is a foreign key?": {
        "keywords": [
            ["foreign"],
            ["key"],
            ["table"],
            ["reference"],
            ["primary"],
            ["relationship"]
        ],
        "answer": (
            "A foreign key is a column or set of columns that references a key "
            "in another table, commonly its primary key. It helps establish "
            "relationships between tables and maintain referential integrity."
        )
    },

    "What is the difference between DELETE, DROP, and TRUNCATE?": {
        "keywords": [
            ["delete"],
            ["drop"],
            ["truncate"],
            ["rows"],
            ["table"],
            ["structure"]
        ],
        "answer": (
            "DELETE removes selected rows from a table and can use a WHERE "
            "condition. TRUNCATE removes all rows while keeping the table "
            "structure. DROP removes the table itself, including its structure."
        )
    },

    "What is a JOIN? Explain different types of JOINs.": {
        "keywords": [
            ["join"],
            ["inner"],
            ["left"],
            ["right"],
            ["full"],
            ["table"]
        ],
        "answer": (
            "A JOIN combines rows from two or more tables using a related column. "
            "INNER JOIN returns matching rows. LEFT JOIN returns all rows from "
            "the left table and matching rows from the right. RIGHT JOIN does "
            "the opposite. FULL JOIN returns matching and non-matching rows "
            "from both tables where supported."
        )
    },

    "What is normalization?": {
        "keywords": [
            ["normalization"],
            ["redundancy"],
            ["duplicate"],
            ["database"],
            ["tables"],
            ["integrity"]
        ],
        "answer": (
            "Normalization is the process of organizing database tables to "
            "reduce data redundancy and improve data integrity. It commonly "
            "involves dividing data into related tables and establishing "
            "relationships between them."
        )
    },

    "What is the difference between WHERE and HAVING?": {
        "keywords": [
            ["where"],
            ["having"],
            ["filter"],
            ["rows"],
            ["group"],
            ["aggregate"]
        ],
        "answer": (
            "WHERE filters individual rows before grouping, while HAVING filters "
            "groups after GROUP BY. HAVING is commonly used with aggregate "
            "functions such as COUNT, SUM, and AVG."
        )
    },

    "What is GROUP BY used for?": {
        "keywords": [
            ["group"],
            ["by"],
            ["aggregate"],
            ["count"],
            ["sum"],
            ["average"]
        ],
        "answer": (
            "GROUP BY groups rows that have the same values in specified columns. "
            "It is commonly used with aggregate functions such as COUNT, SUM, "
            "AVG, MIN, and MAX to calculate results for each group."
        )
    },

    "What is the difference between INNER JOIN and LEFT JOIN?": {
        "keywords": [
            ["inner"],
            ["left"],
            ["join"],
            ["matching"],
            ["rows"],
            ["table"]
        ],
        "answer": (
            "INNER JOIN returns only rows that have matching values in both "
            "tables. LEFT JOIN returns every row from the left table and the "
            "matching rows from the right table. If no match exists, right-side "
            "columns are NULL."
        )
    },

    "What is a subquery?": {
        "keywords": [
            ["subquery"],
            ["query"],
            ["query"],
            ["nested"],
            ["select"]
        ],
        "answer": (
            "A subquery is a query nested inside another SQL query. It can be "
            "used in SELECT, WHERE, FROM, or other clauses to provide intermediate "
            "results to the outer query."
        )
    }
}


# =========================================================
# QUESTION-SPECIFIC WRONG CONCEPTS
# =========================================================

WRONG_CONCEPTS = {

    "What is inheritance in Java? Give an example.": [
        ["private", "hiding"],
        ["data", "hiding"],
        ["encapsulation", "only"]
    ],

    "What is the difference between == and equals() in Java?": [
        ["equals", "assigns"],
        ["==", "inheritance"]
    ],

    "What is exception handling in Java?": [
        ["inheritance", "reus"],
        ["encapsulation", "data", "hiding"]
    ],

    "What is a primary key?": [
        ["foreign", "key", "only"],
        ["duplicate", "allowed"]
    ],

    "What is a foreign key?": [
        ["unique", "identify", "row", "only"],
        ["primary", "key", "only"]
    ],

    "What is the difference between a list and a tuple in Python?": [
        ["tuple", "mutable", "list", "immutable"]
    ],

    "What is the difference between == and is in Python?": [
        ["is", "value", "only"],
        ["==", "identity", "only"]
    ]
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def find_skill_questions(db, skills: str, job_role: str = ""):

    search_text = f"{skills} {job_role}".lower()

    selected_questions = []

    if db is not None:
        try:
            try:
                from backend.models import QuestionItem
            except ModuleNotFoundError:
                from models import QuestionItem
            
            all_questions = db.query(QuestionItem).all()
            for q in all_questions:
                if q.category.lower() in search_text:
                    selected_questions.append(q.question_text)
        except Exception as exc:
            print("Notice: Error loading questions from DB:", exc)

    if not selected_questions:
        # Fallback to local in-memory QUESTION_BANK
        for skill, questions in QUESTION_BANK.items():
            if skill in search_text:
                selected_questions.extend(questions)

    return selected_questions


# =========================================================
# GENERATE INTERVIEW QUESTIONS
# =========================================================

def generate_interview_questions(
    db = None,
    job_role: str = "",
    skills: str = "",
    experience: str = ""
):

    ai_questions = _generate_questions_with_ai(job_role, skills, experience)
    if ai_questions:
        return ai_questions

    try:
        try:
            from backend.models import QuestionItem
        except ModuleNotFoundError:
            from models import QuestionItem
    except Exception:
        QuestionItem = None

    skill_questions = find_skill_questions(db, skills, job_role)

    skill_questions = list(dict.fromkeys(skill_questions))

    random.shuffle(skill_questions)

    technical_questions = skill_questions[:3]

    if len(technical_questions) < 3:

        remaining = 3 - len(technical_questions)

        general_qs = []
        if db is not None and QuestionItem is not None:
            try:
                general_qs = [
                    q.question_text
                    for q in db.query(QuestionItem)
                    .filter(QuestionItem.category == "general")
                    .all()
                ]
            except Exception:
                pass

        if not general_qs:
            general_qs = GENERAL_TECHNICAL

        available_general = [q for q in general_qs if q not in technical_questions]
        random.shuffle(available_general)

        technical_questions.extend(
            available_general[:remaining]
        )

    problem_qs = []
    if db is not None and QuestionItem is not None:
        try:
            problem_qs = [
                q.question_text
                for q in db.query(QuestionItem)
                .filter(QuestionItem.category == "problem_solving")
                .all()
            ]
        except Exception:
            pass

    if not problem_qs:
        problem_qs = PROBLEM_SOLVING

    problem_question = random.choice(problem_qs)

    hr_qs = []
    if db is not None and QuestionItem is not None:
        try:
            hr_qs = [
                q.question_text
                for q in db.query(QuestionItem)
                .filter(QuestionItem.category == "hr")
                .all()
            ]
        except Exception:
            pass

    if not hr_qs:
        hr_qs = HR_QUESTIONS

    hr_question = random.choice(hr_qs)

    questions = (
        technical_questions[:3]
        + [problem_question]
        + [hr_question]
    )

    result = []

    for index, question in enumerate(questions, start=1):

        result.append(
            f"{index}. {question}"
        )

    return "\n".join(result)



def _generate_questions_with_ai(
    job_role: str = "",
    skills: str = "",
    experience: str = ""
) -> str | None:

    prompt = f"""
Generate exactly 5 interview questions for this candidate.

Job Role: {job_role}
Skills: {skills}
Experience: {experience}

Include:
- 3 technical questions based on the skills
- 1 problem-solving question
- 1 HR/behavioral question

Format each question on a new line like:
1. Question text here
2. Question text here

Do not include answers.
"""

    result = _call_openai(
        "question_generation",
        "You are an expert technical interviewer.",
        prompt,
        temperature=0.8,
    )

    if not result:
        return None

    lines = [
        line.strip()
        for line in result.split("\n")
        if line.strip()
    ]

    if len(lines) < 3:
        return None

    return "\n".join(lines[:5])


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text):

    text = text.lower()

    text = text.replace("==", " equal ")
    text = text.replace("()", " ")

    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# CHECK KEYWORD GROUP
# =========================================================

def keyword_group_found(answer, group):

    answer = normalize_text(answer)

    # For groups such as ["object", "oriented"],
    # all words must appear.
    return all(
        word.lower() in answer
        for word in group
    )


# =========================================================
# EVALUATE TECHNICAL ANSWER
# =========================================================

def evaluate_technical_answer(db, question, answer):

    knowledge = None
    keyword_groups = []
    wrong_patterns = []
    ideal_answer = ""

    if db is not None:
        try:
            try:
                from backend.models import AnswerKnowledge
            except ModuleNotFoundError:
                from models import AnswerKnowledge

            record = db.query(AnswerKnowledge).filter(AnswerKnowledge.question_text == question.strip()).first()
            if record:
                import json
                keyword_groups = json.loads(record.keywords_json)
                wrong_patterns = json.loads(record.wrong_concepts_json) if record.wrong_concepts_json else []
                ideal_answer = record.ideal_answer
                knowledge = {
                    "keywords": keyword_groups,
                    "answer": ideal_answer
                }
        except Exception as exc:
            print("Notice: Error loading AnswerKnowledge from DB:", exc)

    if not knowledge:
        # Fallback to local globals
        knowledge = ANSWER_KNOWLEDGE.get(question)
        if not knowledge:
            return None
        keyword_groups = knowledge["keywords"]
        wrong_patterns = WRONG_CONCEPTS.get(question, [])
        ideal_answer = knowledge["answer"]

    found_groups = []

    for group in keyword_groups:

        if keyword_group_found(answer, group):
            found_groups.append(group)

    total_groups = len(keyword_groups)

    matched = len(found_groups)

    coverage = matched / total_groups if total_groups else 0

    # -----------------------------------------------------
    # Detect obviously wrong concepts
    # -----------------------------------------------------

    wrong_matches = []

    for pattern in wrong_patterns:

        if keyword_group_found(answer, pattern):
            wrong_matches.append(" ".join(pattern))

    # -----------------------------------------------------
    # Score correctness
    # -----------------------------------------------------

    if coverage >= 0.80:
        correctness = 9
    elif coverage >= 0.60:
        correctness = 8
    elif coverage >= 0.45:
        correctness = 7
    elif coverage >= 0.30:
        correctness = 5
    elif coverage > 0:
        correctness = 3
    else:
        correctness = 1

    # Wrong concepts should strongly reduce correctness.
    if wrong_matches:
        correctness = min(correctness, 3)

    # -----------------------------------------------------
    # Relevance
    # -----------------------------------------------------

    answer_words = set(
        re.findall(
            r"[a-zA-Z]{3,}",
            answer.lower()
        )
    )

    question_words = set(
        re.findall(
            r"[a-zA-Z]{3,}",
            question.lower()
        )
    )

    common = answer_words.intersection(question_words)

    if not common:
        relevance = 1
    elif len(common) >= 4:
        relevance = 9
    elif len(common) >= 2:
        relevance = 7
    else:
        relevance = 5

    # A technically matching answer is relevant.
    if coverage >= 0.45:
        relevance = max(relevance, 8)

    # -----------------------------------------------------
    # Clarity
    # -----------------------------------------------------

    word_count = len(answer.split())

    if word_count >= 50:
        clarity = 9
    elif word_count >= 30:
        clarity = 8
    elif word_count >= 15:
        clarity = 7
    elif word_count >= 8:
        clarity = 5
    else:
        clarity = 3

    # -----------------------------------------------------
    # Overall score
    # -----------------------------------------------------

    score = round(
        (
            correctness * 0.60
            + relevance * 0.25
            + clarity * 0.15
        )
    )

    score = max(0, min(10, score))

    # -----------------------------------------------------
    # Strengths
    # -----------------------------------------------------

    strengths = []

    if matched > 0:
        strengths.append(
            f"The answer correctly covers {matched} "
            f"of the {total_groups} important concepts."
        )

    if relevance >= 7:
        strengths.append(
            "The answer is relevant to the question."
        )

    if clarity >= 7:
        strengths.append(
            "The answer is reasonably clear and understandable."
        )

    if not strengths:
        strengths.append(
            "The candidate attempted to answer the question."
        )

    # -----------------------------------------------------
    # Weaknesses
    # -----------------------------------------------------

    weaknesses = []

    missing = []

    for group in keyword_groups:

        if not keyword_group_found(answer, group):

            missing.append(
                " / ".join(group)
            )

    if missing:

        weaknesses.append(
            "Important concepts missing: "
            + ", ".join(missing[:4])
            + "."
        )

    if wrong_matches:

        weaknesses.append(
            "The answer contains an incorrect concept: "
            + ", ".join(wrong_matches)
            + "."
        )

    if word_count < 15:

        weaknesses.append(
            "The answer is too short to fully explain the concept."
        )

    if not weaknesses:

        weaknesses.append(
            "The answer could be strengthened with a practical example."
        )

    # -----------------------------------------------------
    # Result label
    # -----------------------------------------------------

    if score >= 9:
        result = "Excellent"
    elif score >= 8:
        result = "Very Good"
    elif score >= 6:
        result = "Mostly Correct"
    elif score >= 4:
        result = "Partially Correct"
    else:
        result = "Incorrect"

    # -----------------------------------------------------
    # Return result
    # -----------------------------------------------------

    return f"""
Score: {score}/10

Result: {result}

Correctness: {correctness}/10
Relevance: {relevance}/10
Clarity: {clarity}/10

Strengths:

- {strengths[0]}
- {strengths[1] if len(strengths) > 1 else "The candidate made an attempt to explain the concept."}

Weaknesses:

- {weaknesses[0]}
- {weaknesses[1] if len(weaknesses) > 1 else "The answer could include more supporting detail."}

Improvement Suggestions:

- Explain the important concepts mentioned in the question.
- Include a simple example where appropriate.
- Use technical terms accurately.

Ideal Answer:

{ideal_answer}
""".strip()



# =========================================================
# GENERAL ANSWER EVALUATION
# =========================================================

def evaluate_general_answer(question, answer):

    word_count = len(answer.split())

    question_words = set(
        re.findall(
            r"[a-zA-Z]{4,}",
            question.lower()
        )
    )

    answer_words = set(
        re.findall(
            r"[a-zA-Z]{4,}",
            answer.lower()
        )
    )

    common_words = question_words.intersection(answer_words)

    # -----------------------------------------------------
    # Relevance
    # -----------------------------------------------------

    if len(common_words) >= 4:
        relevance = 9
    elif len(common_words) >= 2:
        relevance = 7
    elif len(common_words) >= 1:
        relevance = 5
    else:
        relevance = 2

    # -----------------------------------------------------
    # Clarity
    # -----------------------------------------------------

    if word_count >= 50:
        clarity = 9
    elif word_count >= 30:
        clarity = 8
    elif word_count >= 15:
        clarity = 7
    elif word_count >= 8:
        clarity = 5
    else:
        clarity = 3

    # -----------------------------------------------------
    # Correctness
    # -----------------------------------------------------

    if relevance >= 8 and word_count >= 30:
        correctness = 8
    elif relevance >= 6 and word_count >= 15:
        correctness = 7
    elif relevance >= 4:
        correctness = 5
    else:
        correctness = 2

    score = round(
        correctness * 0.55
        + relevance * 0.30
        + clarity * 0.15
    )

    if score >= 9:
        result = "Excellent"
    elif score >= 8:
        result = "Very Good"
    elif score >= 6:
        result = "Mostly Correct"
    elif score >= 4:
        result = "Partially Correct"
    else:
        result = "Incorrect"

    return f"""
Score: {score}/10

Result: {result}

Correctness: {correctness}/10
Relevance: {relevance}/10
Clarity: {clarity}/10

Strengths:

- The candidate attempted to answer the question.
- The response contains relevant information.

Weaknesses:

- The answer should provide more specific technical details.
- A practical example would make the answer stronger.

Improvement Suggestions:

- Answer the exact question directly.
- Explain the reasoning clearly.
- Include a relevant example when possible.

Ideal Answer:

A strong answer should directly address the question, explain the key concept accurately, and provide an appropriate example.
""".strip()


# =========================================================
# MAIN ANSWER EVALUATION FUNCTION
# =========================================================

def evaluate_answer(
    db = None,
    question: str = "",
    answer: str = "",
    job_role: str = ""
):

    answer = answer.strip()
    question = question.strip()

    # -----------------------------------------------------
    # Empty answer
    # -----------------------------------------------------

    if not answer:

        return """
Score: 0/10

Result: No Answer

Correctness: 0/10
Relevance: 0/10
Clarity: 0/10

Strengths:

- No answer was provided.

Weaknesses:

- The interview question was not answered.

Improvement Suggestions:

- Provide a direct answer.
- Explain the main concept.
- Give an example where appropriate.

Ideal Answer:

Please provide an answer to the interview question.
""".strip()

    # -----------------------------------------------------
    # Prevent extremely short meaningless answers
    # -----------------------------------------------------

    if len(answer.split()) <= 2:

        return """
Score: 1/10

Result: Incorrect

Correctness: 1/10
Relevance: 1/10
Clarity: 2/10

Strengths:

- The candidate attempted to respond.

Weaknesses:

- The answer is too short to demonstrate understanding.
- The main concept was not sufficiently explained.

Improvement Suggestions:

- Explain the concept in at least a few sentences.
- Mention important technical points.
- Give an example if possible.

Ideal Answer:

A strong interview answer should explain the concept clearly and accurately.
""".strip()

    ai_evaluation = _evaluate_answer_with_ai(question, answer, job_role)
    if ai_evaluation:
        return ai_evaluation

    # -----------------------------------------------------
    # Use question-specific technical evaluation
    # -----------------------------------------------------

    technical_result = evaluate_technical_answer(
        db,
        question,
        answer
    )


    if technical_result:

        return technical_result

    # -----------------------------------------------------
    # Use general evaluation for questions that do not
    # have a detailed knowledge entry yet.
    # -----------------------------------------------------

    return evaluate_general_answer(
        question,
        answer
    )


def _evaluate_answer_with_ai(
    question: str = "",
    answer: str = "",
    job_role: str = ""
) -> str | None:

    prompt = f"""
Evaluate this interview answer.

Job Role: {job_role or "General"}
Question: {question}
Candidate Answer: {answer}

Respond in this exact format:

Score: X/10

Result: Excellent | Very Good | Mostly Correct | Partially Correct | Incorrect

Correctness: X/10
Relevance: X/10
Clarity: X/10

Strengths:

- point 1
- point 2

Weaknesses:

- point 1
- point 2

Improvement Suggestions:

- suggestion 1
- suggestion 2

Ideal Answer:

Write a strong sample answer here.
"""

    result = _call_openai(
        "answer_evaluation",
        "You are a strict but fair technical interview evaluator.",
        prompt,
        temperature=0.4,
    )

    if not result or "Score:" not in result:
        return None

    return result.strip()


def analyze_skill_gaps(
    job_role: str = "",
    skills: str = "",
    experience: str = ""
) -> str:

    prompt = f"""
Analyze this candidate profile for interview preparation.

Job Role: {job_role}
Skills Listed: {skills}
Experience: {experience}

Provide:
1. Top 3 strengths for this role
2. Top 3 skill gaps or weak areas to focus on
3. 5 recommended topics to revise before the interview
4. Difficulty level suggestion (Easy / Medium / Hard)

Keep the response concise and practical for a student.
"""

    result = _call_openai(
        "skill_analysis",
        "You are a career coach specializing in technical interviews.",
        prompt,
        temperature=0.6,
    )

    if result:
        return result

    role = job_role or "Technical Role"
    skill_list = skills or "general programming fundamentals"

    return f"""Skill Gap Analysis for {role}

Strengths:
- You have listed relevant skills: {skill_list}
- Your experience level ({experience or 'Fresher'}) helps tailor question difficulty
- Mock interviews will improve confidence and communication

Areas to Improve:
- Review core concepts for each listed skill
- Practice explaining answers with examples
- Prepare 1-2 project stories using the STAR method

Recommended Topics:
1. Fundamentals of {skill_list.split(',')[0].strip() if skill_list else 'programming'}
2. Problem-solving and debugging approach
3. Data structures and algorithms basics
4. SQL/database concepts (if applicable)
5. HR/behavioral interview questions

Suggested Interview Difficulty: Medium
""".strip()


def generate_interview_feedback_summary(
    job_role: str = "",
    skills: str = "",
    overall_score: float = 0,
    answers: list | None = None
) -> str:

    answers = answers or []
    answer_summary = []

    for index, item in enumerate(answers, start=1):
        answer_summary.append(
            f"Q{index}: {item.get('question', '')}\n"
            f"Score: {item.get('score', 0)}/100\n"
            f"Answer snippet: {(item.get('answer', '') or '')[:200]}"
        )

    prompt = f"""
Create a final interview performance summary.

Job Role: {job_role}
Skills: {skills}
Overall Score: {overall_score}/100

Interview Details:
{chr(10).join(answer_summary) if answer_summary else 'No detailed answers provided.'}

Provide:
1. Overall performance summary (2-3 sentences)
2. Key strengths shown in the interview
3. Main weaknesses to improve
4. Top 3 action items for the next practice session

Keep it encouraging but honest.
"""

    result = _call_openai(
        "interview_feedback",
        "You are an expert interview coach giving final mock interview feedback.",
        prompt,
        temperature=0.6,
    )

    if result:
        return result

    if overall_score >= 80:
        performance = "Excellent work. You demonstrated strong interview readiness."
    elif overall_score >= 60:
        performance = "Good effort. You have a solid base with room to improve explanations."
    elif overall_score >= 40:
        performance = "Average performance. Focus on fundamentals and clearer answers."
    else:
        performance = "Needs more preparation. Review core concepts and practice regularly."

    return f"""Interview Performance Summary

Overall Score: {overall_score}/100

{performance}

Strengths:
- You completed the full mock interview
- You attempted all questions sincerely
- This session gives a clear baseline for improvement

Weaknesses:
- Some answers need more technical depth
- Add examples and structured explanations
- Review weak topics from your score breakdown

Next Steps:
1. Revisit topics where you scored below 70%
2. Practice 5 questions daily with timed answers
3. Use the dashboard study plan for a 7-day revision schedule
""".strip()
    
# =========================================================
# GENERATE PERSONALIZED STUDY PLAN
# =========================================================

def generate_study_plan(
    job_role: str = "Software Developer",
    weak_topics: str = "",
    score: float = 0
):

    prompt = f"""
You are an expert technical interview coach.

Create a personalized 7-day interview preparation plan.

Job Role:
{job_role}

Weak Topics:
{weak_topics}

Current Score:
{score}/100

Create a simple and practical plan.

For each day provide:

1. Topic
2. What to study
3. Practice activity
4. Interview questions to practice

Keep the plan suitable for a student preparing
for a technical interview.
"""

    result = _call_openai(
        "study_plan",
        "You are an expert interview coach.",
        prompt,
        temperature=0.7,
    )

    if result:
        return result

    # Local fallback study plan generator
    role = job_role if job_role else "Technical Professional"
    topics_str = weak_topics if weak_topics else "Core Concepts and Technical Fundamentals"

    return f"""# 7-Day Personalized Interview Preparation Plan for {role}

**Target Role:** {role}  
**Current Score:** {score}/100  
**Focus Areas:** {topics_str}

---

### Day 1: Core Fundamentals & Paradigm Review
- **Topic:** Foundational theory and key terminology for {role}
- **What to study:** Core definitions, object/data models, and underlying system design principles.
- **Practice Activity:** Write down 5 key technical definitions from memory and compare with official documentation.
- **Interview Questions:**
  1. What are the core architectural building blocks of a {role} project?
  2. What fundamental principles do you apply when designing a modular system?

### Day 2: Focused Weak Area Improvement
- **Topic:** Target Focus Areas: {topics_str}
- **What to study:** In-depth documentation, practical code snippets, and common pitfalls in your weak areas.
- **Practice Activity:** Trace through 2 example scenarios involving {topics_str} step by step.
- **Interview Questions:**
  1. How do you identify and fix bugs related to {topics_str}?
  2. Compare two different solutions or libraries used for {topics_str}.

### Day 3: Data Structures & Problem Solving
- **Topic:** Algorithmic logic and data manipulation
- **What to study:** Array, String, Stack/Queue, and Hash Table operations.
- **Practice Activity:** Write a clean implementation of a search or data-cleaning algorithm from scratch.
- **Interview Questions:**
  1. How would you optimize the performance of a slow routine?
  2. What is the time and space complexity of your recent algorithmic solution?

### Day 4: System Architecture & Defensive Design
- **Topic:** System design, API structure, and robust error handling
- **What to study:** Request/response cycles, error handling strategies, and database transaction safety.
- **Practice Activity:** Sketch a clean architectural block diagram for a scalable Web/API application.
- **Interview Questions:**
  1. How do you design APIs to handle unexpected inputs gracefully?
  2. What steps do you take to guarantee database data consistency?

### Day 5: Practical Hands-on Coding & Testing
- **Topic:** Practical implementation under timed conditions
- **What to study:** Code organization, clean code practices, and unit testing frameworks.
- **Practice Activity:** Build a small standalone demo or test case within 45 minutes.
- **Interview Questions:**
  1. How do you structure unit tests for a critical module?
  2. Walk through a recent debugging session step-by-step.

### Day 6: Behavioral & HR Interview Preparation
- **Topic:** Behavioral questions using the STAR framework (Situation, Task, Action, Result)
- **What to study:** Anecdotes detailing teamwork, handling tight deadlines, and technical decision making.
- **Practice Activity:** Practice speaking your answers aloud with clear STAR structure.
- **Interview Questions:**
  1. Why are you interested in pursuing a {role} position?
  2. Describe a time when you had to adapt quickly to new requirements.

### Day 7: Comprehensive Mock Interview & Final Review
- **Topic:** Full mock interview simulation and final Polish
- **What to study:** Review all notes from Days 1-6 and refine your project elevator pitch.
- **Practice Activity:** Conduct a 30-minute self-timed mock interview covering technical, problem-solving, and HR questions.
- **Interview Questions:**
  1. Summarize your top technical strengths as a {role}.
  2. Do you have any questions about team architecture and development workflow?
""".strip()


# =========================================================
# IDEAL / CORRECT ANSWER LOOKUP
# =========================================================

def extract_ideal_from_evaluation(evaluation: str) -> str:
    """Parse the Ideal Answer section from an AI evaluation string."""
    if not evaluation:
        return ""

    match = re.search(
        r"Ideal Answer:\s*\n([\s\S]+?)(?:\n\n[A-Z][\w\s]+:|$)",
        evaluation,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    match = re.search(r"Ideal Answer:\s*([\s\S]+)", evaluation, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""


def get_ideal_answer(
    db=None,
    question: str = "",
    job_role: str = "",
    stored_ideal: str = "",
    evaluation: str = "",
) -> str:
    """Return the correct/ideal answer for an interview question."""

    if stored_ideal and stored_ideal.strip():
        return stored_ideal.strip()

    question = question.strip()
    if not question:
        return ""

    if db is not None:
        try:
            try:
                from backend.models import AnswerKnowledge
            except ModuleNotFoundError:
                from models import AnswerKnowledge

            record = (
                db.query(AnswerKnowledge)
                .filter(AnswerKnowledge.question_text == question)
                .first()
            )
            if record and record.ideal_answer:
                return record.ideal_answer.strip()
        except Exception as exc:
            print("Notice: ideal answer DB lookup:", exc)

    knowledge = ANSWER_KNOWLEDGE.get(question)
    if knowledge and knowledge.get("answer"):
        return knowledge["answer"].strip()

    try:
        try:
            from backend.rag_service import get_rag_engine
        except ModuleNotFoundError:
            from rag_service import get_rag_engine

        rag = get_rag_engine(db)
        results = rag.retrieve_relevant_context(
            f"{job_role} {question}",
            top_k=2,
        )
        for res in results:
            ideal = res.get("ideal_answer", "")
            if ideal and len(ideal) > 20:
                return ideal.strip()
    except Exception as exc:
        print("Notice: RAG ideal answer lookup:", exc)

    parsed = extract_ideal_from_evaluation(evaluation)
    if parsed:
        return parsed

    ai_ideal = _generate_ideal_answer_with_ai(question, job_role)
    if ai_ideal:
        return ai_ideal

    return (
        "A strong answer should directly address the question, explain the key "
        "concept accurately, and include a relevant example where appropriate."
    )


def _generate_ideal_answer_with_ai(question: str, job_role: str = "") -> str | None:
    prompt = f"""
Write the ideal correct answer for this interview question.

Job Role: {job_role or "General"}
Question: {question}

Provide a concise, accurate model answer (3-6 sentences) that a strong candidate would give.
Do not include scoring or evaluation — only the ideal answer text.
"""

    result = _call_openai(
        "answer_evaluation",
        "You write model interview answers for technical and behavioral questions.",
        prompt,
        temperature=0.4,
    )

    return result.strip() if result else None


# =========================================================
# SENTIMENT & CONFIDENCE ANALYSIS
# =========================================================

POSITIVE_WORDS = {
    "confident", "certain", "definitely", "clearly", "successfully",
    "experienced", "proficient", "strong", "excellent", "effectively",
    "optimized", "implemented", "achieved", "led", "designed", "built",
    "improved", "resolved", "collaborated", "demonstrated",
}

HESITATION_WORDS = {
    "maybe", "perhaps", "might", "possibly", "unsure", "guess",
    "not sure", "i think", "kind of", "sort of", "probably",
    "somewhat", "try", "attempt",
}

NEGATIVE_WORDS = {
    "failed", "unable", "cannot", "don't know", "never", "weak",
    "struggled", "difficult", "confused", "wrong", "bad",
}


def analyze_sentiment_and_confidence(answer: str) -> dict:
    """Analyze communication sentiment and confidence from an answer."""

    if not answer or not answer.strip():
        return {
            "sentiment_score": 0.0,
            "confidence_score": 0.0,
            "sentiment_label": "Neutral",
        }

    text = answer.lower()
    words = set(re.findall(r"[a-z']+", text))
    word_count = len(answer.split())

    positive_hits = sum(1 for w in POSITIVE_WORDS if w in text)
    hesitation_hits = sum(1 for w in HESITATION_WORDS if w in text)
    negative_hits = sum(1 for w in NEGATIVE_WORDS if w in text)

    # Length factor: longer structured answers suggest confidence
    length_bonus = min(word_count / 50, 1.0) * 20

    confidence = 50 + positive_hits * 8 - hesitation_hits * 10 - negative_hits * 5 + length_bonus
    confidence = round(max(0, min(100, confidence)), 1)

    sentiment = 50 + positive_hits * 10 - negative_hits * 12 - hesitation_hits * 5
    sentiment = round(max(0, min(100, sentiment)), 1)

    if sentiment >= 70:
        label = "Positive"
    elif sentiment >= 45:
        label = "Neutral"
    else:
        label = "Negative"

    ai_result = _analyze_sentiment_with_ai(answer)
    if ai_result:
        return ai_result

    return {
        "sentiment_score": sentiment,
        "confidence_score": confidence,
        "sentiment_label": label,
    }


def _analyze_sentiment_with_ai(answer: str) -> dict | None:
    prompt = f"""
Analyze the communication tone of this interview answer.

Answer: {answer}

Respond in this exact format (numbers only, no extra text):
SentimentScore: <0-100>
ConfidenceScore: <0-100>
SentimentLabel: Positive | Neutral | Negative
"""

    result = _call_openai(
        "answer_evaluation",
        "You analyze interview communication tone and confidence.",
        prompt,
        temperature=0.3,
    )

    if not result:
        return None

    try:
        sentiment_match = re.search(r"SentimentScore:\s*(\d+(?:\.\d+)?)", result)
        confidence_match = re.search(r"ConfidenceScore:\s*(\d+(?:\.\d+)?)", result)
        label_match = re.search(r"SentimentLabel:\s*(Positive|Neutral|Negative)", result, re.I)

        if sentiment_match and confidence_match:
            return {
                "sentiment_score": round(float(sentiment_match.group(1)), 1),
                "confidence_score": round(float(confidence_match.group(1)), 1),
                "sentiment_label": label_match.group(1).capitalize() if label_match else "Neutral",
            }
    except (ValueError, AttributeError):
        pass

    return None


# =========================================================
# MULTI-ROUND INTERVIEW GENERATION
# =========================================================

def generate_multi_round_interview(
    db=None,
    job_role: str = "",
    skills: str = "",
    experience: str = "",
    interview_mode: str = "text",
    difficulty: str = "",
    max_questions: int = 0,
) -> dict:
    """Generate structured multi-round interview with technical, coding, and HR rounds."""

    try:
        from backend.dataset import CODING_QUESTIONS, INTERVIEW_ROUNDS, VOICE_PROMPT_QUESTIONS
    except ModuleNotFoundError:
        from dataset import CODING_QUESTIONS, INTERVIEW_ROUNDS, VOICE_PROMPT_QUESTIONS

    skill_questions = find_skill_questions(db, skills, job_role)
    skill_questions = list(dict.fromkeys(skill_questions))
    random.shuffle(skill_questions)

    rounds = []

    level = (difficulty or "").strip().lower()
    level_counts = {
        "easy": {"technical": 2, "coding": 1, "hr": 2},
        "hard": {"technical": 4, "coding": 3, "hr": 1},
    }

    for round_config in INTERVIEW_ROUNDS:
        round_num = round_config["round"]
        round_type = round_config["type"]
        count = level_counts.get(level, {}).get(round_type, round_config["question_count"])
        questions = []

        if round_type == "technical":
            pool = skill_questions[:]
            if len(pool) < count:
                pool.extend(GENERAL_TECHNICAL)
            random.shuffle(pool)
            for q in pool[:count]:
                questions.append({
                    "text": q,
                    "type": "voice" if interview_mode == "voice" else "text",
                    "round": round_num,
                    "round_name": round_config["name"],
                    "difficulty": level or "medium",
                })

            if interview_mode == "voice" and len(questions) < count:
                for vp in VOICE_PROMPT_QUESTIONS[: count - len(questions)]:
                    questions.append({
                        "text": vp,
                        "type": "voice",
                        "round": round_num,
                        "round_name": round_config["name"],
                        "difficulty": level or "medium",
                    })

        elif round_type == "coding":
            coding_pool = _get_coding_questions_from_db(db)
            if not coding_pool:
                coding_pool = CODING_QUESTIONS
            random.shuffle(coding_pool)
            for item in coding_pool[:count]:
                questions.append({
                    "text": item.get("question", item.get("question_text", "")),
                    "type": "coding",
                    "round": round_num,
                    "round_name": round_config["name"],
                    "title": item.get("title", "Coding Problem"),
                    "language": item.get("language", "python"),
                    "starter_code": item.get("starter_code", ""),
                    "test_cases": item.get("test_cases", []),
                    "difficulty": item.get("difficulty") or level or "medium",
                })

        elif round_type == "hr":
            hr_qs = []
            if db is not None:
                try:
                    from backend.models import QuestionItem
                except ModuleNotFoundError:
                    from models import QuestionItem
                try:
                    hr_qs = [
                        q.question_text
                        for q in db.query(QuestionItem)
                        .filter(QuestionItem.category == "hr")
                        .all()
                    ]
                except Exception:
                    pass
            if not hr_qs:
                hr_qs = HR_QUESTIONS
            random.shuffle(hr_qs)
            for q in hr_qs[:count]:
                q_type = "voice" if interview_mode in ("voice", "mixed") else "text"
                questions.append({
                    "text": q,
                    "type": q_type,
                    "round": round_num,
                    "round_name": round_config["name"],
                    "difficulty": level or "medium",
                })

        rounds.append({
            "round": round_num,
            "name": round_config["name"],
            "type": round_type,
            "description": round_config["description"],
            "questions": questions,
        })

    all_questions = []
    for r in rounds:
        all_questions.extend(r["questions"])

    if max_questions and max_questions > 0 and len(all_questions) > max_questions:
        all_questions = all_questions[:max_questions]
        allowed_ids = {id(question) for question in all_questions}
        for interview_round in rounds:
            interview_round["questions"] = [
                question for question in interview_round["questions"]
                if id(question) in allowed_ids
            ]
        rounds = [interview_round for interview_round in rounds if interview_round["questions"]]

    return {
        "total_rounds": len(rounds),
        "interview_mode": interview_mode,
        "difficulty": level or "medium",
        "rounds": rounds,
        "questions": all_questions,
        "total_questions": len(all_questions),
    }


def _get_coding_questions_from_db(db):
    if db is None:
        return []

    try:
        import json
        try:
            from backend.models import QuestionItem
        except ModuleNotFoundError:
            from models import QuestionItem

        items = (
            db.query(QuestionItem)
            .filter(QuestionItem.category == "coding")
            .all()
        )

        result = []
        for item in items:
            test_cases = []
            if item.test_cases_json:
                try:
                    test_cases = json.loads(item.test_cases_json)
                except json.JSONDecodeError:
                    pass
            result.append({
                "title": item.category,
                "question": item.question_text,
                "language": item.language or "python",
                "starter_code": item.starter_code or "",
                "test_cases": test_cases,
            })
        return result
    except Exception:
        return []


# =========================================================
# CODING ANSWER EVALUATION
# =========================================================

def evaluate_coding_answer(
    question: str = "",
    code: str = "",
    test_cases: list = None,
    job_role: str = "",
) -> dict:
    """Evaluate a coding submission with keyword checks and optional AI review."""

    test_cases = test_cases or []
    code = code.strip()

    if not code:
        return {
            "evaluation": "Score: 0/10\n\nNo code was submitted.",
            "score": 0,
            "tests_passed": 0,
            "tests_total": len(test_cases),
        }

    keyword_score = _score_code_keywords(code, question)
    structure_score = _score_code_structure(code)
    tests_passed, tests_total = _check_code_test_cases(code, test_cases)

    test_ratio = tests_passed / tests_total if tests_total > 0 else 0.5
    base_score = (keyword_score * 0.3 + structure_score * 0.3 + test_ratio * 100 * 0.4)
    base_score = round(max(0, min(100, base_score)), 1)

    ai_eval = _evaluate_coding_with_ai(question, code, job_role, tests_passed, tests_total)
    if ai_eval:
        ai_score_match = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", ai_eval, re.I)
        if ai_score_match:
            ai_score = float(ai_score_match.group(1)) * 10
            final_score = round((base_score * 0.4 + ai_score * 0.6), 1)
        else:
            final_score = base_score
        evaluation = ai_eval
        if tests_total > 0:
            evaluation += f"\n\nTest Cases: {tests_passed}/{tests_total} passed"
    else:
        final_score = base_score
        score_10 = round(final_score / 10, 1)
        evaluation = f"""Score: {score_10}/10

Result: {"Excellent" if final_score >= 80 else "Good" if final_score >= 60 else "Needs Improvement"}

Correctness: {round(score_10 * 0.9, 1)}/10
Code Quality: {round(structure_score / 10, 1)}/10
Logic: {round(keyword_score / 10, 1)}/10

Test Cases: {tests_passed}/{tests_total} passed

Strengths:
- Code submitted with {"working logic indicators" if keyword_score > 50 else "basic structure"}

Weaknesses:
- {"Some test cases failed" if tests_passed < tests_total else "Consider edge cases and error handling"}

Improvement Suggestions:
- Add comments explaining your approach
- Handle edge cases (empty input, single element)
- Test your code with the provided examples

Ideal Answer:
A clean, readable solution with proper variable names and correct algorithm logic."""

    return {
        "evaluation": evaluation.strip(),
        "score": final_score,
        "tests_passed": tests_passed,
        "tests_total": tests_total,
    }


def _score_code_keywords(code: str, question: str) -> float:
    code_lower = code.lower()
    score = 30.0

    if "def " in code_lower or "function" in code_lower:
        score += 15
    if "return" in code_lower:
        score += 15
    if "for " in code_lower or "while " in code_lower:
        score += 10
    if "if " in code_lower:
        score += 10
    if len(code.split("\n")) >= 3:
        score += 10
    if "pass" in code_lower and code_lower.count("pass") == code_lower.count("def "):
        score -= 20

    return min(100, max(0, score))


def _score_code_structure(code: str) -> float:
    score = 40.0
    lines = [l for l in code.split("\n") if l.strip()]

    if len(lines) >= 2:
        score += 15
    if not re.search(r"^\s{4,}\S", code, re.MULTILINE) and len(lines) > 1:
        score += 10
    if "#" in code:
        score += 10
    if "pass" in code.lower() and len(lines) <= 3:
        score -= 30

    return min(100, max(0, score))


def _check_code_test_cases(code: str, test_cases: list) -> tuple:
    if not test_cases:
        return 0, 0

    passed = 0
    code_lower = code.lower()

    for tc in test_cases:
        expected = tc.get("expected")
        if expected is None:
            continue

        expected_str = str(expected).lower()
        if expected_str in code_lower:
            passed += 1
            continue

        if isinstance(expected, bool) and expected:
            if "true" in code_lower or "return true" in code_lower.replace(" ", ""):
                passed += 1
        elif isinstance(expected, list):
            if any(str(v).lower() in code_lower for v in expected[:2]):
                passed += 1
        elif isinstance(expected, (int, float)):
            if str(expected) in code:
                passed += 1
        elif isinstance(expected, str):
            if expected.lower() in code_lower or expected[::-1].lower() in code_lower:
                passed += 1

    return passed, len(test_cases)


def _evaluate_coding_with_ai(
    question: str,
    code: str,
    job_role: str,
    tests_passed: int,
    tests_total: int,
) -> str | None:
    prompt = f"""
Evaluate this coding interview submission.

Job Role: {job_role or "Developer"}
Problem: {question}
Candidate Code:
```
{code}
```

Test Cases Passed: {tests_passed}/{tests_total}

Respond in this exact format:

Score: X/10

Result: Excellent | Good | Needs Improvement

Correctness: X/10
Code Quality: X/10
Logic: X/10

Strengths:
- point 1

Weaknesses:
- point 1

Improvement Suggestions:
- suggestion 1

Ideal Answer:
Brief description of optimal approach.
"""

    result = _call_openai(
        "answer_evaluation",
        "You are a coding interview evaluator.",
        prompt,
        temperature=0.4,
    )

    if not result or "Score:" not in result:
        return None

    return result.strip()


# =========================================================
# COMPREHENSIVE INTERVIEW REPORT GENERATOR WITH RAG
# =========================================================

def generate_interview_report(
    interview_data: dict,
    db = None
) -> dict:
    """
    Generate a comprehensive AI Interview Report using RAG domain context.
    Includes: Strong Areas, Weak Areas, Overall Score, Hiring Recommendation & Rationale,
    Competency Breakdown, and Actionable Suggestions.
    """
    try:
        from backend.rag_service import get_rag_engine
    except ModuleNotFoundError:
        from rag_service import get_rag_engine

    job_role = interview_data.get("job_role", "Software Engineer")
    skills = interview_data.get("skills", "General Technical")
    experience = interview_data.get("experience", "Not specified")
    answers = interview_data.get("answers", [])

    # 1. Calculate overall score and category metrics
    total_score = 0.0
    tech_scores = []
    coding_scores = []
    hr_scores = []
    sentiment_scores = []
    confidence_scores = []

    strong_areas = []
    weak_areas = []

    for item in answers:
        raw_score = item.get("score", 0)
        try:
            score_val = float(raw_score)
        except (ValueError, TypeError):
            score_val = 0.0
        if score_val <= 10:
            score_val *= 10
        score_val = max(0.0, min(100.0, score_val))

        q_type = str(item.get("question_type", "text")).lower()
        round_num = item.get("round", 1)
        question_text = item.get("question", "")
        evaluation = item.get("evaluation", "")

        # Sentiment / Confidence tracking
        s_score = item.get("sentiment_score")
        c_score = item.get("confidence_score")
        if s_score is not None:
            sentiment_scores.append(float(s_score))
        if c_score is not None:
            confidence_scores.append(float(c_score))

        # Categorize rounds
        if q_type == "coding" or round_num == 2:
            coding_scores.append(score_val)
        elif round_num == 3 or "hr" in q_type:
            hr_scores.append(score_val)
        else:
            tech_scores.append(score_val)

        # Identify strengths & weaknesses per question
        topic_title = question_text.split("?")[0].strip()
        if len(topic_title) > 60:
            topic_title = topic_title[:57] + "..."

        if score_val >= 75:
            strong_areas.append(f"Demonstrated proficiency in: {topic_title}")
        elif score_val < 60:
            weak_areas.append(f"Needs improvement in: {topic_title}")

    all_scores = [tech_scores, coding_scores, hr_scores]
    flat_scores = [s for sublist in all_scores for s in sublist]
    if flat_scores:
        overall_score = round(sum(flat_scores) / len(flat_scores), 1)
    else:
        overall_score = 0.0

    tech_avg = round(sum(tech_scores) / len(tech_scores), 1) if tech_scores else overall_score
    coding_avg = round(sum(coding_scores) / len(coding_scores), 1) if coding_scores else overall_score
    hr_avg = round(sum(hr_scores) / len(hr_scores), 1) if hr_scores else overall_score
    comm_avg = round(sum(sentiment_scores + confidence_scores) / len(sentiment_scores + confidence_scores), 1) if (sentiment_scores or confidence_scores) else overall_score

    # 2. Retrieve RAG domain context for role and skills
    rag_engine = get_rag_engine(db)
    rag_context = rag_engine.get_job_role_context(job_role, skills)

    # 3. Determine Grade & Recommendation
    if overall_score >= 88:
        grade = "A+"
        recommendation = "STRONG HIRE"
        rec_color = "emerald"
    elif overall_score >= 75:
        grade = "A"
        recommendation = "RECOMMENDED"
        rec_color = "green"
    elif overall_score >= 60:
        grade = "B"
        recommendation = "CONSIDER WITH RESERVATIONS"
        rec_color = "amber"
    else:
        grade = "C"
        recommendation = "NEEDS FURTHER PRACTICE"
        rec_color = "rose"

    # Default fallback strengths & weaknesses if lists are small
    if not strong_areas:
        if overall_score >= 50:
            strong_areas.append(f"Good technical foundation in {job_role} core concepts.")
            strong_areas.append("Clear participation and complete answer submissions.")
        else:
            strong_areas.append("Attempted all assigned interview rounds and questions.")

    if not weak_areas:
        if overall_score >= 80:
            weak_areas.append("Minor technical edge cases could be explored deeper.")
        else:
            weak_areas.append(f"Incomplete coverage of specific {skills} domain concepts.")
            weak_areas.append("Could benefit from practicing structured problem-solving frameworks.")

    # Deduplicate areas
    strong_areas = list(dict.fromkeys(strong_areas))[:5]
    weak_areas = list(dict.fromkeys(weak_areas))[:5]

    # 4. Attempt AI-enhanced report generation with RAG context
    ai_report = _generate_report_with_ai(
        job_role, skills, experience, overall_score,
        tech_avg, coding_avg, hr_avg, comm_avg,
        recommendation, strong_areas, weak_areas, rag_context
    )

    if ai_report:
        return {
            "overall_score": overall_score,
            "grade": grade,
            "recommendation": ai_report.get("recommendation", recommendation),
            "recommendation_reason": ai_report.get("recommendation_reason", f"Candidate scored {overall_score}% overall across technical, coding, and behavioral rounds."),
            "strong_areas": ai_report.get("strong_areas", strong_areas),
            "weak_areas": ai_report.get("weak_areas", weak_areas),
            "category_scores": {
                "technical": tech_avg,
                "coding": coding_avg,
                "hr_behavioral": hr_avg,
                "communication": comm_avg
            },
            "key_recommendations": ai_report.get("key_recommendations", [
                f"Review core documentation for {skills}.",
                "Practice coding problems under timed constraints.",
                "Utilize STAR method for HR behavioral questions."
            ]),
            "rag_context_used": True
        }

    # Rule-based fallback report
    rec_reason = (
        f"Candidate achieved an overall score of {overall_score}% for the {job_role} position. "
        f"Demonstrated technical score: {tech_avg}%, coding score: {coding_avg}%, and behavioral score: {hr_avg}%. "
        f"Based on retrieved benchmark knowledge for {skills}, candidate status is {recommendation}."
    )

    key_recommendations = [
        f"Deepen knowledge in weak technical areas: {', '.join([w.split(': ')[-1] for w in weak_areas[:2]])}.",
        f"Practice problem solving and code structure for {job_role} interview scenarios.",
        "Refine communication clarity and structure using the STAR technique."
    ]

    return {
        "overall_score": overall_score,
        "grade": grade,
        "recommendation": recommendation,
        "recommendation_reason": rec_reason,
        "strong_areas": strong_areas,
        "weak_areas": weak_areas,
        "category_scores": {
            "technical": tech_avg,
            "coding": coding_avg,
            "hr_behavioral": hr_avg,
            "communication": comm_avg
        },
        "key_recommendations": key_recommendations,
        "rag_context_used": True
    }


def _generate_report_with_ai(
    job_role: str,
    skills: str,
    experience: str,
    overall_score: float,
    tech_score: float,
    coding_score: float,
    hr_score: float,
    comm_score: float,
    recommendation: str,
    strong_areas: list,
    weak_areas: list,
    rag_context: str
) -> dict | None:
    prompt = f"""
You are an expert technical interviewer and talent assessor.
Generate a comprehensive interview evaluation report using the provided candidate performance and RAG domain knowledge.

Target Role: {job_role}
Skills: {skills}
Experience Level: {experience}
Overall Score: {overall_score}%
Category Scores:
- Technical Knowledge: {tech_score}%
- Coding & Problem Solving: {coding_score}%
- HR & Behavioral: {hr_score}%
- Communication & Tone: {comm_score}%

Initial Recommendation: {recommendation}

RAG Domain Knowledge Context:
{rag_context[:1000]}

Candidate Strengths Observed:
{str(strong_areas)}

Candidate Weaknesses Observed:
{str(weak_areas)}

Respond strictly in JSON format with these exact keys:
{{
  "recommendation": "{recommendation}",
  "recommendation_reason": "2-3 sentences justifying the hiring decision based on overall performance and role fit.",
  "strong_areas": ["strength 1", "strength 2", "strength 3"],
  "weak_areas": ["weakness 1", "weakness 2", "weakness 3"],
  "key_recommendations": ["actionable advice 1", "actionable advice 2", "actionable advice 3"]
}}
"""
    result = _call_openai(
        "interview_feedback",
        "You output valid JSON interview evaluation reports.",
        prompt,
        temperature=0.3,
    )

    if not result:
        return None

    try:
        import json
        json_match = re.search(r"\{.*\}", result, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            if "strong_areas" in parsed and "weak_areas" in parsed:
                return parsed
    except Exception as exc:
        print("Notice: AI report generation JSON parse error:", exc)

    return None

