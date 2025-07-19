ScribeFlow: Elaborate Design Document

  I. Core Philosophy & Design Principles

  ScribeFlow is an intelligent writing assistant designed for technical storytellers. It's not just an editor; it's a creative partner that helps you refine your prose, validate your code, and publish your work seamlessly.

   * Principle 1: Seamless Workflow: The user should move fr  Here is the complete journey a user will take through ScribeFlow:

  **Authentication Flow:**
  App Launch -> Check Auth Status -> [Not Authenticated] -> Login Screen -> Google OAuth -> Token Validation -> Main App

  **Core Writing Flow:**
  Main App -> Create New Story -> Write Content -> Select Text -> Click "Enhance with AI"
      |
      -> Review AI Suggestions (Diff View) -> [Accept] or [Reject] or [Refine with Instructions]
      |
      -> Select Code Snippet -> Click "Run" -> View Output in Console -> Modify Code & Rerun
      |
      -> Finalize Story -> Click "Publish" -> Configure (Tags, Status) -> Publish to Medium/Blogger -> End

  **Session Management:**
  Throughout usage -> Auto Token Refresh -> [If Expired] -> Re-authenticate -> Continue Seamlesslypublished article without ever leaving the application. The context switching between writing, coding, and publishing is eliminated.
   * Principle 2: Iterative Enhancement: The AI is a collaborator, not a replacement. The user is always in control, with the ability to accept, reject, and refine AI suggestions in a conversational loop.
   * Principle 3: Trust & Verification: Technical content must be accurate. Embedded code snippets are not just text; they are runnable and testable, giving both the author and the reader confidence in the content.

  II. Authentication & User Management System

  ### 2.1 Google OAuth 2.0 Authentication Flow

  ScribeFlow uses Google OAuth 2.0 as the primary authentication mechanism to provide secure, seamless access while leveraging users' existing Google accounts.

  **Authentication Requirements:**
   * Users must authenticate with Google before accessing any app features
   * JWT tokens with refresh mechanism for session management
   * Secure storage of authentication tokens
   * Automatic token refresh and session validation
   * Graceful handling of authentication failures

  ### 2.2 User Authentication Workflow

  ```
  App Launch → Check Stored Auth → [Valid?] → Main App
      ↓                              ↓
  Login Screen ← [Invalid] ← Token Validation
      ↓
  Google OAuth Flow → Token Exchange → Store Tokens → Main App
      ↓
  [Error Handling] → Retry/Fallback
  ```

  **Detailed Authentication Steps:**

  1. **App Initialization**:
     - Check for stored authentication tokens in secure storage
     - Validate token expiry and refresh if needed
     - Redirect to appropriate screen based on auth state

  2. **Google Sign-In Process**:
     - Display branded login screen with Google Sign-In button
     - Initiate Google OAuth 2.0 flow using `google_sign_in` package
     - Handle consent screen and permissions
     - Exchange authorization code for access/refresh tokens

  3. **Token Management**:
     - Store tokens securely using `flutter_secure_storage`
     - Implement automatic token refresh mechanism
     - Handle token expiration gracefully
     - Provide logout functionality with proper token cleanup

  4. **Backend Validation**:
     - Verify Google ID tokens on the backend
     - Create or update user profile in PostgreSQL database
     - Generate application-specific JWT tokens
     - Implement role-based access control (if needed)

  ### 2.3 Flutter Authentication Implementation

  **Core Authentication Service:**

  ```dart
  class AuthService {
    final GoogleSignIn _googleSignIn;
    final FlutterSecureStorage _secureStorage;
    final Dio _dio;
    
    // Google Sign-In
    Future<User?> signInWithGoogle();
    
    // Token Management
    Future<void> storeTokens(AuthTokens tokens);
    Future<AuthTokens?> getStoredTokens();
    Future<bool> refreshTokens();
    
    // Session Management
    Future<bool> isAuthenticated();
    Future<void> signOut();
    
    // Backend Communication
    Future<User> validateWithBackend(String idToken);
  }
  ```

  **Authentication State Management (Riverpod):**

  ```dart
  @riverpod
  class AuthNotifier extends _$AuthNotifier {
    @override
    AuthState build() => const AuthState.initial();
    
    Future<void> signIn() async {
      state = const AuthState.loading();
      try {
        final user = await _authService.signInWithGoogle();
        if (user != null) {
          state = AuthState.authenticated(user);
        } else {
          state = const AuthState.unauthenticated();
        }
      } catch (e) {
        state = AuthState.error(e.toString());
      }
    }
    
    Future<void> signOut() async {
      await _authService.signOut();
      state = const AuthState.unauthenticated();
    }
  }
  ```

  ### 2.4 Backend Authentication Implementation

  **FastAPI Authentication Endpoints:**

  ```python
  from fastapi import FastAPI, Depends, HTTPException
  from google.auth.transport import requests
  from google.oauth2 import id_token
  
  @app.post("/auth/google")
  async def authenticate_google(token_data: GoogleTokenRequest):
      try:
          # Verify Google ID token
          idinfo = id_token.verify_oauth2_token(
              token_data.id_token, requests.Request(), GOOGLE_CLIENT_ID
          )
          
          # Extract user information
          user_email = idinfo['email']
          user_name = idinfo['name']
          google_id = idinfo['sub']
          
          # Create or update user in database
          user = await get_or_create_user(
              email=user_email,
              name=user_name,
              google_id=google_id
          )
          
          # Generate JWT token
          access_token = create_access_token(data={"sub": user.id})
          refresh_token = create_refresh_token(data={"sub": user.id})
          
          return {
              "access_token": access_token,
              "refresh_token": refresh_token,
              "token_type": "bearer",
              "user": user.dict()
          }
          
      except ValueError:
          raise HTTPException(status_code=401, detail="Invalid token")
  ```

  ### 2.5 User Interface Design

  **Login Screen Components:**

  ```dart
  class LoginScreen extends ConsumerWidget {
    @override
    Widget build(BuildContext context, WidgetRef ref) {
      final authState = ref.watch(authNotifierProvider);
      
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // ScribeFlow Logo
              Image.asset('assets/logo.png', height: 120),
              
              const SizedBox(height: 32),
              
              // Welcome Text
              Text(
                'Welcome to ScribeFlow',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              
              Text(
                'Your intelligent writing companion',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              
              const SizedBox(height: 48),
              
              // Google Sign-In Button
              authState.when(
                loading: () => const CircularProgressIndicator(),
                error: (error) => Column(
                  children: [
                    Text('Error: $error'),
                    const SizedBox(height: 16),
                    _buildSignInButton(ref),
                  ],
                ),
                data: (_) => _buildSignInButton(ref),
              ),
            ],
          ),
        ),
      );
    }
    
    Widget _buildSignInButton(WidgetRef ref) {
      return ElevatedButton.icon(
        onPressed: () => ref.read(authNotifierProvider.notifier).signIn(),
        icon: SvgPicture.asset('assets/google_icon.svg'),
        label: const Text('Continue with Google'),
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(250, 50),
          backgroundColor: Colors.white,
          foregroundColor: Colors.black87,
        ),
      );
    }
  }
  ```

  ### 2.6 Secure Token Storage

  **Token Storage Implementation:**

  ```dart
  class SecureTokenStorage {
    static const _accessTokenKey = 'access_token';
    static const _refreshTokenKey = 'refresh_token';
    static const _userDataKey = 'user_data';
    
    final FlutterSecureStorage _storage = const FlutterSecureStorage(
      aOptions: AndroidOptions(
        encryptedSharedPreferences: true,
      ),
      iOptions: IOSOptions(
        accessibility: IOSAccessibility.first_unlock_this_device,
      ),
    );
    
    Future<void> storeTokens({
      required String accessToken,
      required String refreshToken,
      required Map<String, dynamic> userData,
    }) async {
      await Future.wait([
        _storage.write(key: _accessTokenKey, value: accessToken),
        _storage.write(key: _refreshTokenKey, value: refreshToken),
        _storage.write(key: _userDataKey, value: jsonEncode(userData)),
      ]);
    }
    
    Future<AuthTokens?> getTokens() async {
      final values = await Future.wait([
        _storage.read(key: _accessTokenKey),
        _storage.read(key: _refreshTokenKey),
        _storage.read(key: _userDataKey),
      ]);
      
      if (values.every((v) => v != null)) {
        return AuthTokens(
          accessToken: values[0]!,
          refreshToken: values[1]!,
          userData: jsonDecode(values[2]!),
        );
      }
      return null;
    }
    
    Future<void> clearTokens() async {
      await _storage.deleteAll();
    }
  }
  ```

  ### 2.7 Navigation & Route Protection

  **Authentication-Aware Routing:**

  ```dart
  final appRouter = GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      final authState = ProviderScope.containerOf(context)
          .read(authNotifierProvider);
      
      final isAuthenticated = authState.when(
        authenticated: (_) => true,
        unauthenticated: () => false,
        loading: () => false,
        error: (_) => false,
      );
      
      // Handle authentication routing
      if (!isAuthenticated && !state.location.startsWith('/auth')) {
        return '/auth/login';
      }
      
      if (isAuthenticated && state.location.startsWith('/auth')) {
        return '/home';
      }
      
      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/auth/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const HomeScreen(),
      ),
      // ... other protected routes
    ],
  );
  ```

  ### 2.8 Error Handling & User Experience

  **Authentication Error States:**

  - **Network Connectivity Issues**: Show retry button with offline indicator
  - **Google Sign-In Cancelled**: Return to login screen with helpful message
  - **Token Validation Failures**: Auto-retry with exponential backoff
  - **Backend Unavailable**: Show maintenance message with estimated recovery time
  - **Account Restrictions**: Clear error messages with support contact information

  **Loading States:**
  - Smooth animations during sign-in process
  - Progress indicators for token validation
  - Skeleton screens while loading user data
  - Graceful transitions between authentication states

  ### 2.9 Security Considerations

  **Frontend Security:**
  - No sensitive data stored in plain text
  - Secure storage for all authentication tokens
  - Automatic token cleanup on app uninstall
  - Protection against token extraction on rooted/jailbroken devices

  **Backend Security:**
  - Google ID token verification on every request
  - Rate limiting on authentication endpoints
  - Secure JWT token generation with short expiry times
  - Comprehensive audit logging for authentication events

  **Privacy Compliance:**
  - Clear privacy policy regarding Google data usage
  - Minimal data collection (only email and basic profile)
  - User consent management for data processing
  - GDPR compliance for EU users

  III. Enhanced User Flow with Authentication

  Here is the updated journey a user will take through ScribeFlow, including authentication:

  Start -> Authenticate (Google/Medium) -> Create New Story -> Write Content
      |
      -> Select Text -> Click "Enhance with AI"
      |
      -> Review AI Suggestions (Diff View) -> [Accept] or [Reject] or [Refine with Instructions]
      |
      -> Select Code Snippet -> Click "Run" -> View Output in Console -> Modify Code & Rerun
      |
      -> Finalize Story -> Click "Publish" -> Configure (Tags, Status) -> Publish to Medium/Blogger -> End

  IV. Technology Stack & Architecture

