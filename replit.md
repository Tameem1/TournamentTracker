# Tournament Management System (نادي الأمين)

## Overview

This is a tournament management system built for "نادي الأمين" (Al-Ameen Club) using Streamlit. The application manages sports tournaments with support for multiple sports including football, basketball, tennis, and ping pong. The system handles team registration, match scheduling, score tracking, and provides a dashboard for viewing tournament progress. The interface is primarily in Arabic to serve the target user base.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Framework
- **Streamlit**: Chosen for rapid development of interactive web applications with minimal frontend code
- **Session State Management**: Uses Streamlit's session state to maintain application state across page reloads and user interactions
- **Multi-page Navigation**: Implements a sidebar-based navigation system with different views (dashboard, tournament management)

### Data Models
- **Object-Oriented Design**: Uses Python dataclasses for clean data modeling
- **Enum-Based Types**: SportType and MatchStatus enums for type safety and consistency
- **Unique Identifiers**: UUID-based IDs for teams, matches, and tournaments to ensure data integrity

### Data Storage
- **JSON File Storage**: Simple file-based persistence using `tournaments_data.json`
- **Dictionary-Based Memory Storage**: Runtime data stored in Python dictionaries for fast access
- **Session State Integration**: Tournament data cached in Streamlit session state for performance

### Tournament Logic
- **Multiple Tournament Support**: Can manage concurrent tournaments for different sports
- **Team Management**: Handles team registration and organization within tournaments
- **Match System**: Tracks match results with status management (pending/completed)
- **Score Validation**: Built-in score validation system for match results

### User Interface Components
- **Responsive Layout**: Wide layout configuration for better use of screen space
- **Arabic RTL Support**: Designed to handle Arabic text and right-to-left reading
- **Icon Integration**: Sport-specific emoji icons for visual identification
- **Interactive Controls**: Real-time updates using Streamlit's reactive model

## External Dependencies

### Core Framework
- **Streamlit**: Web application framework for creating the user interface and handling user interactions

### Python Standard Library
- **json**: Data serialization for tournament persistence
- **os**: File system operations for data storage
- **uuid**: Unique identifier generation for entities
- **time**: Time-based operations for potential slideshow features
- **dataclasses**: Object-oriented data modeling
- **enum**: Type-safe enumeration definitions
- **typing**: Type hints and annotations for code clarity

### Data Persistence
- **File System**: Local JSON file storage for tournament data
- No external database dependencies - uses simple file-based storage for ease of deployment