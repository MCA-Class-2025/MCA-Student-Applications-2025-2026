"""Extended interview dataset: coding problems, voice prompts, and round configs."""

CODING_QUESTIONS = [
    {
        "title": "Reverse a String",
        "question": "Write a function `reverse_string(s)` that takes a string and returns the reversed string.",
        "language": "python",
        "starter_code": "def reverse_string(s):\n    # Your code here\n    pass\n",
        "test_cases": [
            {"input": "hello", "expected": "olleh"},
            {"input": "Python", "expected": "nohtyP"},
            {"input": "", "expected": ""},
        ],
        "keywords": ["slice", "[::-1]", "reversed", "loop", "index"],
        "ideal_answer": "Use slicing s[::-1] or iterate from end to start.",
    },
    {
        "title": "Find Maximum in Array",
        "question": "Write a function `find_max(arr)` that returns the largest element in a list of numbers.",
        "language": "python",
        "starter_code": "def find_max(arr):\n    # Your code here\n    pass\n",
        "test_cases": [
            {"input": [3, 7, 2, 9, 1], "expected": 9},
            {"input": [-5, -1, -10], "expected": -1},
            {"input": [42], "expected": 42},
        ],
        "keywords": ["max", "loop", "compare", "iterate"],
        "ideal_answer": "Use max(arr) or iterate comparing each element.",
    },
    {
        "title": "Check Palindrome",
        "question": "Write a function `is_palindrome(s)` that returns True if the string is a palindrome, False otherwise.",
        "language": "python",
        "starter_code": "def is_palindrome(s):\n    # Your code here\n    pass\n",
        "test_cases": [
            {"input": "racecar", "expected": True},
            {"input": "hello", "expected": False},
            {"input": "A", "expected": True},
        ],
        "keywords": ["palindrome", "reverse", "compare", "two pointer"],
        "ideal_answer": "Compare string with its reverse or use two pointers.",
    },
    {
        "title": "Count Vowels",
        "question": "Write a function `count_vowels(s)` that counts the number of vowels (a, e, i, o, u) in a string.",
        "language": "python",
        "starter_code": "def count_vowels(s):\n    # Your code here\n    pass\n",
        "test_cases": [
            {"input": "hello", "expected": 2},
            {"input": "aeiou", "expected": 5},
            {"input": "xyz", "expected": 0},
        ],
        "keywords": ["vowel", "count", "in", "lower"],
        "ideal_answer": "Iterate and count characters in 'aeiou'.",
    },
    {
        "title": "FizzBuzz",
        "question": "Write a function `fizzbuzz(n)` that returns a list of strings from 1 to n. Multiples of 3 → 'Fizz', multiples of 5 → 'Buzz', both → 'FizzBuzz', else the number as string.",
        "language": "python",
        "starter_code": "def fizzbuzz(n):\n    # Your code here\n    pass\n",
        "test_cases": [
            {"input": 5, "expected": ["1", "2", "Fizz", "4", "FizzBuzz"]},
            {"input": 3, "expected": ["1", "2", "Fizz"]},
        ],
        "keywords": ["fizz", "buzz", "modulo", "%", "multiple"],
        "ideal_answer": "Use modulo checks for 3 and 5.",
    },
    {
        "title": "Sum of List",
        "question": "Write a function `sum_list(arr)` that returns the sum of all numbers in a list.",
        "language": "python",
        "starter_code": "def sum_list(arr):\n    # Your code here\n    pass\n",
        "test_cases": [
            {"input": [1, 2, 3, 4], "expected": 10},
            {"input": [], "expected": 0},
            {"input": [-1, 1], "expected": 0},
        ],
        "keywords": ["sum", "loop", "accumulate", "total"],
        "ideal_answer": "Use sum(arr) or accumulate in a loop.",
    },
    {
        "title": "Two Sum (Return Indices)",
        "question": "Write a function `two_sum(nums, target)` that returns indices of two numbers that add up to target. Assume exactly one solution exists.",
        "language": "python",
        "starter_code": "def two_sum(nums, target):\n    # Your code here\n    pass\n",
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
        ],
        "keywords": ["hash", "dict", "complement", "map", "lookup"],
        "ideal_answer": "Use a hash map to store complements.",
    },
    {
        "title": "Remove Duplicates",
        "question": "Write a function `remove_duplicates(arr)` that returns a new list with duplicates removed, preserving order.",
        "language": "python",
        "starter_code": "def remove_duplicates(arr):\n    # Your code here\n    pass\n",
        "test_cases": [
            {"input": [1, 2, 2, 3, 1], "expected": [1, 2, 3]},
            {"input": ["a", "b", "a"], "expected": ["a", "b"]},
        ],
        "keywords": ["set", "seen", "unique", "order"],
        "ideal_answer": "Track seen elements with a set while preserving order.",
    },
]

VOICE_PROMPT_QUESTIONS = [
    "Explain your approach to solving a complex technical problem out loud.",
    "Describe a project you are proud of and the challenges you faced.",
    "How would you explain REST APIs to a non-technical person?",
    "Walk me through how you would debug a production issue.",
    "Tell me about a time you had to learn a new technology quickly.",
]

INTERVIEW_ROUNDS = [
    {
        "round": 1,
        "name": "Technical Round",
        "type": "technical",
        "question_count": 3,
        "description": "Core technical knowledge based on your skills",
    },
    {
        "round": 2,
        "name": "Coding Round",
        "type": "coding",
        "question_count": 2,
        "description": "Hands-on coding problems",
    },
    {
        "round": 3,
        "name": "HR & Behavioral Round",
        "type": "hr",
        "question_count": 2,
        "description": "Communication, teamwork, and culture fit",
    },
]

# Additional technical questions for dataset expansion
EXTRA_TECHNICAL = {
    "javascript": [
        "What is the difference between let, const, and var in JavaScript?",
        "Explain closures in JavaScript with an example.",
        "What is the event loop in JavaScript?",
        "What is the difference between == and === in JavaScript?",
        "What are Promises and async/await?",
    ],
    "react": [
        "What is React and why is it used?",
        "What is the difference between state and props?",
        "What is the Virtual DOM?",
        "What are React Hooks? Name a few.",
        "What is the difference between controlled and uncontrolled components?",
    ],
    "nodejs": [
        "What is Node.js and how is it different from browser JavaScript?",
        "What is npm and what is package.json used for?",
        "Explain the difference between synchronous and asynchronous code in Node.js.",
        "What is middleware in Express.js?",
        "How does Node.js handle concurrency?",
    ],
    "system design": [
        "What is scalability in system design?",
        "What is the difference between vertical and horizontal scaling?",
        "What is a load balancer?",
        "What is caching and why is it important?",
        "Explain the difference between SQL and NoSQL databases.",
    ],
    "devops": [
        "What is CI/CD?",
        "What is Docker and why is it used?",
        "What is the difference between Docker and Kubernetes?",
        "What is infrastructure as code?",
        "What is the purpose of monitoring in production systems?",
    ],
}