For your specific requirements—building ScribeFlow for iOS, Android, Windows, macOS, and Linux—the best language and framework choice is Flutter.

  Here's a detailed breakdown of why Flutter is the ideal solution and how the architecture would look.

  VIII. Flutter Implementation Strategy

  Why Flutter is the Best Choice for ScribeFlow

  Flutter is a UI toolkit developed by Google for building beautiful, natively compiled applications for mobile, web, and desktop from a single codebase.

   1. **True Single Codebase**: This is the most significant advantage. You will write the ScribeFlow application once in the Dart language, and Flutter will compile it to a native application for every platform. This saves immense development time
      and ensures feature parity everywhere.

   2. **Excellent Performance**: Flutter doesn't use webviews or native OEM widgets. It compiles to native ARM or x86 machine code and uses its own high-performance rendering engine (Skia) to draw every pixel on the screen. This results in a smooth,
      60/120 FPS experience, which is crucial for a responsive text editor.

   3. **Consistent UI Across All Platforms**: Because Flutter controls the entire UI, your ScribeFlow application will look and feel exactly the same on an iPhone, an Android tablet, a Windows laptop, and a MacBook. This is a huge win for branding and
      user experience, as you can deliver a polished, custom design without platform-specific tweaks.

   4. **Rich Ecosystem and Google's Backing**: Flutter is a top-tier project at Google with a massive and active community. The package repository (pub.dev) has thousands of libraries, including everything you would need for
      ScribeFlow:
       * Powerful rich text editors.
       * Markdown support and syntax highlighting.
       * OAuth clients for logging into Google/Medium.
       * HTTP clients for communicating with your backend.

   5. **Developer-Friendly**: Features like Hot Reload allow you to see UI changes in real-time, making development incredibly fast and iterative. The Dart language is modern, type-safe, and relatively easy to learn for anyone familiar with
      TypeScript, Java, or C#.

  ### 8.1 Flutter Architecture Implementation

  The overall architecture remains similar, but the "Frontend" is now a Flutter application instead of a web app.

  **Flutter Application Structure (in Dart)**

  This is the single application you will build for all platforms.

   * **Core UI Framework**: Flutter SDK with Material Design 3 components.
   * **Rich Text Editor**: A package like `flutter_quill` is perfect. It's a powerful, extensible, and highly performant rich text editor for Flutter that can be customized to include your "Run" button on code blocks.
   * **API Communication**: The built-in `dio` package to make secure API calls to your Python backend for AI enhancement and code execution.
   * **Authentication**: Use packages like `google_sign_in` and a generic `oauth2_client` to handle authentication with Google and Medium. Flutter's deep platform integration makes this seamless.
   * **State Management**: A simple but powerful state management solution like `Riverpod` to manage the application's state (e.g., story content, user login status).
   * **Publishing**: The app will make an API call to your backend, which will then handle the actual publishing to Medium/Blogger.

  ### 8.2 Backend: The Python Server (Enhanced)

  Your backend logic remains exactly the same. It doesn't care if the request comes from a web browser or a Flutter app.

   * **Framework**: FastAPI (Python) with enhanced performance and security features.
   * **Enhanced Responsibilities**:
       * `/enhance` endpoint: Receives text from the Flutter app, sends it to the Gemini API, and returns the suggestion with structured diff data.
       * `/run_code` endpoint: Receives a code snippet, executes it in a secure Docker container with resource limits, and returns the output with execution metrics.
       * `/publish` endpoint: Receives the final story content and credentials, then uses the Medium/Blogger APIs to publish the story with full metadata support.
       * `/collaborate` endpoint: Real-time collaboration features using WebSocket connections.
       * **User Database**: Manages user accounts, securely stores API tokens, and handles content versioning.

  ### 8.3 Why Not Other Cross-Platform Options?

   * **React Native**: Primarily focused on mobile. While desktop support exists (via community efforts), it's not as mature or integrated as Flutter's, making it harder to maintain a single, consistent app.
   * **Kotlin Multiplatform (KMP)**: An excellent choice for sharing business logic, but its UI framework (Compose Multiplatform) is still less mature on iOS and desktop compared to Flutter. For a UI-heavy application like ScribeFlow, Flutter's
     stability across all platforms is a major advantage.
   * **Electron**: While cross-platform, it results in large application sizes and poor performance compared to native compilation.
   * **Progressive Web App (PWA)**: Limited native integration and offline capabilities compared to true native applications.

  ### 8.4 Flutter-Specific Implementation Details

  **Project Structure**:
  ```
  lib/
  ├── main.dart
  ├── app/
  │   ├── app.dart
  │   ├── router/
  │   └── theme/
  ├── features/
  │   ├── auth/
  │   ├── editor/
  │   ├── ai_assistant/
  │   ├── code_runner/
  │   └── publisher/
  ├── shared/
  │   ├── widgets/
  │   ├── services/
  │   ├── models/
  │   └── utils/
  └── core/
      ├── network/
      ├── storage/
      └── constants/
  ```

  **Key Dependencies (pubspec.yaml)**:
  ```yaml
  dependencies:
    flutter: ^3.16.0
    flutter_quill: ^8.0.0
    riverpod: ^2.4.0
    dio: ^5.3.0
    google_sign_in: ^6.1.0
    flutter_secure_storage: ^9.0.0
    go_router: ^12.0.0
    freezed: ^2.4.0
    json_annotation: ^4.8.0
    
  dev_dependencies:
    build_runner: ^2.4.0
    freezed: ^2.4.0
    json_serializable: ^6.7.0
    flutter_lints: ^3.0.0
  ```

  IX. Conclusion & Next Steps

  ### 9.1 Strategic Advantages

  For a project as ambitious as ScribeFlow that needs to run everywhere, Flutter is the strategic choice. It provides the best balance of performance, developer experience, and true cross-platform capability, allowing you to focus on building great
   features, not on managing multiple different codebases.

  ### 9.2 Immediate Next Steps

  **Phase 1: Authentication Setup (Week 1-2)**
  1. **Google Cloud Console Setup**:
     - Create Google Cloud Project
     - Enable Google Sign-In API
     - Configure OAuth 2.0 credentials for all platforms (iOS, Android, Web, Desktop)
     - Set up allowed domains and redirect URIs

  2. **Flutter Project Initialization**:
     - Create Flutter project with proper structure
     - Add authentication dependencies to `pubspec.yaml`:
       ```yaml
       dependencies:
         google_sign_in: ^6.1.5
         flutter_secure_storage: ^9.0.0
         riverpod: ^2.4.7
         go_router: ^12.1.1
         dio: ^5.3.2
         json_annotation: ^4.8.1
       ```

  3. **Backend Authentication Foundation**:
     - Set up FastAPI server with authentication endpoints
     - Configure PostgreSQL database with user tables
     - Implement Google ID token verification
     - Create JWT token generation and validation

  **Phase 2: Core App Development (Week 3-4)**
  4. **Authentication Implementation**:
     - Build login screen with Google Sign-In button
     - Implement authentication state management
     - Create secure token storage system
     - Set up route protection and navigation

  5. **Basic Editor Setup**:
     - Integrate flutter_quill rich text editor
     - Create basic UI layout (three-panel design)
     - Implement local content saving
     - Add markdown support

  **Phase 3: MVP Features (Week 5-8)**
  6. **AI Integration**: 
     - Implement multi-provider AI framework
     - Configure Google Gemini as primary provider
     - Set up OpenAI and Claude as fallback options
     - Create AI provider selection interface
  7. **Publishing**: Add basic Medium API publishing functionality
  8. **Testing & Polish**: Comprehensive testing and UI/UX improvements

  ### 9.3 Success Metrics

  **Technical Metrics**:
   * Cross-platform performance: 60 FPS on all supported platforms
   * App size: Under 50MB for mobile, under 100MB for desktop
   * Cold start time: Under 3 seconds on all platforms
   * API response time: Under 500ms for enhancement requests

  **User Experience Metrics**:
   * User retention: 70%+ monthly active users after 6 months
   * Publishing success rate: 95%+ successful publications
   * User satisfaction: 4.5+ star rating across all app stores
   * Content quality: Measurable improvement in published content engagement

  This comprehensive design provides a solid foundation for building ScribeFlow as a world-class, cross-platform writing assistant that truly serves the needs of technical storytellers.

  ---

  ## Summary of Tools & Technologies

  ### Frontend (Flutter)
  - **Flutter SDK 3.16+** - Cross-platform UI framework
  - **Dart 3.0+** - Programming language
  - **flutter_quill** - Rich text editor
  - **Riverpod** - State management
  - **dio** - HTTP client
  - **google_sign_in** - Google OAuth authentication
  - **flutter_secure_storage** - Secure token storage
  - **go_router** - Navigation with route protection
  - **json_annotation** - JSON serialization
  - **flutter_svg** - SVG icon support

  ### Backend (Python)
  - **FastAPI** - Web framework
  - **Python 3.11+** - Programming language
  - **PostgreSQL 15+** - Database
  - **SQLAlchemy 2.0** - ORM
  - **Docker** - Containerization
  - **google-generativeai** - Google Gemini API integration
  - **openai** - OpenAI GPT models integration
  - **anthropic** - Claude models integration
  - **cohere** - Cohere models integration
  - **langchain** - Multi-provider AI framework
  - **python-jose[cryptography]** - JWT token handling
  - **google-auth** - Google ID token verification
  - **passlib[bcrypt]** - Password hashing
  - **python-multipart** - Form data handling
  - **redis** - Caching and usage tracking

  ### Infrastructure
  - **Google Cloud Platform** - Cloud hosting
  - **Docker & Kubernetes** - Container orchestration
  - **GitHub Actions** - CI/CD
  - **Nginx** - Load balancer
  - **Redis** - Caching

  ### External APIs
  - **Google Gemini API** - AI text enhancement (Primary)
  - **OpenAI API** - GPT models for AI assistance (Fallback)
  - **Anthropic Claude API** - Advanced AI reasoning (Fallback)
  - **Cohere API** - Text generation and analysis
  - **Medium API** - Publishing platform
  - **Blogger API** - Google blogging platform
  - **OAuth 2.0** - Authentication providers

  X. Database Schema & Data Models

  ### 10.1 PostgreSQL Database Schema

  **Users Table:**
  ```sql
  CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
  );
  ```

  **Stories Table:**
  ```sql
  CREATE TABLE stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content JSONB NOT NULL, -- Quill Delta format
    markdown_content TEXT, -- Cached markdown version
    status VARCHAR(50) DEFAULT 'draft', -- draft, published, archived
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    word_count INTEGER DEFAULT 0,
    read_time INTEGER DEFAULT 0, -- in minutes
    version INTEGER DEFAULT 1
  );
  ```

  **Story Versions Table (for version history):**
  ```sql
  CREATE TABLE story_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    version_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_summary TEXT
  );
  ```

  **Published Articles Table:**
  ```sql
  CREATE TABLE published_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL, -- medium, blogger, dev.to
    external_id VARCHAR(255), -- Platform-specific article ID
    external_url TEXT,
    published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'published' -- published, failed, pending
  );
  ```

  **AI Enhancement History:**
  ```sql
  CREATE TABLE ai_enhancements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    story_id UUID REFERENCES stories(id) ON DELETE SET NULL,
    original_text TEXT NOT NULL,
    enhanced_text TEXT NOT NULL,
    prompt_used TEXT,
    model_used VARCHAR(100) DEFAULT 'gemini-pro',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  ```

  ### 10.2 Flutter Data Models

  **User Model:**
  ```dart
  @freezed
  class User with _$User {
    const factory User({
      required String id,
      required String email,
      required String name,
      required String googleId,
      String? avatarUrl,
      required DateTime createdAt,
      DateTime? lastLogin,
      @Default(true) bool isActive,
    }) = _User;
    
    factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
  }
  ```

  **Story Model:**
  ```dart
  @freezed
  class Story with _$Story {
    const factory Story({
      required String id,
      required String userId,
      required String title,
      required Map<String, dynamic> content, // Quill Delta
      String? markdownContent,
      @Default(StoryStatus.draft) StoryStatus status,
      @Default([]) List<String> tags,
      required DateTime createdAt,
      required DateTime updatedAt,
      DateTime? publishedAt,
      @Default(0) int wordCount,
      @Default(0) int readTime,
      @Default(1) int version,
    }) = _Story;
    
    factory Story.fromJson(Map<String, dynamic> json) => _$StoryFromJson(json);
  }
  
  enum StoryStatus { draft, published, archived }
  ```

  XI. Offline Capabilities & Data Synchronization

  ### 11.1 Offline-First Architecture

  **Local Database (SQLite):**
  ```dart
  class LocalDatabase {
    static final LocalDatabase _instance = LocalDatabase._internal();
    factory LocalDatabase() => _instance;
    LocalDatabase._internal();
    
    Database? _database;
    
    Future<Database> get database async {
      _database ??= await _initDatabase();
      return _database!;
    }
    
    Future<Database> _initDatabase() async {
      final path = await getDatabasesPath();
      return await openDatabase(
        join(path, 'scribeflow.db'),
        version: 1,
        onCreate: _createTables,
      );
    }
  }
  ```

  **Sync Strategy:**
  - Stories auto-saved locally every 30 seconds
  - Background sync when network available
  - Conflict resolution with server timestamps
  - Optimistic UI updates with rollback capability

  ### 11.2 Conflict Resolution

  **Three-Way Merge Strategy:**
  1. **Last Writer Wins**: For simple text edits
  2. **Operational Transform**: For collaborative editing
  3. **User Choice**: For major conflicts with diff view

  XII. Testing Strategy & Quality Assurance

  ### 12.1 Flutter Testing Pyramid

  **Unit Tests (70%):**
  ```dart
  // Business logic, models, services
  group('AuthService', () {
    test('should authenticate user with valid Google token', () async {
      // Arrange
      final mockGoogleSignIn = MockGoogleSignIn();
      final authService = AuthService(mockGoogleSignIn);
      
      // Act
      final result = await authService.signInWithGoogle();
      
      // Assert
      expect(result, isA<User>());
    });
  }
  ```

  **Widget Tests (20%):**
  ```dart
  // UI components and interactions
  testWidgets('LoginScreen should show Google Sign-In button', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(home: LoginScreen()),
      ),
    );
    
    expect(find.text('Continue with Google'), findsOneWidget);
  });
  ```

  **Integration Tests (10%):**
  ```dart
  // End-to-end user flows
  testWidgets('Complete authentication flow', (tester) async {
    // Test full login -> main app flow
  });
  ```

  ### 12.2 Backend Testing

  **FastAPI Testing:**
  ```python
  @pytest.mark.asyncio
  async def test_google_auth_endpoint():
      async with AsyncClient(app=app, base_url="http://test") as ac:
          response = await ac.post("/auth/google", json={
              "id_token": "valid_test_token"
          })
      assert response.status_code == 200
      assert "access_token" in response.json()
  ```

  ### 12.3 Performance Testing

  **Key Metrics to Monitor:**
  - App startup time: < 3 seconds
  - Text editor responsiveness: < 16ms frame time
  - API response times: < 500ms
  - Memory usage: < 200MB on mobile
  - Battery usage: Minimal background processing

  XIII. Deployment & DevOps Pipeline

  ### 13.1 CI/CD Pipeline (GitHub Actions)

  **Flutter Build Pipeline:**
  ```yaml
  name: Build and Test
  on: [push, pull_request]
  
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - uses: subosito/flutter-action@v2
        - run: flutter pub get
        - run: flutter test
        - run: flutter analyze
        
    build:
      needs: test
      strategy:
        matrix:
          platform: [android, ios, windows, macos, linux]
      runs-on: ${{ matrix.platform == 'ios' || matrix.platform == 'macos' && 'macos-latest' || 'ubuntu-latest' }}
      steps:
        - name: Build ${{ matrix.platform }}
          run: flutter build ${{ matrix.platform }}
  ```

  ### 13.2 Backend Deployment

  **Docker Configuration:**
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  EXPOSE 8000
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

  **Google Cloud Run Deployment:**
  ```yaml
  apiVersion: serving.knative.dev/v1
  kind: Service
  metadata:
    name: scribeflow-api
  spec:
    template:
      metadata:
        annotations:
          autoscaling.knative.dev/maxScale: "100"
      spec:
        containers:
        - image: gcr.io/PROJECT_ID/scribeflow-api
          env:
          - name: DATABASE_URL
            valueFrom:
              secretKeyRef:
                name: db-credentials
                key: url
  ```

  XIV. Security & Compliance Framework

  ### 14.1 Security Checklist

  **Frontend Security:**
  - ✅ No hardcoded secrets in source code
  - ✅ Secure storage for sensitive data
  - ✅ Certificate pinning for API calls
  - ✅ Obfuscation for release builds
  - ✅ Biometric authentication support

  **Backend Security:**
  - ✅ Input validation and sanitization
  - ✅ SQL injection prevention
  - ✅ Rate limiting and DDoS protection
  - ✅ CORS configuration
  - ✅ Security headers (HTTPS, CSP, etc.)

  ### 14.2 Privacy Compliance

  **GDPR Requirements:**
  - Data minimization: Only collect necessary user data
  - Right to access: API endpoint for user data export
  - Right to deletion: Complete data removal capability
  - Consent management: Clear privacy policy and consent flows
  - Data portability: Export in standard formats

  ### 14.3 Monitoring & Observability

  **Application Monitoring:**
  ```dart
  // Firebase Crashlytics integration
  void main() async {
    await Firebase.initializeApp();
    FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterError;
    
    runApp(MyApp());
  }
  ```

  **Backend Monitoring:**
  ```python
  # Prometheus metrics
  from prometheus_client import Counter, Histogram, generate_latest
  
  REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
  REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
  ```

  XV. Cost Estimation & Business Model

  ### 15.1 Infrastructure Costs (Monthly)

  **Development Phase:**
  - Google Cloud Run: $20-50
  - Cloud SQL (PostgreSQL): $30-100
  - Google Gemini API: $50-200 (based on usage)
  - **Total: $100-350/month**

  **Production Phase (1000 users):**
  - Google Cloud Run: $200-500
  - Cloud SQL: $200-500
  - Google Gemini API: $500-2000
  - Cloud Storage: $20-50
  - **Total: $920-3050/month**

  ### 15.2 Monetization Strategy

  **Freemium Model:**
  - Free tier: 10 AI enhancements/month, basic publishing
  - Pro tier ($9.99/month): Unlimited AI, advanced analytics
  - Team tier ($29.99/month): Collaboration features, priority support

  XVI. AI Integration Framework (Multi-Provider)

  ### 16.1 AI Provider Abstraction Layer

  ScribeFlow implements a flexible AI integration system that supports multiple language models and providers, allowing you to configure and switch between different AI services based on requirements.

  **Supported AI Providers:**
  - **Google Gemini**: Gemini Pro, Gemini Ultra models
  - **OpenAI**: GPT-4, GPT-4-turbo, GPT-3.5-turbo
  - **Anthropic**: Claude-3 Opus, Claude-3 Sonnet, Claude-2
  - **Cohere**: Command models for text generation
  - **Hugging Face**: Open-source models via API
  - **Custom Models**: Support for self-hosted models

  ### 16.2 AI Service Architecture

  **Python Backend - AI Provider Interface:**

  ```python
  from abc import ABC, abstractmethod
  from typing import Dict, List, Optional
  from dataclasses import dataclass
  
  @dataclass
  class AIRequest:
      prompt: str
      context: Optional[str] = None
      max_tokens: Optional[int] = 1000
      temperature: Optional[float] = 0.7
      model_parameters: Optional[Dict[str, Any]] = None
  
  @dataclass
  class AIResponse:
      content: str
      model_used: str
      tokens_used: int
      cost_estimate: float
      processing_time: float
      confidence_score: Optional[float] = None
  
  class AIProvider(ABC):
      """Abstract base class for all AI providers"""
      
      @abstractmethod
      async def generate_text(self, request: AIRequest) -> AIResponse:
          """Generate enhanced text based on the input request"""
          pass
      
      @abstractmethod
      async def health_check(self) -> bool:
          """Check if the provider is available"""
          pass
      
      @abstractmethod
      def get_supported_models(self) -> List[str]:
          """Return list of supported models for this provider"""
          pass
  ```

  **Google Gemini Provider:**

  ```python
  import google.generativeai as genai
  from .base import AIProvider, AIRequest, AIResponse
  
  class GeminiProvider(AIProvider):
      def __init__(self, api_key: str, model: str = "gemini-pro"):
          genai.configure(api_key=api_key)
          self.model = genai.GenerativeModel(model)
          self.model_name = model
      
      async def generate_text(self, request: AIRequest) -> AIResponse:
          start_time = time.time()
          
          try:
              response = await self.model.generate_content_async(
                  contents=request.prompt,
                  generation_config=genai.types.GenerationConfig(
                      max_output_tokens=request.max_tokens,
                      temperature=request.temperature,
                  )
              )
              
              processing_time = time.time() - start_time
              
              return AIResponse(
                  content=response.text,
                  model_used=self.model_name,
                  tokens_used=response.usage_metadata.total_token_count,
                  cost_estimate=self._calculate_cost(response.usage_metadata),
                  processing_time=processing_time,
                  confidence_score=response.candidates[0].safety_ratings[0].probability
              )
              
          except Exception as e:
              raise AIProviderError(f"Gemini API error: {str(e)}")
      
      def get_supported_models(self) -> List[str]:
          return ["gemini-pro", "gemini-pro-vision", "gemini-ultra"]
  ```

  **OpenAI Provider:**

  ```python
  import openai
  from .base import AIProvider, AIRequest, AIResponse
  
  class OpenAIProvider(AIProvider):
      def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
          self.client = openai.AsyncOpenAI(api_key=api_key)
          self.model_name = model
      
      async def generate_text(self, request: AIRequest) -> AIResponse:
          start_time = time.time()
          
          try:
              response = await self.client.chat.completions.create(
                  model=self.model_name,
                  messages=[
                      {"role": "system", "content": "You are a helpful writing assistant."},
                      {"role": "user", "content": request.prompt}
                  ],
                  max_tokens=request.max_tokens,
                  temperature=request.temperature,
              )
              
              processing_time = time.time() - start_time
              
              return AIResponse(
                  content=response.choices[0].message.content,
                  model_used=self.model_name,
                  tokens_used=response.usage.total_tokens,
                  cost_estimate=self._calculate_cost(response.usage),
                  processing_time=processing_time
              )
              
          except Exception as e:
              raise AIProviderError(f"OpenAI API error: {str(e)}")
      
      def get_supported_models(self) -> List[str]:
          return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
  ```

  **Claude Provider:**

  ```python
  import anthropic
  from .base import AIProvider, AIRequest, AIResponse
  
  class ClaudeProvider(AIProvider):
      def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
          self.client = anthropic.AsyncAnthropic(api_key=api_key)
          self.model_name = model
      
      async def generate_text(self, request: AIRequest) -> AIResponse:
          start_time = time.time()
          
          try:
              response = await self.client.messages.create(
                  model=self.model_name,
                  max_tokens=request.max_tokens,
                  temperature=request.temperature,
                  messages=[
                      {"role": "user", "content": request.prompt}
                  ]
              )
              
              processing_time = time.time() - start_time
              
              return AIResponse(
                  content=response.content[0].text,
                  model_used=self.model_name,
                  tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                  cost_estimate=self._calculate_cost(response.usage),
                  processing_time=processing_time
              )
              
          except Exception as e:
              raise AIProviderError(f"Claude API error: {str(e)}")
      
      def get_supported_models(self) -> List[str]:
          return ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-2.1"]
  ```

  ### 16.3 AI Manager & Fallback System

  **AI Manager with Provider Fallback:**

  ```python
  from typing import Dict, List, Optional
  from enum import Enum
  
  class AIProviderType(Enum):
      GEMINI = "gemini"
      OPENAI = "openai"
      CLAUDE = "claude"
      COHERE = "cohere"
      HUGGINGFACE = "huggingface"
  
  class AIManager:
      def __init__(self, providers_config: Dict[str, Dict]):
          self.providers: Dict[AIProviderType, AIProvider] = {}
          self.primary_provider = None
          self.fallback_chain = []
          self._initialize_providers(providers_config)
      
      def _initialize_providers(self, config: Dict[str, Dict]):
          """Initialize all configured AI providers"""
          for provider_type, provider_config in config.items():
              if provider_config.get('enabled', False):
                  provider = self._create_provider(provider_type, provider_config)
                  self.providers[AIProviderType(provider_type)] = provider
                  
                  if provider_config.get('primary', False):
                      self.primary_provider = AIProviderType(provider_type)
                  
                  if provider_config.get('fallback_order'):
                      self.fallback_chain = provider_config['fallback_order']
      
      async def enhance_text(self, 
                            prompt: str, 
                            context: Optional[str] = None,
                            preferred_provider: Optional[AIProviderType] = None) -> AIResponse:
          """
          Enhance text using AI with automatic fallback
          """
          request = AIRequest(
              prompt=prompt,
              context=context,
              max_tokens: 1000,
              temperature: 0.7
          )
          
          # Determine provider priority
          providers_to_try = []
          if preferred_provider and preferred_provider in self.providers:
              providers_to_try.append(preferred_provider)
          
          if self.primary_provider:
              providers_to_try.append(self.primary_provider)
          
          # Add fallback providers
          for provider_type in self.fallback_chain:
              if AIProviderType(provider_type) in self.providers:
                  providers_to_try.append(AIProviderType(provider_type))
          
          # Try providers in order
          last_error = None
          for provider_type in providers_to_try:
              try:
                  provider = self.providers[provider_type]
                  if await provider.health_check():
                      response = await provider.generate_text(request)
                      
                      # Log successful usage
                      await self._log_usage(provider_type, request, response)
                      return response
                      
              except Exception as e:
                  last_error = e
                  # Log failed attempt
                  await self._log_error(provider_type, str(e))
                  continue
          
          raise AIProviderError(f"All AI providers failed. Last error: {last_error}")
      
      async def get_available_models(self) -> Dict[str, List[str]]:
          """Get all available models from all providers"""
          models = {}
          for provider_type, provider in self.providers.items():
              if await provider.health_check():
                  models[provider_type.value] = provider.get_supported_models()
          return models
  ```

  ### 16.4 Configuration System

  **Environment-Based Configuration:**

  ```python
  # config/ai_providers.yaml
  ai_providers:
    gemini:
      enabled: true
      primary: true
      api_key: ${GEMINI_API_KEY}
      model: "gemini-pro"
      rate_limit: 60  # requests per minute
      cost_per_1k_tokens: 0.001
      
    openai:
      enabled: true
      api_key: ${OPENAI_API_KEY}
      model: "gpt-4-turbo"
      rate_limit: 500
      cost_per_1k_tokens: 0.01
      
    claude:
      enabled: false
      api_key: ${ANTHROPIC_API_KEY}
      model: "claude-3-sonnet-20240229"
      rate_limit: 100
      cost_per_1k_tokens: 0.008
      
    fallback_order: ["openai", "claude"]
    
    # Feature-specific model selection
    features:
      text_enhancement:
        preferred_provider: "gemini"
        fallback: ["openai", "claude"]
      code_explanation:
        preferred_provider: "openai"
        fallback: ["claude", "gemini"]
      grammar_check:
        preferred_provider: "claude"
        fallback: ["openai"]
  ```

  **FastAPI Configuration Endpoint:**

  ```python
  from fastapi import APIRouter, Depends
  from typing import Dict, Any
  
  router = APIRouter(prefix="/ai", tags=["AI Configuration"])
  
  @router.get("/providers")
  async def get_available_providers() -> Dict[str, Any]:
      """Get list of available AI providers and their models"""
      ai_manager = get_ai_manager()
      providers = {}
      
      for provider_type, provider in ai_manager.providers.items():
          if await provider.health_check():
              providers[provider_type.value] = {
                  "models": provider.get_supported_models(),
                  "status": "available"
              }
          else:
              providers[provider_type.value] = {
                  "models": [],
                  "status": "unavailable"
              }
      
      return {
          "providers": providers,
          "primary": ai_manager.primary_provider.value if ai_manager.primary_provider else None,
          "fallback_chain": ai_manager.fallback_chain
      }
  
  @router.post("/enhance")
  async def enhance_text(
      request: TextEnhancementRequest,
      ai_manager: AIManager = Depends(get_ai_manager)
  ) -> AIResponse:
      """Enhanced text generation with provider selection"""
      return await ai_manager.enhance_text(
          prompt=request.prompt,
          context=request.context,
          preferred_provider=request.preferred_provider
      )
  ```

  ### 16.5 Flutter AI Integration

  **Flutter AI Service:**

  ```dart
  // AI Provider selection in Flutter
  enum AIProvider { gemini, openai, claude, auto }
  
  @freezed
  class AIEnhancementRequest with _$AIEnhancementRequest {
    const factory AIEnhancementRequest({
      required String text,
      String? instructions,
      @Default(AIProvider.auto) AIProvider preferredProvider,
      @Default(1000) int maxTokens,
      @Default(0.7) double temperature,
    }) = _AIEnhancementRequest;
    
    factory AIEnhancementRequest.fromJson(Map<String, dynamic> json) =>
        _$AIEnhancementRequestFromJson(json);
  }
  
  class AIService {
    final Dio _dio;
    final SecureStorage _storage;
    
    AIService(this._dio, this._storage);
    
    Future<AIEnhancementResponse> enhanceText(AIEnhancementRequest request) async {
      try {
        final response = await _dio.post('/ai/enhance', data: {
          'prompt': _buildPrompt(request.text, request.instructions),
          'context': request.text,
          'preferred_provider': request.preferredProvider.name,
          'max_tokens': request.maxTokens,
          'temperature': request.temperature,
        });
        
        return AIEnhancementResponse.fromJson(response.data);
      } catch (e) {
        throw AIServiceException('Failed to enhance text: $e');
      }
    }
    
    Future<List<AIProvider>> getAvailableProviders() async {
      try {
        final response = await _dio.get('/ai/providers');
        final providers = response.data['providers'] as Map<String, dynamic>;
        
        return providers.entries
            .where((entry) => entry.value['status'] == 'available')
            .map((entry) => AIProvider.values.firstWhere(
                (p) => p.name == entry.key,
                orElse: () => AIProvider.auto))
            .toList();
      } catch (e) {
        return [AIProvider.auto]; // Fallback to auto selection
      }
    }
  }
  ```

  ### 16.6 Cost Management & Analytics

  **Usage Tracking:**

  ```python
  class AIUsageTracker:
      def __init__(self, redis_client):
          self.redis = redis_client
      
      async def track_usage(self, user_id: str, provider: str, 
                           tokens: int, cost: float):
          """Track AI usage for billing and analytics"""
          today = datetime.now().strftime('%Y-%m-%d')
          
          # Daily usage tracking
          await self.redis.hincrby(f"usage:{user_id}:{today}", "tokens", tokens)
          await self.redis.hincrbyfloat(f"usage:{user_id}:{today}", "cost", cost)
          await self.redis.hincrby(f"usage:{user_id}:{today}", f"requests_{provider}", 1)
          
          # Monthly limits check
          monthly_usage = await self.get_monthly_usage(user_id)
          user_tier = await self.get_user_tier(user_id)
          
          if monthly_usage['tokens'] > TIER_LIMITS[user_tier]['tokens']:
              raise UsageLimitExceeded(f"Monthly token limit exceeded")
      
      async def get_usage_analytics(self, user_id: str) -> Dict:
          """Get detailed usage analytics for user"""
          # Implementation for usage analytics
          pass
  ```

  This comprehensive AI integration framework provides:

  ✅ **Multi-Provider Support**: Easy switching between AI providers
  ✅ **Automatic Fallback**: Reliability through provider redundancy  
  ✅ **Cost Management**: Usage tracking and limits
  ✅ **Performance Monitoring**: Response times and success rates
  ✅ **Flexible Configuration**: Easy provider and model changes
  ✅ **Feature-Specific Models**: Different models for different tasks

  XVII. UX/UI Design System & User Experience

  ### 17.1 Design Philosophy & Principles

  ScribeFlow's interface is designed around the core principle of **"Invisible Technology"** - the interface should fade into the background, allowing writers to focus entirely on their craft. The AI assistance should feel magical yet predictable, and the publishing workflow should be effortless.

  **Core UX Principles:**

  1. **Clarity Over Cleverness**: Every interface element has a clear, obvious purpose
  2. **Progressive Disclosure**: Advanced features are hidden until needed
  3. **Contextual Assistance**: AI suggestions appear precisely when and where needed
  4. **Seamless Transitions**: Smooth animations that guide attention and maintain context
  5. **Cross-Platform Consistency**: Identical experience across all devices and platforms
  6. **Accessibility First**: Designed for users with diverse abilities and assistive technologies

  ### 17.2 Visual Design Language

  **Color Palette:**
  ```
  Primary Colors:
  - ScribeFlow Blue: #2563EB (Primary brand color)
  - Deep Navy: #1E3A8A (Dark accent)
  - Soft Blue: #DBEAFE (Light accent)
  
  Content Colors:
  - Rich Black: #1F2937 (Primary text)
  - Medium Gray: #6B7280 (Secondary text)
  - Light Gray: #F3F4F6 (Background elements)
  - Pure White: #FFFFFF (Main background)
  
  Semantic Colors:
  - Success Green: #10B981
  - Warning Amber: #F59E0B
  - Error Red: #EF4444
  - AI Accent: #8B5CF6 (Purple for AI features)
  ```

  **Typography System:**
  ```
  Primary Font: Inter (System font fallback)
  - Display: 32px, 600 weight (Headlines)
  - H1: 28px, 600 weight (Page titles)
  - H2: 24px, 600 weight (Section titles)
  - H3: 20px, 600 weight (Subsections)
  - Body Large: 16px, 400 weight (Primary content)
  - Body: 14px, 400 weight (UI text)
  - Caption: 12px, 400 weight (Helper text)
  
  Editor Font: JetBrains Mono (Monospace for code)
  - Code blocks and syntax highlighting
  - Line numbers and editor UI
  ```

  **Spacing & Layout System:**
  ```
  Base unit: 8px
  - XS: 4px (0.5 unit)
  - SM: 8px (1 unit)
  - MD: 16px (2 units)
  - LG: 24px (3 units)
  - XL: 32px (4 units)
  - 2XL: 48px (6 units)
  - 3XL: 64px (8 units)
  
  Container Max-widths:
  - Mobile: 100% (with 16px padding)
  - Tablet: 768px
  - Desktop: 1200px
  - Wide: 1400px
  ```

  ### 17.3 Application Layout & Navigation

  **Three-Panel Desktop Layout:**
  ```
  +------------------+-------------------------+------------------+
  |    Sidebar       |     Main Editor         |   Assistant      |
  |    (280px)       |     (Flexible)          |   Panel (320px)  |
  |                  |                         |                  |
  | • Stories List   | • Rich Text Editor      | • AI Suggestions |
  | • Recent Files   | • Markdown Preview      | • Code Output    |
  | • Tags           | • Writing Statistics    | • Publishing     |
  | • Settings       | • Version History       | • Collaboration  |
  |                  |                         |                  |
  +------------------+-------------------------+------------------+
  ```

  **Mobile Layout (Responsive):**
  ```
  Full-width editor with collapsible panels:
  - Bottom sheet for AI assistance
  - Slide-in drawer for navigation
  - Floating action button for quick actions
  - Top app bar with essential controls
  ```

  ### 17.4 Detailed Wireframes & User Flows

  **Authentication Flow Wireframes:**

  ```
  Login Screen:
  ┌─────────────────────────────────────┐
  │                                     │
  │           [ScribeFlow Logo]         │
  │                                     │
  │         Welcome to ScribeFlow       │
  │     Your intelligent writing companion │
  │                                     │
  │     [🔍] Continue with Google       │
  │                                     │
  │         Privacy Policy | Terms      │
  │                                     │
  └─────────────────────────────────────┘
  ```

  **Main Editor Interface:**

  ```
  Desktop Layout:
  ┌─────────────────────────────────────────────────────────────────┐
  │ ScribeFlow    [New] [Save] [Publish]           [Avatar] [Settings] │
  ├───────────┬─────────────────────────────────────┬─────────────────┤
  │ 📄 Stories │ # My Technical Blog Post           │ ✨ AI Assistant │
  │           │                                     │                 │
  │ • Story 1  │ Today I want to share my experience │ [Enhance Text]  │
  │ • Story 2  │ with building scalable APIs...      │                 │
  │ • Draft 3  │                                     │ Recent Code:    │
  │           │ ```python                           │ ✅ API endpoint │
  │ 🏷️ Tags   │ def create_user(user_data):         │ ⏳ Database     │
  │ • Python   │     return user_service.create()   │                 │
  │ • APIs     │ ```                                 │ 📊 Stats:      │
  │ • DevOps   │                                     │ 487 words      │
  │           │ [👁️ Preview] [▶️ Run Code]          │ 3 min read     │
  │ ⚙️ Settings│                                     │ 2 code blocks  │
  │           │                                     │                 │
  └───────────┴─────────────────────────────────────┴─────────────────┘
  ```

  **Mobile Editor Interface:**

  ```
  Mobile Layout:
  ┌─────────────────────────────────┐
  │ [☰] ScribeFlow        [⋮] [👤] │
  ├─────────────────────────────────┤
  │                                 │
  │ # My Technical Blog Post        │
  │                                 │
  │ Today I want to share my        │
  │ experience with building        │
  │ scalable APIs...                │
  │                                 │
  │ ```python                       │
  │ def create_user(user_data):     │
  │     return user_service.create()│
  │ ```                             │
  │                                 │
  │                                 │
  │                                 │
  ├─────────────────────────────────┤
  │        [✨ Enhance] [▶️ Run]     │
  └─────────────────────────────────┘
  ```

  ### 17.5 Component Design System

  **Button System:**

  ```dart
  // Primary Button (Actions like Save, Publish)
  ElevatedButton(
    style: ElevatedButton.styleFrom(
      backgroundColor: ScribeFlowColors.primary,
      foregroundColor: Colors.white,
      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      elevation: 2,
    ),
    child: Text('Publish Story'),
  )
  
  // Secondary Button (Cancel, Back actions)
  OutlinedButton(
    style: OutlinedButton.styleFrom(
      foregroundColor: ScribeFlowColors.primary,
      side: BorderSide(color: ScribeFlowColors.primary),
      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),
    child: Text('Cancel'),
  )
  
  // AI Enhancement Button (Special purple styling)
  Container(
    decoration: BoxDecoration(
      gradient: LinearGradient(
        colors: [ScribeFlowColors.aiAccent, ScribeFlowColors.primary],
      ),
      borderRadius: BorderRadius.circular(8),
    ),
    child: ElevatedButton.icon(
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.transparent,
        shadowColor: Colors.transparent,
      ),
      icon: Icon(Icons.auto_awesome),
      label: Text('Enhance with AI'),
    ),
  )
  ```

  **Card System:**

  ```dart
  // Story Card in sidebar
  Card(
    elevation: 1,
    margin: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    child: ListTile(
      leading: Icon(
        story.status == StoryStatus.published 
            ? Icons.public 
            : Icons.draft_outlined,
        color: story.status == StoryStatus.published 
            ? ScribeFlowColors.success 
            : ScribeFlowColors.medium,
      ),
      title: Text(
        story.title,
        style: Theme.of(context).textTheme.bodyLarge,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(
        '${story.wordCount} words • ${story.readTime} min read',
        style: Theme.of(context).textTheme.caption,
      ),
      trailing: PopupMenuButton(
        items: [
          PopupMenuItem(child: Text('Edit')),
          PopupMenuItem(child: Text('Duplicate')),
          PopupMenuItem(child: Text('Delete')),
        ],
      ),
    ),
  )
  ```

  ### 17.6 AI Enhancement UX Design

  **Text Selection & Enhancement Flow:**

  ```
  User Flow:
  1. User selects text in editor
     ↓
  2. Context menu appears with "✨ Enhance with AI" option
     ↓
  3. AI panel slides in from right with loading animation
     ↓
  4. Original and enhanced text shown side-by-side
     ↓
  5. User can Accept, Reject, or Refine with additional instructions
  ```

  **AI Suggestion Panel Design:**

  ```dart
  class AISuggestionPanel extends StatelessWidget {
    @override
    Widget build(BuildContext context) {
      return Container(
        width: 320,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(16),
            bottomLeft: Radius.circular(16),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 10,
              offset: Offset(-2, 0),
            ),
          ],
        ),
        child: Column(
          children: [
            // Header
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: ScribeFlowColors.aiAccent.withOpacity(0.1),
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(16),
                ),
              ),
              child: Row(
                children: [
                  Icon(Icons.auto_awesome, color: ScribeFlowColors.aiAccent),
                  SizedBox(width: 8),
                  Text('AI Enhancement', style: TextStyle(fontWeight: FontWeight.w600)),
                  Spacer(),
                  IconButton(
                    icon: Icon(Icons.close),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
            
            // Content comparison
            Expanded(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  children: [
                    // Original text
                    _buildTextBlock(
                      title: 'Original',
                      content: originalText,
                      color: Colors.grey[100],
                    ),
                    
                    SizedBox(height: 16),
                    
                    // Enhanced text
                    _buildTextBlock(
                      title: 'Enhanced',
                      content: enhancedText,
                      color: ScribeFlowColors.aiAccent.withOpacity(0.1),
                    ),
                    
                    SizedBox(height: 24),
                    
                    // Action buttons
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => _rejectSuggestion(),
                            child: Text('Reject'),
                          ),
                        ),
                        SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () => _acceptSuggestion(),
                            child: Text('Accept'),
                          ),
                        ),
                      ],
                    ),
                    
                    SizedBox(height: 12),
                    
                    // Refine button
                    TextButton.icon(
                      onPressed: () => _showRefineDialog(),
                      icon: Icon(Icons.edit),
                      label: Text('Refine with instructions'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    }
  }
  ```

  ### 17.7 Code Execution Interface

  **Inline Code Runner Design:**

  ```dart
  class CodeBlockWidget extends StatelessWidget {
    final String code;
    final String language;
    final bool isExecutable;
    
    @override
    Widget build(BuildContext context) {
      return Container(
        margin: EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: Colors.grey[900],
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey[700]!),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with language and run button
            Container(
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.grey[800],
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(8),
                  topRight: Radius.circular(8),
                ),
              ),
              child: Row(
                children: [
                  Text(
                    language.toUpperCase(),
                    style: TextStyle(
                      color: Colors.grey[400],
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Spacer(),
                  if (isExecutable)
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: ScribeFlowColors.success,
                        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        minimumSize: Size.zero,
                      ),
                      icon: Icon(Icons.play_arrow, size: 16),
                      label: Text('Run', style: TextStyle(fontSize: 12)),
                      onPressed: () => _executeCode(),
                    ),
                ],
              ),
            ),
            
            // Code content
            Container(
              padding: EdgeInsets.all(12),
              child: SelectableText(
                code,
                style: TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 14,
                  color: Colors.white,
                ),
              ),
            ),
            
            // Output section (when code is executed)
            if (hasOutput)
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.only(
                    bottomLeft: Radius.circular(8),
                    bottomRight: Radius.circular(8),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Output:',
                      style: TextStyle(
                        color: ScribeFlowColors.success,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    SizedBox(height: 4),
                    SelectableText(
                      output,
                      style: TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 13,
                        color: Colors.green[400],
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      );
    }
  }
  ```

  ### 17.8 Publishing Workflow UI

  **Publishing Dialog Design:**

  ```dart
  class PublishDialog extends StatefulWidget {
    @override
    _PublishDialogState createState() => _PublishDialogState();
  }
  
  class _PublishDialogState extends State<PublishDialog> {
    @override
    Widget build(BuildContext context) {
      return Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Container(
          width: 500,
          padding: EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  Icon(Icons.publish, color: ScribeFlowColors.primary),
                  SizedBox(width: 12),
                  Text(
                    'Publish Story',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  Spacer(),
                  IconButton(
                    icon: Icon(Icons.close),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
              
              SizedBox(height: 24),
              
              // Platform selection
              Text('Select Platform:', style: TextStyle(fontWeight: FontWeight.w600)),
              SizedBox(height: 12),
              
              Wrap(
                spacing: 12,
                children: [
                  _buildPlatformChip('Medium', Icons.article, isSelected: true),
                  _buildPlatformChip('Dev.to', Icons.code, isSelected: false),
                  _buildPlatformChip('Blogger', Icons.edit, isSelected: false),
                ],
              ),
              
              SizedBox(height: 24),
              
              // Tags input
              Text('Tags:', style: TextStyle(fontWeight: FontWeight.w600)),
              SizedBox(height: 8),
              
              TagInputField(
                tags: currentTags,
                onTagsChanged: (tags) => setState(() => currentTags = tags),
              ),
              
              SizedBox(height: 24),
              
              // Publishing options
              CheckboxListTile(
                title: Text('Publish as draft'),
                value: publishAsDraft,
                onChanged: (value) => setState(() => publishAsDraft = value),
                contentPadding: EdgeInsets.zero,
              ),
              
              CheckboxListTile(
                title: Text('Allow responses'),
                value: allowResponses,
                onChanged: (value) => setState(() => allowResponses = value),
                contentPadding: EdgeInsets.zero,
              ),
              
              SizedBox(height: 32),
              
              // Action buttons
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: Text('Cancel'),
                    ),
                  ),
                  SizedBox(width: 16),
                  Expanded(
                    child: ElevatedButton.icon(
                      icon: Icon(Icons.publish),
                      label: Text('Publish Now'),
                      onPressed: _publishStory,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    }
  }
  ```

  ### 17.9 Responsive Design Strategy

  **Breakpoint System:**

  ```dart
  class ResponsiveBreakpoints {
    static const double mobile = 768;
    static const double tablet = 1024;
    static const double desktop = 1200;
    static const double wide = 1400;
    
    static bool isMobile(BuildContext context) =>
        MediaQuery.of(context).size.width < mobile;
    
    static bool isTablet(BuildContext context) =>
        MediaQuery.of(context).size.width >= mobile &&
        MediaQuery.of(context).size.width < desktop;
    
    static bool isDesktop(BuildContext context) =>
        MediaQuery.of(context).size.width >= desktop;
  }
  ```

  **Adaptive Layout Implementation:**

  ```dart
  class AdaptiveLayout extends StatelessWidget {
    final Widget mobileLayout;
    final Widget tabletLayout;
    final Widget desktopLayout;
    
    @override
    Widget build(BuildContext context) {
      return LayoutBuilder(
        builder: (context, constraints) {
          if (constraints.maxWidth < ResponsiveBreakpoints.mobile) {
            return mobileLayout;
          } else if (constraints.maxWidth < ResponsiveBreakpoints.desktop) {
            return tabletLayout ?? mobileLayout;
          } else {
            return desktopLayout;
          }
        },
      );
    }
  }
  ```

  ### 17.10 Animation & Micro-interactions

  **Key Animation Principles:**

  1. **Purposeful Motion**: Every animation serves a clear purpose
  2. **Consistent Timing**: Standard duration curves (200ms for simple, 300ms for complex)
  3. **Natural Easing**: Use ease-out for entrances, ease-in for exits
  4. **Respect Accessibility**: Honor reduced motion preferences

  **Core Animations:**

  ```dart
  // Page transitions
  class SlidePageRoute<T> extends PageRouteBuilder<T> {
    final Widget child;
    
    SlidePageRoute({required this.child})
        : super(
            pageBuilder: (context, animation, _) => child,
            transitionsBuilder: (context, animation, secondaryAnimation, child) {
              return SlideTransition(
                position: Tween<Offset>(
                  begin: Offset(1.0, 0.0),
                  end: Offset.zero,
                ).animate(CurvedAnimation(
                  parent: animation,
                  curve: Curves.easeOutCubic,
                )),
                child: child,
              );
            },
            transitionDuration: Duration(milliseconds: 300),
          );
  }
  
  // AI suggestion slide-in
  class AIPanelSlideAnimation extends StatefulWidget {
    @override
    _AIPanelSlideAnimationState createState() => _AIPanelSlideAnimationState();
  }
  
  class _AIPanelSlideAnimationState extends State<AIPanelSlideAnimation>
      with SingleTickerProviderStateMixin {
    late AnimationController _controller;
    late Animation<Offset> _slideAnimation;
    late Animation<double> _fadeAnimation;
    
    @override
    void initState() {
      super.initState();
      _controller = AnimationController(
        duration: Duration(milliseconds: 400),
        vsync: this,
      );
      
      _slideAnimation = Tween<Offset>(
        begin: Offset(1.0, 0.0),
        end: Offset.zero,
      ).animate(CurvedAnimation(
        parent: _controller,
        curve: Curves.easeOutCubic,
      ));
      
      _fadeAnimation = Tween<double>(
        begin: 0.0,
        end: 1.0,
      ).animate(CurvedAnimation(
        parent: _controller,
        curve: Interval(0.3, 1.0, curve: Curves.easeOut),
      ));
      
      _controller.forward();
    }
    
    @override
    Widget build(BuildContext context) {
      return SlideTransition(
        position: _slideAnimation,
        child: FadeTransition(
          opacity: _fadeAnimation,
          child: AISuggestionPanel(),
        ),
      );
    }
  }
  ```

  ### 17.11 Accessibility Design

  **Accessibility Compliance (WCAG 2.1 AA):**

  ```dart
  class AccessibleScribeFlow {
    // Color contrast ratios
    static const double minContrastRatio = 4.5; // AA standard
    
    // Focus management
    static FocusNode createManagedFocus({String? debugLabel}) {
      return FocusNode(
        debugLabel: debugLabel,
        descendantsAreFocusable: true,
        descendantsAreTraversable: true,
      );
    }
    
    // Semantic labels
    static Widget semanticWrapper({
      required Widget child,
      required String label,
      String? hint,
      bool isButton = false,
      bool isHeading = false,
    }) {
      return Semantics(
        label: label,
        hint: hint,
        button: isButton,
        header: isHeading,
        child: child,
      );
    }
  }
  ```

 **Screen Reader Support:**

  ```dart
  // AI enhancement button with proper semantics
  Semantics(
    label: 'Enhance selected text with AI',
    hint: 'Double tap to improve the selected text using artificial intelligence',
    button: true,
    child: ElevatedButton.icon(
      icon: Icon(Icons.auto_awesome),
      label: Text('Enhance with AI'),
      onPressed: _enhanceText,
    ),
  )
  
  // Code execution with status announcements
  class AccessibleCodeRunner extends StatelessWidget {
    @override
    Widget build(BuildContext context) {
      return Semantics(
        liveRegion: true,
        child: Column(
          children: [
            CodeBlockWidget(),
            if (isExecuting)
              Semantics(
                label: 'Code is executing, please wait',
                child: CircularProgressIndicator(),
              ),
            if (hasOutput)
              Semantics(
                label: 'Code execution complete. Output: $output',
                child: OutputWidget(),
              ),
          ],
        ),
      );
    }
  }
  ```

  ### 17.12 Dark Mode & Theme System

  **Theme Configuration:**

  ```dart
  class ScribeFlowTheme {
    static ThemeData lightTheme = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: ScribeFlowColors.primary,
        brightness: Brightness.light,
      ),
      fontFamily: 'Inter',
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
    );
    
    static ThemeData darkTheme = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: ScribeFlowColors.primary,
        brightness: Brightness.dark,
      ),
      fontFamily: 'Inter',
      scaffoldBackgroundColor: Color(0xFF121212),
      cardColor: Color(0xFF1E1E1E),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
    };
  }
  ```

  ### 17.13 Performance Considerations

  **UI Performance Optimizations:**

  1. **Efficient Rebuilds**: Use const constructors and keys appropriately
  2. **List Virtualization**: ListView.builder for large story lists
  3. **Image Optimization**: Cached network images with proper sizing
  4. **Animation Performance**: Use Transform instead of positioned widgets
  5. **Text Rendering**: Precompute text spans for syntax highlighting

  ```dart
  // Optimized story list
  class OptimizedStoryList extends StatelessWidget {
    @override
    Widget build(BuildContext context) {
      return ListView.builder(
        itemCount: stories.length,
        itemBuilder: (context, index) {
          final story = stories[index];
          return StoryCard(
            key: ValueKey(story.id), // Stable key for efficient updates
            story: story,
          );
        },
        cacheExtent: 1000, // Cache off-screen items
      );
    }
  }
  ```

  ### 17.14 User Testing & Iteration Plan

  **Usability Testing Framework:**

  1. **Moderated Remote Sessions**: 5 users per iteration cycle
  2. **A/B Testing**: AI suggestion placement and timing
  3. **Analytics Integration**: Track user engagement and pain points
  4. **Accessibility Testing**: Screen reader and keyboard navigation validation
  5. **Performance Monitoring**: Real-user monitoring for UI responsiveness

  **Key Metrics to Track:**
  - Time to first enhancement: < 30 seconds
  - AI suggestion acceptance rate: > 60%
  - Publishing completion rate: > 85%
  - Cross-platform consistency score: > 95%
  - Accessibility compliance score: 100% WCAG 2.1 AA

  This comprehensive UX/UI design system ensures ScribeFlow delivers a premium, accessible, and intuitive experience across all platforms while maintaining the focus on seamless technical writing and AI-enhanced content creation.

