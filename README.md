# Resume Analysis Backend

FastAPI backend for intelligent resume analysis using Groq LLM.

## Features

- PDF text extraction using pdfplumber
- AI-powered structured data extraction using Groq LLM
- Supabase database integration
- RESTful API endpoints for resume processing

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
```

### 3. Database Setup

The database schema is already defined in the project. Ensure the following tables exist in your Supabase database:

- `profiles` - User profiles
- `resumes` - Resume file records
- `resume_details` - Parsed resume data

See `schema.md` in the webdevhackathon project for the complete schema.

### 4. Run the Server

```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/resume/analyze

Analyze a resume PDF and extract structured data.

**Request Body:**
```json
{
  "resume_id": "uuid",
  "file_url": "https://...",
  "user_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Resume analyzed successfully",
  "data": {
    "id": "uuid",
    "resume_id": "uuid",
    "skills": ["Python", "JavaScript", "React"],
    "experience": [...],
    "education": [...],
    "projects": [...],
    "parsed_at": "2024-01-01T00:00:00Z"
  }
}
```

### GET /api/resume/{resume_id}/details

Get parsed resume details.

**Query Parameters:**
- `user_id` - User ID for authorization

### GET /api/user/{user_id}/resumes

Get all resumes for a user.

### DELETE /api/resume/{resume_id}

Delete a resume and its details.

**Query Parameters:**
- `user_id` - User ID for authorization

### GET /health

Health check endpoint.

## Architecture

### Services

- **resume_processor.py** - Handles PDF processing and LLM extraction
  - Downloads PDF from Supabase Storage
  - Extracts text using pdfplumber
  - Calls Groq API for structured data extraction

- **supabase_client.py** - Database operations
  - CRUD operations for resumes and resume_details
  - User authorization checks

### Data Flow

1. User uploads PDF via frontend → Supabase Storage
2. Frontend calls backend `/api/resume/analyze`
3. Backend downloads PDF and extracts text
4. Groq LLM structures the data (skills, experience, education, projects)
5. Structured data saved to `resume_details` table
6. Frontend displays parsed resume data

## Groq LLM Integration

The system uses Groq's API to extract structured information from resume text:

- Model: `llama-3.3-70b-versatile`
- Temperature: 0.1 (for consistent extraction)
- Max tokens: 2000

The LLM is prompted to extract:
- Skills (array of strings)
- Experience (company, role, duration, description)
- Education (school, degree, field, year)
- Projects (name, technologies, description)

## Error Handling

All endpoints include comprehensive error handling:
- Invalid file URLs
- PDF extraction failures
- LLM API failures
- Database errors
- Authorization checks

## Development

### Project Structure

```
fast-backend-nov/
├── main.py                 # FastAPI application
├── services/
│   ├── resume_processor.py # PDF processing and LLM
│   └── supabase_client.py  # Database operations
├── .env                    # Environment variables
├── .env.example            # Example environment file
├── pyproject.toml          # Dependencies
└── README.md               # This file
```

### Adding New Features

1. Add service logic to appropriate file in `services/`
2. Define Pydantic models in `main.py`
3. Create endpoint in `main.py`
4. Update this README

## Troubleshooting

### PDF Extraction Issues

- Ensure PDF is not password-protected
- Check file URL is accessible
- Verify PDF is not corrupted

### Groq API Issues

- Verify API key is valid
- Check rate limits
- Monitor response timeouts

### Database Issues

- Verify Supabase credentials
- Check table schemas match expected structure
- Ensure RLS policies allow service role access
