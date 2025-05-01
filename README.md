# Interactive Matplotlib Plot Server

This project provides a FastAPI backend server that accepts Python code for generating Matplotlib plots (both 2D and 3D) and returns them in various formats to be displayed interactively in a Next.js frontend.

## Features

- Execute Matplotlib code securely on the server
- Support for both 2D and 3D plots
- Multiple output formats:
  - Interactive plots (using mpld3)
  - PNG images
  - SVG images
- Customizable plot dimensions
- Example plots included
- Error handling and output capture
- Responsive UI for different screen sizes

## Project Structure

```
project/
├── backend/
│   ├── main.py              # FastAPI server code
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend Docker configuration
├── frontend/
│   ├── pages/               # Next.js pages
│   │   └── index.js         # Plot viewer component
│   ├── styles/              # CSS modules
│   │   └── PlotViewer.module.css  # Styles for the plot viewer
│   ├── package.json         # Frontend dependencies
│   └── Dockerfile           # Frontend Docker configuration
└── docker-compose.yml       # Docker compose configuration
```

## Setup Instructions

### Option 1: Using Docker Compose (Recommended)

1. Make sure you have Docker and Docker Compose installed
2. Clone this repository
3. Create the directory structure as shown above
4. Place the files in their respective directories
5. Run the application:

```bash
docker-compose up
```

6. Access the application at http://localhost:3000

### Option 2: Manual Setup

#### Backend Setup

1. Create a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Run the FastAPI server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

1. Make sure you have Node.js installed
2. Install dependencies:

```bash
cd frontend
npm install
```

3. Run the Next.js development server:

```bash
npm run dev
```

4. Access the application at http://localhost:3000

## Usage

1. Enter your Matplotlib code in the text editor
2. Select the plot type (2D or 3D)
3. Choose the output format (Interactive, PNG, or SVG)
4. Set the desired width and height
5. Click "Generate Plot" to execute the code and display the result
6. Use the examples from the dropdown menu to get started

## Security Considerations

- The server uses AST parsing to perform basic validation of the Python code
- Code execution is isolated with restricted globals
- Error handling captures and returns tracebacks without exposing server details

## Dependencies

### Backend
- FastAPI
- Uvicorn
- Matplotlib
- NumPy
- mpld3
- Pydantic

### Frontend
- Next.js
- React
- CSS Modules

## Future Improvements

- Add authentication to restrict access
- Support for additional plotting libraries (Plotly, Seaborn, etc.)
- Save and share plot functionality
- More interactive features and customization options
- Support for collaborative editing
