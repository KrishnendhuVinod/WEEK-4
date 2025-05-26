import sqlite3
import chromadb
import PyPDF2

# Backend
def setup_sqlite():
    conn = sqlite3.connect('university.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT,
            course_code TEXT,
            year INTEGER,
            semester INTEGER,
            branch TEXT,
            course_outcome TEXT,
            program_outcome TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            question_text TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    conn.commit()
    return conn, c
# Insert sample structured data

def insert_sample_data(c):
    c.execute("SELECT COUNT(*) FROM courses")
    count = c.fetchone()[0]
    if count == 0:
        c.execute('''
            INSERT INTO courses (course_name, course_code, year, semester, branch, course_outcome, program_outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Introduction to AI', 'AI101', 2025, 1, 'CS', 'Understand AI basics', 'Apply problem solving skills'))
        c.execute('''
            INSERT INTO questions (course_id, question_text)
            VALUES (?, ?)
        ''', (1, 'What are the main applications of AI?'))

def insert_question(conn, c, course_id, question_text):
    # Check if question already exists to avoid duplicates
    c.execute("SELECT COUNT(*) FROM questions WHERE question_text = ?", (question_text,))
    exists = c.fetchone()[0]
    if exists == 0:
        c.execute('''
            INSERT INTO questions (course_id, question_text)
            VALUES (?, ?)
        ''', (course_id, question_text))
        conn.commit()


# Setup ChromaDB client
def setup_chromadb():
    client = chromadb.Client()
    collection = client.get_or_create_collection(name="course_texts")
    return collection


# Extract text from uploaded PDF

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + " "
    return text


# Insert PDF text chunks into ChromaDB
def insert_pdf_text_to_chromadb(collection, pdf_text):
    # Simple chunking by sentences (split by '.')
    chunks = [chunk.strip() for chunk in pdf_text.split('.') if chunk.strip()]
    documents = chunks
    metadatas = [{"source": "uploaded_pdf"} for _ in chunks]
    ids = [f"pdf_doc_{i}" for i in range(len(chunks))]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)


# Query ChromaDB to answer user question
def answer_user_question(collection, user_question):
    results = collection.query(
        query_texts=[user_question],
        n_results=3
    )
    answers = results['documents'][0]

    print(f"\nUser question: {user_question}")
    print("System answers:")
    for ans in answers:
        print(f"- {ans}")


# Main function
def main():
    # Setup DB and insert structured sample data
    conn, cursor = setup_sqlite()
    insert_sample_data(cursor)
    conn.commit()

    # Setup ChromaDB
    collection = setup_chromadb()

    # Ask user to input PDF file path (simulate file upload)
    pdf_path = input("Enter the path of your syllabus/textbook PDF: ").strip()
    pdf_text = extract_text_from_pdf(pdf_path)
    insert_pdf_text_to_chromadb(collection, pdf_text)

    # Ask user questions until they quit
    while True:
       question = input("\nAsk a question (or type 'exit' to quit): ").strip()
       if question.lower() == "exit":
          break

    # Insert question dynamically to SQLite DB
       insert_question(conn, cursor, 1, question)  # assuming course_id = 1

    # Query ChromaDB for answer
       answer_user_question(collection, question)

    # Close DB connection
    conn.close()

if __name__ == "__main__":
    main()
