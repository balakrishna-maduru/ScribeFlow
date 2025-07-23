#!/bin/bash

# ScribeFlow Complete Application Launcher
# This script handles everything: setup, backend, frontend, and monitoring

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_DIR="backend"
FRONTEND_DIR="app"
LOG_DIR="logs"
PID_FILE="scribeflow.pid"

# Ensure logs directory exists immediately and handle any errors
mkdir -p "$LOG_DIR" 2>/dev/null || {
    echo "Warning: Could not create logs directory, using current directory for logs"
    LOG_DIR="."
}

# Touch the log file to ensure it exists
touch "$LOG_DIR/launcher.log" 2>/dev/null || true

# Logging functions with proper error handling
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    {
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" || true
    } >> "$LOG_DIR/launcher.log" 2>/dev/null || true
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    {
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" || true
    } >> "$LOG_DIR/launcher.log" 2>/dev/null || true
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    {
        echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" || true
    } >> "$LOG_DIR/launcher.log" 2>/dev/null || true
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    {
        echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" || true
    } >> "$LOG_DIR/launcher.log" 2>/dev/null || true
}

log_ai() {
    echo -e "${PURPLE}[AI]${NC} $1"
    {
        echo "$(date '+%Y-%m-%d %H:%M:%S') [AI] $1" || true
    } >> "$LOG_DIR/launcher.log" 2>/dev/null || true
}

# Function to print banner
print_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
   _____ ___________ _____ ____  ______   ______ _      ______          __
  / ____/  _/ ____/ __  /  __ \/ ____/  / ____/ |    / / __ \        /  \
 | (___  ___) |   / / / / /_/ / __/    | |__ | |  |/ / / / /        /____\
  \___ \| |/ |   / / / /  ___/ /___    |  __|| |    / / / /        /      \
  ____) | |\__|  / /_/ / |   / /___|   | |   | |    \/ /_/ /       /        \
 |_____/___/   /_____/__| |/___|      |_|   |__|    \____/       /__________\

    AI-Powered Technical Writing Assistant
    Cross-Platform • Flutter • FastAPI • Multi-AI Integration
EOF
    echo -e "${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -ti:$1 >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    if port_in_use $1; then
        log_warning "Port $1 is in use. Killing existing process..."
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to wait for service to be ready with better feedback
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30  # Reduced from 60 for faster feedback
    local attempt=1

    log_info "Waiting for $service_name to be ready..."
    log_info "Testing URL: $url"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 5 --max-time 10 "$url" >/dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        
        if [ $((attempt % 5)) -eq 0 ]; then
            echo ""
            log_info "Still waiting for $service_name... (attempt $attempt/$max_attempts)"
            
            # Show some debug info every 5 attempts
            if [ "$service_name" = "Backend API" ]; then
                if [ -f "$LOG_DIR/backend.log" ]; then
                    echo "Last few lines from backend log:"
                    tail -n 3 "$LOG_DIR/backend.log" 2>/dev/null || echo "No backend log available"
                fi
            fi
        else
            echo -n "."
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo ""
    log_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    
    # Show logs on failure
    if [ "$service_name" = "Backend API" ] && [ -f "$LOG_DIR/backend.log" ]; then
        echo ""
        echo "Backend logs:"
        tail -n 10 "$LOG_DIR/backend.log" 2>/dev/null || echo "No backend log available"
    fi
    
    return 1
}

# Function to cleanup on exit
cleanup() {
    log_info "Shutting down ScribeFlow services..."
    
    # Read PIDs from file if it exists
    if [ -f "$PID_FILE" ]; then
        while IFS= read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping process $pid"
                kill -TERM "$pid" 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    
    # Kill processes by name as backup
    pkill -f "flutter" 2>/dev/null || true
    pkill -f "uvicorn" 2>/dev/null || true
    
    # Kill specific ports
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    log_success "ScribeFlow shutdown completed"
}

