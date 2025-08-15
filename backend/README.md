# Backend Documentation

## Overview
This is the backend part of the `pxs` project, which is built using FastAPI. The backend serves as an API for the React frontend.

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd pxs/backend
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```
   pip3 install -r requirements.txt
   ```

## Usage

To run the FastAPI application, execute the following command:
```
python3 app.py
```

Or run directly with Uvicorn:
```
uvicorn app:app --reload
```

The backend will be available at `http://localhost:8000`.

## API Endpoints

- **GET /api**: Returns a welcome message.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.