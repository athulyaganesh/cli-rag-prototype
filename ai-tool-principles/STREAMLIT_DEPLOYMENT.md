## **Deployment: Streamlit Web Application**

Deploy the existing Python RAG project as a browser-accessible web application using **Streamlit and Docker**.

Streamlit provides the frontend without requiring a separate React or JavaScript application. It connects directly to the existing Python RAG backend (`rag.py`), so the retrieval and answer-generation logic remains unchanged.

### **Web application interface**

Build a single Streamlit application with two tabs:

**1. Chat Support**

- Chat interface where users can ask questions about the indexed documentation.
- Display generated answers and supporting document citations.
- Show warnings when a question cannot be answered from the documentation.

**2. Email Support**

- Text area where support agents can paste customer emails.
- Generate suggested email replies using the existing RAG pipeline.
- Display supporting citations.
- Allow agents to edit and copy the generated response.
- Flag unsupported questions for human review.

### **Deployment approach**

1. Create `src/app.py` containing the Streamlit interface.
2. Reuse the existing `answer()` function from `rag.py` for both chat and email workflows.
3. Add an email-specific prompt for generating professional customer-support replies.
4. Package the application using Docker.
5. Persist the ChromaDB database using a Docker volume.
6. Deploy the container on the homeserver.
7. Access the application through a browser, optionally using a reverse proxy and authentication.

**Result:** One deployed web application with two interfaces—interactive chat support and AI-assisted email drafting—running on the same existing RAG backend.