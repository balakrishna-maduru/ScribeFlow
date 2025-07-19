# ScribeFlow

**AI-powered cross-platform technical writing assistant built with Flutter and FastAPI**

ScribeFlow is an intelligent writing assistant designed for technical storytellers. It combines the power of AI-enhanced text editing with executable code blocks and seamless publishing capabilities across multiple platforms.

## 🚀 Features

- ✨ **AI-Enhanced Writing**: Multi-provider AI integration (Google Gemini, OpenAI, Claude) for intelligent text enhancement
- 📝 **Rich Text Editor**: Powerful editor with syntax highlighting and markdown support
- ⚡ **Code Execution**: Run code snippets directly in the editor with live output
- 🔄 **Cross-Platform**: Single codebase for iOS, Android, Windows, macOS, and Linux
- 📤 **Multi-Platform Publishing**: Direct publishing to Medium, Blogger, and other platforms
- 🔐 **Secure Authentication**: Google OAuth 2.0 with JWT token management
- 💾 **Offline Support**: Local storage with cloud synchronization
- 🎨 **Modern UI**: Beautiful, responsive design with dark mode support

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Flutter App    │    │  FastAPI        │    │  AI Providers   │
│  (All Platforms)│◄──►│  Backend        │◄──►│  (Multi-AI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Local Storage  │    │  PostgreSQL     │    │  Publishing     │
│  (SQLite)       │    │  Database       │    │  APIs           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Frontend (Flutter)
- **Flutter SDK 3.16+** - Cross-platform UI framework
- **Dart 3.0+** - Programming language
- **Riverpod** - State management
- **flutter_quill** - Rich text editor
- **dio** - HTTP client
- **google_sign_in** - Authentication
- **flutter_secure_storage** - Secure token storage
- **go_router** - Navigation

### Backend (Python)
- **FastAPI** - Web framework
- **Python 3.11+** - Programming language
- **PostgreSQL 15+** - Database
- **SQLAlchemy 2.0** - ORM
- **Docker** - Containerization
- **Redis** - Caching
- **google-generativeai** - Google Gemini API
- **openai** - OpenAI GPT models
- **anthropic** - Claude models

### Infrastructure
- **Google Cloud Platform** - Cloud hosting
- **Docker & Kubernetes** - Container orchestration
- **GitHub Actions** - CI/CD
- **Nginx** - Load balancer

## 📁 Project Structure

```
ScribeFlow/
├── app/                          # Flutter application
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app/
│   │   ├── features/
│   │   ├── shared/
│   │   └── core/
│   ├── pubspec.yaml
│   ├── analysis_options.yaml
│   └── README.md
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── infrastructure/               # Infrastructure as Code
│   ├── docker-compose.yml
│   ├── kubernetes/
│   └── terraform/
├── docs/                         # Documentation
│   ├── api/
│   ├── deployment/
│   └── user-guide/
├── .github/                      # GitHub Actions workflows
│   └── workflows/
├── scripts/                      # Development scripts
├── DESIGN.md                     # Complete design document
├── README.md                     # This file
└── LICENSE
```

## 🚀 Quick Start

### Prerequisites

- **Flutter SDK 3.16+**
- **Python 3.11+**
- **PostgreSQL 15+**
- **Docker** (optional)
- **Google Cloud Account** (for AI APIs)

### 1. Clone the Repository

```bash
git clone https://github.com/balakrishna-maduru/ScribeFlow.git
cd ScribeFlow
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database URL

# Run database migrations
python scripts/migrate.py

# Start the backend server
uvicorn app.main:app --reload
```

### 3. Flutter App Setup

```bash
cd app
flutter pub get
flutter run
```

### 4. Docker Setup (Alternative)

```bash
docker-compose up --build
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/scribeflow

# AI Providers
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your_jwt_secret_key

# Publishing
MEDIUM_CLIENT_ID=your_medium_client_id
MEDIUM_CLIENT_SECRET=your_medium_client_secret
```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sign-In API
4. Create OAuth 2.0 credentials
5. Add authorized domains and redirect URIs

## 📚 Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Flutter tests
cd app
flutter test
```

### Code Generation (Flutter)

```bash
cd app
dart run build_runner build
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## 🚢 Deployment

### Production Deployment

```bash
# Build Flutter apps for all platforms
cd app
flutter build apk
flutter build ios
flutter build windows
flutter build macos
flutter build linux

# Deploy backend to Google Cloud Run
cd backend
docker build -t gcr.io/your-project/scribeflow-api .
docker push gcr.io/your-project/scribeflow-api
gcloud run deploy scribeflow-api --image gcr.io/your-project/scribeflow-api
```

### CI/CD

The project includes GitHub Actions workflows for:
- Automated testing
- Cross-platform builds
- Docker image creation
- Deployment to staging/production

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Roadmap

### Phase 1: Foundation (Weeks 1-2)
- ✅ Project structure and setup
- ✅ Authentication system
- ✅ Basic Flutter app shell

### Phase 2: Core Features (Weeks 3-4)
- 🔄 Rich text editor integration
- 🔄 AI enhancement system
- 🔄 Code execution engine

### Phase 3: Advanced Features (Weeks 5-8)
- 📋 Publishing workflow
- 📋 Offline synchronization
- 📋 Advanced UI/UX features

### Phase 4: Polish & Launch (Weeks 9-12)
- 📋 Performance optimization
- 📋 Testing and bug fixes
- 📋 App store deployment

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Flutter](https://flutter.dev/) - UI framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Google Gemini](https://ai.google.dev/) - AI capabilities
- [OpenAI](https://openai.com/) - AI models
- [Anthropic](https://www.anthropic.com/) - Claude AI

## 📞 Support

- 📧 Email: support@scribeflow.app
- 💬 Discord: [ScribeFlow Community](https://discord.gg/scribeflow)
- 🐛 Issues: [GitHub Issues](https://github.com/balakrishna-maduru/ScribeFlow/issues)
- 📖 Documentation: [docs.scribeflow.app](https://docs.scribeflow.app)

---

**Built with ❤️ for technical storytellers worldwide**
