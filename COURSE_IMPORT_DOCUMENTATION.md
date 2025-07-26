# Course Data Import System Documentation

## Overview

The Course Data Import System allows you to import real course ratings and slopes from external golf course databases and JSON files. This system enhances the Wolf Goat Pig simulation with authentic course data, including USGA course ratings, slope ratings, and detailed hole information.

## Features

### 🎯 **Multiple Import Sources**
- **USGA Database**: Official United States Golf Association course data
- **GHIN Network**: Golf Handicap and Information Network
- **GolfNow**: GolfNow course database
- **TheGrint**: TheGrint golf course database
- **JSON File Upload**: Custom course data import

### 📊 **Rich Course Data**
- Course ratings and slope ratings
- Detailed hole information (par, yards, handicap)
- Course descriptions and location data
- Contact information and websites
- Multiple tee box configurations

### 🔍 **Smart Search**
- Course name search with fuzzy matching
- State and city filtering for precise results
- Preview functionality before import
- Duplicate detection and update handling

## Setup Instructions

### 1. Environment Variables

Configure API keys for external sources in your `.env` file:

```bash
# USGA API (requires registration)
USGA_API_KEY=your_usga_api_key_here

# GHIN API (optional, basic search works without key)
GHIN_API_KEY=your_ghin_api_key_here

# GolfNow API (requires partnership)
GOLF_NOW_API_KEY=your_golf_now_api_key_here

# TheGrint API (requires partnership)
THEGRINT_API_KEY=your_thegrint_api_key_here
```

### 2. Dependencies

Ensure you have the required Python packages:

```bash
pip install httpx  # For async HTTP requests
```

### 3. Database Setup

The system automatically creates the necessary database tables. No additional setup required.

## API Endpoints

### 1. Import Sources Status

**GET** `/courses/import/sources`

Returns available import sources and their configuration status.

**Response:**
```json
{
  "sources": [
    {
      "name": "USGA",
      "description": "United States Golf Association course database",
      "available": true,
      "requires_api_key": true,
      "endpoint": "/courses/import/search"
    },
    {
      "name": "GHIN",
      "description": "Golf Handicap and Information Network",
      "available": true,
      "requires_api_key": false,
      "endpoint": "/courses/import/search"
    }
  ],
  "configured_sources": 2,
  "total_sources": 5
}
```

### 2. Search and Import Course

**POST** `/courses/import/search`

Search for a course by name and import it.

**Request Body:**
```json
{
  "course_name": "Pebble Beach Golf Links",
  "state": "CA",
  "city": "Pebble Beach"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Course 'Pebble Beach Golf Links' imported successfully from GHIN",
  "course": {
    "name": "Pebble Beach Golf Links",
    "description": "Iconic coastal golf course...",
    "total_par": 72,
    "total_yards": 7075,
    "course_rating": 75.5,
    "slope_rating": 145,
    "holes": [...],
    "source": "GHIN",
    "last_updated": "2024-01-15T10:30:00Z",
    "location": "Pebble Beach, CA",
    "website": "https://www.pebblebeach.com/",
    "phone": "(831) 622-8723"
  }
}
```

### 3. Preview Course (No Import)

**POST** `/courses/import/preview`

Preview course data before importing.

**Request Body:** Same as search endpoint

**Response:** Same as search endpoint but with `"status": "preview"`

### 4. Import from JSON File

**POST** `/courses/import/file`

Upload and import a course from a JSON file.

**Request:** Multipart form data with JSON file

**Response:** Same as search endpoint

## JSON File Format

### Required Fields

```json
{
  "name": "Course Name",
  "holes_data": [
    {
      "hole_number": 1,
      "par": 4,
      "yards": 420,
      "handicap": 5,
      "description": "Hole description",
      "tee_box": "regular"
    }
    // ... 18 holes total
  ]
}
```

### Optional Fields

```json
{
  "name": "Course Name",
  "description": "Course description",
  "course_rating": 72.5,
  "slope_rating": 135,
  "location": "City, State",
  "website": "https://course-website.com",
  "phone": "(555) 123-4567",
  "holes_data": [...]
}
```

### Validation Rules

- **Exactly 18 holes** required
- **Hole numbers** must be 1-18
- **Par values** must be 3, 4, or 5
- **Yards** must be reasonable (100-700 per hole)
- **Handicaps** must be 1-18 (stroke index)
- **Unique handicaps** required (no duplicates)

## Frontend Integration

### Course Import Component

The `CourseImport` React component provides a user-friendly interface:

