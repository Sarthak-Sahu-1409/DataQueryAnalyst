# Data Query Assistant

A powerful web application that allows users to analyze CSV data using natural language queries. The system leverages AI (Google Gemini) to generate Python code for data analysis and visualization. It supports both AWS S3 and local storage for secure file management, making data exploration accessible to users without programming knowledge.

## 🚀 Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **AI-Powered Code Generation**: Uses Google Gemini 1.5/2.5 Flash to generate Python code
- **Interactive Web Interface**: Modern React-based UI with drag-and-drop file upload and progress indicators
- **Real-time Data Analysis**: Execute generated code and see results instantly
- **Data Visualization**: Generate charts and graphs with matplotlib
- **CSV Metadata Extraction**: Automatic analysis of data structure and sample rows
- **Flexible Storage**: AWS S3 for production, automatic local fallback for development
- **Smart Session Management**: 
  - Persistent conversation memory (keeps last 5 interactions)
  - Secure file handling with automatic cleanup
  - Full session isolation and deletion
- **Encoding Support**: Automatic CSV encoding detection and handling
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## 🏗️ Architecture

The project follows a modern full-stack architecture with flexible storage options and intelligent session management:

### Backend (FastAPI + Python)
- **FastAPI**: High-performance web framework for building APIs
- **LangChain**: Framework for building LLM-powered applications
  - ConversationBufferWindowMemory for context-aware chat
  - RunnableWithMessageHistory for modern LangChain integration
- **Google Gemini**: AI model for code generation
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Data visualization
- **Storage**:
  - AWS S3 (boto3) for production storage
  - Local filesystem fallback for development
  - Automatic encoding detection (chardet)
- **Poetry**: Dependency management

### Frontend (React + Vite)
- **React 19**: Modern UI library
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client with upload progress support
- **Lucide React**: Beautiful icon library
- **Responsive CSS**: Mobile-first design approach

## 📁 Project Structure

```
Data Query Assistant/
├── backend/                    # Python FastAPI backend
│   ├── main.py                # Main FastAPI application
│   ├── utils/                 # Utility modules
│   │   ├── llmhandler.py      # AI code generation & chat memory
│   │   ├── processdata.py     # CSV processing utilities
│   │   ├── pythonexecutor.py  # Code execution engine
│   │   └── local_storage.py   # Local storage fallback
│   ├── uploaded_csv/          # Local storage for sessions
│   │   └── <session_id>/      # Per-session storage
│   │       ├── *.csv          # Uploaded CSV files
│   │       ├── *.png          # Generated visualizations
│   │       └── memory.pkl     # Conversation memory
│   ├── pyproject.toml         # Python dependencies
│   └── poetry.lock            # Locked dependency versions
├── frontend/                  # React frontend
│   └── csv-analyzer-ui/       # Main UI application
│       ├── src/               # React components
│       │   ├── App.jsx        # Main application logic
│       │   └── assets/        # Static assets
│       └── package.json       # Node.js dependencies
└── README.md                  # This file
```

## 🛠️ Prerequisites

Required:
- **Python 3.12+**
- **Node.js 18+**
- **Google Gemini API Key** (for AI code generation)

Optional:
- **AWS Account + S3 Bucket** (for production storage)
  - If not provided, system uses local storage automatically

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Data Query Assistant"
```

### 2. Backend Setup

```bash
cd backend

# Install Poetry (if not already installed)
pip install poetry

# Install dependencies
poetry install

# Create .env file with required environment variables
@"
GOOGLE_API_KEY=your_api_key_here

# AWS credentials (optional - for S3 storage)
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=your_aws_region

# Target S3 bucket (optional)
S3_BUCKET_NAME=your_bucket_name
"@ | Out-File -Encoding utf8 .env

# Note: If S3 credentials are not provided, the system will automatically 
# use local storage in the backend/uploaded_csv directory

# Activate virtual environment
poetry shell
```

### 3. Frontend Setup

```bash
cd frontend/csv-analyzer-ui

# Install dependencies
npm install
```

### 4. Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=your_aws_region
S3_BUCKET_NAME=your_bucket_name
```

## 🏃‍♂️ Running the Application

### Start the Backend

```bash
cd backend
poetry shell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Start the Frontend

```bash
cd frontend/csv-analyzer-ui
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 📖 Usage

### 1. Upload CSV File
- Drag and drop your CSV file onto the upload zone
- Or click to browse and select a file
- The file is stored in AWS S3 under `sessions/{session_id}/{file_name}`
- The system will automatically extract metadata and sample data

### 2. Ask Questions
Type natural language queries about your data, such as:
- "Show me a histogram of the price distribution"
- "What's the correlation between sales and profit?"
- "Create a bar chart of product categories by revenue"
- "Find the top 10 products by sales volume"

### 3. View Results
- **Generated Code**: See the Python code that was created
- **Output**: View the execution results and any printed output
- **Visualizations**: Download generated charts and graphs
- **Metadata**: Explore your data structure and sample rows

## 🔧 API Endpoints

### Backend API

- `POST /upload/` - Uploads CSV file to S3 and returns `session_id` and `file_name`.
- `POST /analyze/` - Downloads the CSV from S3, analyzes with natural language query, returns metadata, code, stdout/stderr, and an optional `image_key` and `image_timestamp` if a chart was generated.
- `POST /clear_session/` - Deletes the session's objects from S3.
- `GET /get_image/` - Fetches a generated image from S3 by `session_id` and `timestamp`.

## 🎯 Example Queries

Here are some example queries you can try with your CSV data:

**Data Analysis:**
- "Calculate the average price of all products"
- "Show me the distribution of product categories"
- "What's the total revenue by month?"

**Visualization:**
- "Create a scatter plot of price vs. rating"
- "Generate a pie chart of sales by region"
- "Show me a line graph of sales over time"

**Statistical Insights:**
- "Find products with prices above the 90th percentile"
- "Calculate the correlation between price and sales"
- "Show me the top 5 performing products"

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 👨‍💻 Author

**Sarthak** - [s.sarthak1357@gmail.com](mailto:s.sarthak1357@gmail.com)

## 🙏 Acknowledgments

- **Google Gemini** for AI-powered code generation
- **FastAPI** for the high-performance backend framework
- **React** for the modern frontend framework
- **Pandas & Matplotlib** for data analysis and visualization
- **AWS S3** for reliable object storage



