import json
import shutil

FILE = "data/books_database.json"
BACKUP = "data/books_database_backup.json"

# Create backup first
shutil.copy2(FILE, BACKUP)

with open(FILE, "r", encoding="utf-8") as f:
    books = json.load(f)

new_books = [
    {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "genre": "Historical Fiction",
        "summary": "A young girl learns about justice, racism, and compassion in the American South.",
        "year": 1960
    },
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "genre": "Classic",
        "summary": "A mysterious millionaire's obsession with the past unfolds during the Jazz Age.",
        "year": 1925
    },
    {
        "title": "Jane Eyre",
        "author": "Charlotte Brontë",
        "genre": "Romance",
        "summary": "An independent young woman struggles with love, morality, and social expectations.",
        "year": 1847
    },
    {
        "title": "Wuthering Heights",
        "author": "Emily Brontë",
        "genre": "Romance",
        "summary": "A passionate and tragic story of love, revenge, and obsession.",
        "year": 1847
    },
    {
        "title": "The Alchemist",
        "author": "Paulo Coelho",
        "genre": "Adventure",
        "summary": "A young shepherd follows his dreams in search of a hidden treasure.",
        "year": 1988
    },
    {
        "title": "The Little Prince",
        "author": "Antoine de Saint-Exupéry",
        "genre": "Fantasy",
        "summary": "A young prince travels between planets and learns about love, friendship, and life.",
        "year": 1943
    },
    {
        "title": "The Catcher in the Rye",
        "author": "J. D. Salinger",
        "genre": "Classic",
        "summary": "A teenager reflects on identity, adulthood, and alienation after leaving school.",
        "year": 1951
    },
    {
        "title": "The Lord of the Rings",
        "author": "J. R. R. Tolkien",
        "genre": "Fantasy",
        "summary": "A group of companions journeys to destroy a powerful ring and defeat evil.",
        "year": 1954
    },
    {
        "title": "The Hunger Games",
        "author": "Suzanne Collins",
        "genre": "Science Fiction",
        "summary": "A young woman enters a deadly competition in a dystopian society.",
        "year": 2008
    },
    {
        "title": "The Fault in Our Stars",
        "author": "John Green",
        "genre": "Romance",
        "summary": "Two teenagers form a relationship while dealing with serious illness and uncertainty.",
        "year": 2012
    },
    {
        "title": "The Picture of Dorian Gray",
        "author": "Oscar Wilde",
        "genre": "Classic",
        "summary": "A young man's portrait ages while he remains outwardly young.",
        "year": 1890
    },
    {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "genre": "Science Fiction",
        "summary": "A dystopian society sacrifices individuality and freedom for stability and happiness.",
        "year": 1932
    },
    {
        "title": "The Old Man and the Sea",
        "author": "Ernest Hemingway",
        "genre": "Classic",
        "summary": "An aging fisherman struggles against nature while pursuing a great catch.",
        "year": 1952
    },
    {
        "title": "Fahrenheit 451",
        "author": "Ray Bradbury",
        "genre": "Science Fiction",
        "summary": "A fireman questions a society where books are forbidden and independent thought is suppressed.",
        "year": 1953
    }
]

start_id = max(book.get("id", 0) for book in books) + 1

for index, book in enumerate(new_books, start=start_id):
    book["id"] = index
    books.append(book)

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(books, f, indent=2, ensure_ascii=False)

print(f"Original books: {start_id - 1}")
print(f"Added books: {len(new_books)}")
print(f"Final books: {len(books)}")
print(f"Backup created: {BACKUP}")