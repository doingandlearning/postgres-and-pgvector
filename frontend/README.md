# Frontend for PDF Query System

A simple, responsive HTML frontend for querying PDF documents using vector similarity search and AI enhancement.

## Features

- 🎨 **Modern UI** - Clean, responsive design with gradient backgrounds
- 🤖 **AI-Powered Queries** - Get intelligent responses using OpenAI
- 🔍 **Vector Search** - Search documents without AI enhancement
- 📊 **Rich Results Display** - Shows similarity scores, metadata, and chunk types
- 📱 **Mobile Responsive** - Works great on all device sizes
- ⚡ **Real-time Health Check** - Automatically checks backend connectivity

## Usage

### Option 1: Open Directly in Browser
```bash
# Simply open the HTML file in your browser
open frontend/index.html
```

### Option 2: Serve with Python (Recommended for CORS)
```bash
cd frontend
python3 -m http.server 8000
# Then visit http://localhost:8000
```

### Option 3: Serve with Node.js
```bash
cd frontend
npx serve .
# Then visit the provided URL
```

## Interface Overview

### Query Input
- **Text Area**: Enter your question or search query
- **Enter Key**: Press Enter to submit (Shift+Enter for new line)

### Action Buttons
- **🤖 Query with AI**: Uses the full RAG pipeline with OpenAI enhancement
- **🔍 Search Only**: Returns similar chunks without AI processing
- **Results Input**: Set the number of chunks to return (1-20)

### Results Display

#### AI Response Section
- Shows the enhanced answer from OpenAI
- Only appears when using "Query with AI"
- Includes proper context and citations

#### Document Chunks Section
- **Page Number**: Shows which page the chunk comes from
- **Similarity Score**: Percentage match with your query
- **Chunk Length**: Number of characters in the chunk
- **Type Badge**: Classification of the chunk content:
  - 🔴 **Exception Clause**: Legal exceptions or conditions
  - 🟠 **Table Reference**: References to tables
  - 🟣 **Page Image Reference**: References to images/diagrams
  - 🟢 **Rule or Definition**: Standard rules or definitions

### Error Handling
- **Connection Errors**: Shows if backend is unreachable
- **Query Validation**: Prevents empty queries
- **Server Errors**: Displays backend error messages

## Example Queries

Try these sample queries:
- "What are the frequency allocations for VHF FM broadcasting?"
- "Explain the coordination procedures"
- "What are the technical parameters for transmitters?"
- "Tell me about interference protection"

## Prerequisites

- Backend server running on `http://localhost:5100`
- Documents loaded into the PostgreSQL database
- OpenAI API key configured (for AI queries)

## Troubleshooting

### "Cannot connect to server" Error
1. Make sure the Flask backend is running:
   ```bash
   cd backend
   python app.py
   ```
2. Check that the server is on port 5100
3. Verify your database connection and data

### CORS Issues
- Use a local server instead of opening the file directly
- The backend includes CORS headers, but some browsers are strict

### No Results Found
- Check if documents are properly loaded in the database
- Try simpler or more specific queries
- Verify embeddings were generated correctly

## Browser Compatibility

- ✅ Chrome 60+
- ✅ Firefox 55+
- ✅ Safari 12+
- ✅ Edge 79+

## Customization

The frontend is self-contained in a single HTML file with embedded CSS and JavaScript. You can easily customize:

- **Colors**: Modify the CSS color variables
- **API URL**: Change `API_BASE_URL` in the JavaScript
- **Styling**: Update the CSS classes
- **Behavior**: Modify the JavaScript functions 