```jsx
import CourseImport from './CourseImport';

function App() {
  const handleCourseImported = (course) => {
    console.log('Course imported:', course);
    // Refresh course list or update UI
  };

  return (
    <CourseImport
      onClose={() => setShowImport(false)}
      onCourseImported={handleCourseImported}
    />
  );
}
```

### Course Manager Integration

The course import functionality is integrated into the existing `CourseManager`:

```jsx
// Import button in CourseManager
<button onClick={() => setShowImport(true)}>
  📥 Import Course
</button>

// Import modal
{showImport && (
  <CourseImport
    onClose={() => setShowImport(false)}
    onCourseImported={handleCourseImported}
  />
)}
```

## Usage Examples

### 1. Import from External Database

```python
from backend.app.course_import import import_course_by_name, save_course_to_database

# Search and import a course
course_data = await import_course_by_name(
    "Pebble Beach Golf Links", 
    state="CA", 
    city="Pebble Beach"
)

if course_data:
    # Save to database
    success = save_course_to_database(course_data)
    print(f"Import successful: {success}")
```

### 2. Import from JSON File

```python
from backend.app.course_import import import_course_from_json

# Import from JSON file
course_data = await import_course_from_json("course_data.json")

if course_data:
    success = save_course_to_database(course_data)
    print(f"Import successful: {success}")
```

### 3. API Usage

```bash
# Check available sources
curl http://localhost:8000/courses/import/sources

# Search for a course
curl -X POST http://localhost:8000/courses/import/search \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Pebble Beach Golf Links", "state": "CA"}'

# Preview a course
curl -X POST http://localhost:8000/courses/import/preview \
  -H "Content-Type: application/json" \
  -d '{"course_name": "Augusta National", "state": "GA"}'
```

## Error Handling

### Common Error Responses

```json
{
  "detail": "Course 'Course Name' not found in any external database"
}
```

```json
{
  "detail": "Course must have exactly 18 holes"
}
```

```json
{
  "detail": "Invalid JSON format"
}
```

```json
{
  "detail": "USGA API key not configured"
}
```

### Error Recovery

1. **Course Not Found**: Try different search terms or add state/city
2. **API Key Missing**: Configure environment variables
3. **Invalid JSON**: Check file format against schema
4. **Network Errors**: Retry with exponential backoff

## Testing

### Run Import Tests

```bash
# Test the import functionality
python test_course_import.py

# Test with sample data
python -c "
import asyncio
from backend.app.course_import import import_course_from_json
asyncio.run(import_course_from_json('sample_course_import.json'))
"
```

### Test API Endpoints

```bash
# Start the server
cd backend
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/courses/import/sources
```

## Performance Considerations

### Caching

- Course data is cached in the database
- External API calls are minimized
- Import results are stored for reuse

### Rate Limiting

- Respect external API rate limits
- Implement exponential backoff for failures
- Queue large import operations

### Data Validation

- Validate all imported data
- Sanitize user inputs
- Handle malformed responses gracefully

## Security

### API Key Management

- Store API keys in environment variables
- Never commit keys to version control
- Rotate keys regularly

### Input Validation

- Validate all JSON input
- Sanitize file uploads
- Prevent SQL injection

### Access Control

- Implement authentication for import endpoints
- Log all import operations
- Monitor for abuse

## Troubleshooting

### Common Issues

1. **"API key not configured"**
   - Check environment variables
   - Verify API key format
   - Ensure keys are valid

2. **"Course not found"**
   - Try different search terms
   - Add state/city information
   - Check spelling and formatting

3. **"Invalid JSON format"**
   - Validate JSON syntax
   - Check required fields
   - Ensure 18 holes are present

4. **"Database error"**
   - Check database connection
   - Verify table structure
   - Check permissions

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

For issues with external APIs:
- **USGA**: Contact USGA technical support
- **GHIN**: Contact GHIN support team
- **GolfNow**: Contact GolfNow partnership team
- **TheGrint**: Contact TheGrint support

## Future Enhancements

### Planned Features

1. **Bulk Import**: Import multiple courses at once
2. **Course Updates**: Automatic updates from external sources
3. **Course Comparison**: Compare imported courses
4. **Advanced Search**: Filter by rating, slope, location
5. **Course Validation**: Validate against USGA standards

### API Improvements

1. **Webhook Support**: Real-time course updates
2. **GraphQL API**: More flexible querying
3. **Rate Limiting**: Built-in rate limiting
4. **Caching**: Redis-based caching

## Contributing

### Development Setup

1. Clone the repository
2. Install dependencies
3. Configure environment variables
4. Run tests
5. Submit pull request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for all classes/methods
- Write tests for new functionality

---

This documentation covers the complete course import system. For additional help, refer to the API documentation or contact the development team. 