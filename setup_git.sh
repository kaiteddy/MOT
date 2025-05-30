#!/bin/bash

# MOT OCR System - Git Setup Script
# This script initializes the Git repository and sets up GitHub integration

set -e  # Exit on any error

echo "🚀 MOT OCR System - Git Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

print_status "Git is installed"

# Check if we're already in a Git repository
if [ -d ".git" ]; then
    print_warning "Already in a Git repository"
    read -p "Do you want to continue? This will modify the existing repository. (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Exiting..."
        exit 0
    fi
else
    # Initialize Git repository
    print_info "Initializing Git repository..."
    git init
    print_status "Git repository initialized"
fi

# Set up Git configuration (if not already set)
if [ -z "$(git config --global user.name)" ]; then
    read -p "Enter your Git username: " git_username
    git config --global user.name "$git_username"
    print_status "Git username set to: $git_username"
fi

if [ -z "$(git config --global user.email)" ]; then
    read -p "Enter your Git email: " git_email
    git config --global user.email "$git_email"
    print_status "Git email set to: $git_email"
fi

# Set default branch to main
git config init.defaultBranch main
print_status "Default branch set to 'main'"

# Add all files to Git
print_info "Adding files to Git..."
git add .

# Check if there are any changes to commit
if git diff --staged --quiet; then
    print_warning "No changes to commit"
else
    # Create initial commit
    print_info "Creating initial commit..."
    git commit -m "Initial commit: MOT OCR System with Vision-Language Models

Features:
- Multi-model ensemble (Claude 3.5 Sonnet, GPT-4V, Gemini Pro)
- 99%+ accuracy MOT data extraction
- UK registration validation
- DVLA API integration
- Production-ready FastAPI
- Comprehensive test suite
- Docker support
- CI/CD pipeline"

    print_status "Initial commit created"
fi

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    print_status "GitHub CLI is installed"
    
    # Check if user is authenticated
    if gh auth status &> /dev/null; then
        print_status "GitHub CLI is authenticated"
        
        # Ask if user wants to create a GitHub repository
        echo
        print_info "GitHub Repository Setup"
        echo "========================"
        read -p "Do you want to create a new GitHub repository? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter repository name (default: MOTCHECK): " repo_name
            repo_name=${repo_name:-MOTCHECK}
            
            read -p "Enter repository description (optional): " repo_description
            repo_description=${repo_description:-"High-accuracy MOT reminder data extraction using Vision-Language Models"}
            
            read -p "Make repository public? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                visibility="--public"
            else
                visibility="--private"
            fi
            
            print_info "Creating GitHub repository..."
            
            # Create the repository
            if gh repo create "$repo_name" $visibility --description "$repo_description" --source=. --remote=origin --push; then
                print_status "GitHub repository created successfully!"
                print_info "Repository URL: https://github.com/$(gh api user --jq .login)/$repo_name"
                
                # Set up branch protection (optional)
                read -p "Do you want to set up branch protection for main branch? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    print_info "Setting up branch protection..."
                    gh api repos/$(gh api user --jq .login)/$repo_name/branches/main/protection \
                        --method PUT \
                        --field required_status_checks='{"strict":true,"contexts":["test"]}' \
                        --field enforce_admins=true \
                        --field required_pull_request_reviews='{"required_approving_review_count":1}' \
                        --field restrictions=null \
                        2>/dev/null || print_warning "Could not set up branch protection (may require admin permissions)"
                fi
                
            else
                print_error "Failed to create GitHub repository"
            fi
        fi
    else
        print_warning "GitHub CLI is not authenticated"
        print_info "Run 'gh auth login' to authenticate with GitHub"
    fi
else
    print_warning "GitHub CLI is not installed"
    print_info "Manual GitHub setup required:"
    echo "1. Go to https://github.com/new"
    echo "2. Create a new repository named 'MOTCHECK'"
    echo "3. Run the following commands:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/MOTCHECK.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
fi

# Set up Git hooks (optional)
echo
print_info "Git Hooks Setup"
echo "==============="
read -p "Do you want to set up pre-commit hooks for code quality? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create pre-commit hook
    mkdir -p .git/hooks
    
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for MOT OCR System

echo "Running pre-commit checks..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Virtual environment not activated"
fi

# Run black formatting check
if command -v black &> /dev/null; then
    echo "Checking code formatting with black..."
    if ! black --check src/ tests/ 2>/dev/null; then
        echo "Code formatting issues found. Run 'black src/ tests/' to fix."
        exit 1
    fi
fi

# Run flake8 linting
if command -v flake8 &> /dev/null; then
    echo "Running flake8 linting..."
    if ! flake8 src/ --max-line-length=88 --extend-ignore=E203,W503; then
        echo "Linting issues found. Please fix before committing."
        exit 1
    fi
fi

# Run tests
if command -v pytest &> /dev/null; then
    echo "Running tests..."
    if ! pytest tests/ -q; then
        echo "Tests failed. Please fix before committing."
        exit 1
    fi
fi

echo "All pre-commit checks passed!"
EOF

    chmod +x .git/hooks/pre-commit
    print_status "Pre-commit hook installed"
fi

# Create development branch
echo
print_info "Branch Setup"
echo "============"
read -p "Do you want to create a 'develop' branch for development? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    git checkout -b develop
    git checkout main
    print_status "Development branch 'develop' created"
    print_info "Use 'git checkout develop' to switch to development branch"
fi

# Final instructions
echo
print_status "Git setup completed successfully!"
echo
print_info "Next Steps:"
echo "==========="
echo "1. Configure your API keys in .env file"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Run tests: python test_system.py"
echo "4. Start development: python run.py"
echo
print_info "Git Workflow:"
echo "============="
echo "• Work on feature branches: git checkout -b feature/your-feature"
echo "• Commit changes: git add . && git commit -m 'Your message'"
echo "• Push to GitHub: git push origin your-branch"
echo "• Create pull requests on GitHub"
echo
print_info "Useful Git Commands:"
echo "==================="
echo "• Check status: git status"
echo "• View history: git log --oneline"
echo "• Create branch: git checkout -b branch-name"
echo "• Switch branch: git checkout branch-name"
echo "• Push changes: git push origin branch-name"
echo
echo "🎉 Happy coding!"