# Function to clean build artifacts and processes
deep_clean() {
    log_info "Performing deep clean of ScribeFlow..."
    
    # 1. Stop all services first
    cleanup
    
    # 2. Clean Flutter build artifacts
    log_info "Cleaning Flutter build artifacts..."
    cd "$FRONTEND_DIR"
    if flutter clean; then
        log_success "Flutter clean completed"
    else
        log_error "Flutter clean failed"
    fi
    
    # 3. Clear Flutter pub cache issues
    log_info "Getting Flutter dependencies..."
    if flutter pub get; then
        log_success "Flutter dependencies updated"
    else
        log_warning "Flutter pub get had issues"
    fi
    
    # 4. Clean Python cache and virtual environment
    log_info "Cleaning Python cache..."
    cd "../$BACKEND_DIR"
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    # 5. Reinstall Python dependencies
    if [ -f "requirements.txt" ]; then
        log_info "Reinstalling Python dependencies..."
        if pip install -r requirements.txt; then
            log_success "Python dependencies reinstalled"
        else
            log_warning "Python dependency installation had issues"
        fi
    fi
    
    # 6. Clean system processes (comprehensive)
    log_info "Cleaning system processes..."
    pkill -f "flutter" 2>/dev/null || true
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "dart" 2>/dev/null || true
    pkill -f "python.*main.py" 2>/dev/null || true
    
    # 7. Force kill ports
    for port in $BACKEND_PORT $FRONTEND_PORT; do
        local pid=$(lsof -t -i:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            log_info "Force killing process on port $port"
            kill -9 $pid 2>/dev/null || true
        fi
    done
    
    # 8. Clean temporary files
    log_info "Cleaning temporary files..."
    cd ..
    rm -f *.log 2>/dev/null || true
    rm -f "$PID_FILE" 2>/dev/null || true
    
    log_success "Deep clean completed - system ready for fresh start"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check Flutter
    if ! command_exists flutter; then
        missing_deps+=("Flutter SDK")
    else
        local flutter_version=$(flutter --version 2>/dev/null | head -n1 | cut -d' ' -f2 || echo "unknown")
        log_info "Flutter version: $flutter_version"
    fi
    
    # Check Python
    if ! command_exists python3; then
        missing_deps+=("Python 3.11+")
    else
        local python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 || echo "unknown")
        log_info "Python version: $python_version"
    fi
    
    # Check curl (needed for health checks)
    if ! command_exists curl; then
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        echo "Please install missing dependencies and try again."
        exit 1
    fi
    
    log_success "All prerequisites are installed"
}

# Function to check project structure
check_project_structure() {
    log_info "Validating project structure..."
    
    local required_files=(
        "DESIGN.md"
        "README.md"
        "$BACKEND_DIR/app/main.py"
        "$BACKEND_DIR/requirements.txt"
        "$FRONTEND_DIR/pubspec.yaml"
        "$FRONTEND_DIR/lib/main.dart"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        log_error "Missing required project files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    log_success "Project structure is valid"
}

# Function to setup backend
setup_backend() {
    log_info "Setting up FastAPI backend..."
    
    cd "$BACKEND_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip >/dev/null 2>&1
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install -q -r requirements.txt
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating environment configuration..."
        cat > .env << EOF
# ScribeFlow Backend Configuration
DATABASE_URL=sqlite+aiosqlite:///./scribeflow.db
SECRET_KEY=your-secret-key-change-in-production-$(date +%s)
DEBUG=true

# AI Provider Keys (Add your actual keys here)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google OAuth (Add your actual credentials)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
EOF
        log_warning "Please add your API keys to $BACKEND_DIR/.env"
    fi
    
    cd ..
    log_success "Backend setup completed"
}

# Function to setup frontend
setup_frontend() {
    log_info "Setting up Flutter frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Clean previous builds
    flutter clean >/dev/null 2>&1
    
    # Get dependencies
    log_info "Installing Flutter dependencies..."
    if ! flutter pub get 2>/dev/null; then
        log_error "Failed to install Flutter dependencies"
        cd ..
        return 1
    fi
    
    # Check for web support
    if ! flutter devices 2>/dev/null | grep -q "Chrome"; then
        log_warning "Chrome not available for Flutter web. Enabling web support..."
        flutter config --enable-web >/dev/null 2>&1
    fi
    
    cd ..
    log_success "Frontend setup completed"
}

# Function to start backend with better error handling
start_backend() {
    log_info "Starting FastAPI backend on port $BACKEND_PORT..."
    
    # Kill any existing process on port
    kill_port $BACKEND_PORT
    
    cd "$BACKEND_DIR"
    
    # Check if venv exists and activate it
    if [ ! -d "venv" ]; then
        log_error "Virtual environment not found. Please run setup first."
        cd ..
        return 1
    fi
    
    source venv/bin/activate
    
    # Check if main.py exists
    if [ ! -f "app/main.py" ]; then
        log_error "Backend main.py not found. Cannot start backend."
        cd ..
        return 1
    fi
    
    # Start backend in background
    log_info "Launching backend server..."
    log_info "Command: uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT"
    
    nohup uvicorn app.main:app \
        --reload \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --log-level info \
        > "../$LOG_DIR/backend.log" 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID >> "../$PID_FILE"
    
    cd ..
    
    # Give backend a moment to start
    sleep 3
    
    # Check if the process is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        log_error "Backend process died immediately. Check logs:"
        if [ -f "$LOG_DIR/backend.log" ]; then
            tail -n 10 "$LOG_DIR/backend.log"
        fi
        return 1
    fi
    
    # Wait for backend to be ready
    if wait_for_service "http://localhost:$BACKEND_PORT/" "Backend API"; then
        log_success "Backend started successfully (PID: $BACKEND_PID)"
        log_info "Backend API: http://localhost:$BACKEND_PORT"
        log_info "API Documentation: http://localhost:$BACKEND_PORT/docs"
        return 0
    else
        log_error "Backend failed to start properly"
        if [ -f "$LOG_DIR/backend.log" ]; then
            echo ""
            echo "Backend logs:"
            tail -n 20 "$LOG_DIR/backend.log"
        fi
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    log_info "Starting Flutter frontend on port $FRONTEND_PORT..."

    # Kill any existing process on port
    kill_port $FRONTEND_PORT

    cd "$FRONTEND_DIR"

    # Check if pubspec.yaml exists
    if [ ! -f "pubspec.yaml" ]; then
        log_error "Frontend pubspec.yaml not found. Cannot start frontend."
        cd ..
        return 1
    fi

    log_info "Launching frontend application..."
    log_info "Command: flutter run -d web-server --web-port $FRONTEND_PORT"

    # Start frontend in background
    nohup flutter run -d web-server --web-port $FRONTEND_PORT \
        > "../$LOG_DIR/frontend.log" 2>&1 &

    FRONTEND_PID=$!
    echo $FRONTEND_PID >> "../$PID_FILE"

    cd ..

    # Give frontend a moment to start compiling
    sleep 5

    # Check if the process is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        log_error "Frontend process died immediately. Check logs:"
        if [ -f "$LOG_DIR/frontend.log" ]; then
            tail -n 10 "$LOG_DIR/frontend.log"
        fi
        return 1
    fi

    # Wait for frontend to be ready
    if wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend App"; then
        log_success "Frontend started successfully (PID: $FRONTEND_PID)"
        log_info "Application URL: http://localhost:$FRONTEND_PORT"
        return 0
    else
        log_error "Frontend failed to start properly"
        if [ -f "$LOG_DIR/frontend.log" ]; then
            echo ""
            echo "Frontend logs:"
            tail -n 20 "$LOG_DIR/frontend.log"
        fi
        return 1
    fi
}
# Quick status check function
quick_status() {
    echo ""
    echo -e "${CYAN}🚀 ScribeFlow Quick Status${NC}"
    echo "=========================="
    
    # Backend check
    echo -n "Backend (port $BACKEND_PORT): "
    if curl -s --connect-timeout 2 "http://localhost:$BACKEND_PORT/" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Running${NC}"
    else
        echo -e "${RED}❌ Not responding${NC}"
    fi
    
    # Frontend check
    echo -n "Frontend (port $FRONTEND_PORT): "
    if curl -s --connect-timeout 2 "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Running${NC}"
    else
        echo -e "${RED}❌ Not responding${NC}"
    fi
    
    echo ""
    echo "URLs:"
    echo "  🌐 Application: http://localhost:$FRONTEND_PORT"
    echo "  🔧 API: http://localhost:$BACKEND_PORT"
    echo "  📚 API Docs: http://localhost:$BACKEND_PORT/docs"
    echo ""
}

# Function for full-stack start
full_start() {
    print_banner
    echo -e "${GREEN}Starting ScribeFlow Application (Full Stack Mode)...${NC}"
    echo ""

    # Set trap for cleanup on exit
    trap cleanup EXIT INT TERM

    # Run checks
    check_prerequisites
    check_project_structure

    # Setup
    setup_backend || { log_error "Backend setup failed"; exit 1; }
    setup_frontend || { log_error "Frontend setup failed"; exit 1; }

    # Start services
    start_backend || { log_error "Failed to start backend"; exit 1; }
    start_frontend || { log_error "Failed to start frontend"; cleanup; exit 1; }

    log_success "ScribeFlow is running!"
    quick_status

    echo "Press Ctrl+C to stop all services."

    # Wait for any process to exit, then the trap will handle cleanup
    wait -n
}

# Simple start function with frontend and auto-restart
simple_start() {
    print_banner
    echo -e "${GREEN}Starting ScribeFlow Application (Full Stack Mode)...${NC}"
    echo ""
    
    # Set trap for cleanup on exit
    trap cleanup EXIT INT TERM
    
    # Basic checks
    if [ ! -d "$BACKEND_DIR" ] || [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Backend or Frontend directory not found!"
        exit 1
    fi
    
    log_info "Setting up backend..."
    setup_backend || {
        log_error "Backend setup failed"
        exit 1
    }
    
    log_info "Setting up frontend..."
    setup_frontend || {
        log_error "Frontend setup failed"
        exit 1
    }
    
    log_info "Starting backend..."
    if start_backend; then
        log_success "Backend is running!"
        
        log_info "Starting frontend..."
        if start_frontend; then
            log_success "Frontend is running!"
            quick_status
            
            echo "Both services are ready! You can:"
            echo "1. Visit the application at: http://localhost:$FRONTEND_PORT"
            echo "2. View API docs at: http://localhost:$BACKEND_PORT/docs"
            echo "3. Press Ctrl+C to stop all services"
            echo ""
            echo "Monitoring services for stability..."
            
            # Keep running and monitor both services with auto-restart
            local restart_count=0
            local max_restarts=3
            
            while true; do
                sleep 15  # Check every 15 seconds
                backend_ok=false
                frontend_ok=false
                
                if curl -s --connect-timeout 3 "http://localhost:$BACKEND_PORT/" >/dev/null 2>&1; then
                    backend_ok=true
                fi
                
                if curl -s --connect-timeout 3 "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
                    frontend_ok=true
                fi
                
                # Handle backend failure
                if [ "$backend_ok" = false ]; then
                    log_error "Backend stopped responding"
                    if [ $restart_count -lt $max_restarts ]; then
                        restart_count=$((restart_count + 1))
                        log_warning "Attempting to restart backend (attempt $restart_count/$max_restarts)..."
                        
                        # Try to restart backend
                        kill_port $BACKEND_PORT
                        sleep 2
                        if start_backend; then
                            log_success "Backend restarted successfully!"
                            continue
                        else
                            log_error "Backend restart failed"
                            break
                        fi
                    else
                        log_error "Maximum restart attempts reached for backend"
                        break
                    fi
                fi
                
                # Handle frontend failure  
                if [ "$frontend_ok" = false ]; then
                    log_warning "Frontend stopped responding - this is common with Flutter development server"
                    if [ $restart_count -lt $max_restarts ]; then
                        restart_count=$((restart_count + 1))
                        log_warning "Attempting to restart frontend (attempt $restart_count/$max_restarts)..."
                        
                        # Try to restart frontend
                        kill_port $FRONTEND_PORT
                        sleep 3
                        if start_frontend; then
                            log_success "Frontend restarted successfully!"
                            restart_count=0  # Reset on successful restart
                            continue
                        else
                            log_error "Frontend restart failed"
                            break
                        fi
                    else
                        log_error "Maximum restart attempts reached for frontend"
                        break
                    fi
                fi
                
                # Reset restart count if both services are healthy
                if [ "$backend_ok" = true ] && [ "$frontend_ok" = true ]; then
                    if [ $restart_count -gt 0 ]; then
                        restart_count=0
                        log_success "Services are stable again"
                    fi
                fi
            done
        else
            log_error "Frontend failed to start"
            cleanup
            exit 1
        fi
    else
        log_error "Failed to start backend"
        exit 1
    fi
}

# Main execution function
main() {
    # Ensure we're in the right directory
    if [ ! -f "DESIGN.md" ] || [ ! -d "backend" ] || [ ! -d "app" ]; then
        echo -e "${RED}[ERROR]${NC} Please run this script from the ScribeFlow root directory"
        echo "Current directory: $(pwd)"
        echo "Expected files: DESIGN.md, backend/, app/"
        exit 1
    fi
    
    # Handle command line arguments
    case "${1:-start}" in
        "full")
            full_start
            ;;
        "start"|"simple")
            simple_start
            ;;
        "stop")
            echo -e "${YELLOW}Stopping ScribeFlow services...${NC}"
            cleanup
            ;;
        "restart")
            echo -e "${YELLOW}Restarting ScribeFlow services with deep clean...${NC}"
            deep_clean
            sleep 3
            simple_start
            ;;
        "status")
            quick_status
            ;;
        "logs")
            echo -e "${GREEN}=== Backend Logs ===${NC}"
            if [ -f "$LOG_DIR/backend.log" ]; then
                tail -n 20 "$LOG_DIR/backend.log"
            else
                echo "No backend logs found"
            fi
            echo ""
            echo -e "${GREEN}=== Frontend Logs ===${NC}"
            if [ -f "$LOG_DIR/frontend.log" ]; then
                tail -n 20 "$LOG_DIR/frontend.log"
            else
                echo "No frontend logs found"
            fi
            echo ""
            echo -e "${PURPLE}=== Launcher Logs ===${NC}"
            if [ -f "$LOG_DIR/launcher.log" ]; then
                tail -n 20 "$LOG_DIR/launcher.log"
            else
                echo "No launcher logs found"
            fi
            ;;
        "clean")
            echo -e "${YELLOW}Performing comprehensive cleanup...${NC}"
            deep_clean
            ;;
        "deepclean")
            echo -e "${YELLOW}Performing deep clean of all artifacts and processes...${NC}"
            deep_clean
            ;;
        "quickclean")
            echo -e "${YELLOW}Performing quick cleanup...${NC}"
            cleanup
            rm -rf "$LOG_DIR"
            rm -f "$PID_FILE"
            if [ -d "$FRONTEND_DIR" ]; then
                cd "$FRONTEND_DIR" && flutter clean >/dev/null 2>&1 && cd ..
            fi
            if [ -d "$BACKEND_DIR" ]; then
                cd "$BACKEND_DIR" && rm -rf __pycache__ .pytest_cache *.pyc 2>/dev/null && cd ..
            fi
            log_success "Quick cleanup completed"
            ;;
        "help"|*)
            print_banner
            echo ""
            echo -e "${CYAN}ScribeFlow Application Launcher${NC}"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo -e "${GREEN}Commands:${NC}"
            echo "  start/simple   Start backend and frontend (default)"
            echo "  full           Start with full checks and validation"
            echo "  stop           Stop all services"
            echo "  restart        Stop and start all services with deep clean"
            echo "  status         Show service status"
            echo "  logs           Show recent logs"
            echo "  clean          Deep clean build artifacts and processes"
            echo "  deepclean      Comprehensive clean with dependency reinstall"
            echo "  quickclean     Basic cleanup without dependency changes"
            echo "  help           Show this help message"
            echo ""
            echo -e "${BLUE}Examples:${NC}"
            echo "  $0             # Start full application"
            echo "  $0 status      # Check status"
            echo "  $0 stop        # Stop everything"
            echo "  $0 restart     # Deep clean restart"
            echo "  $0 clean       # Clean build artifacts"
            ;;
    esac
}

# Run main function with all arguments
main "$@"