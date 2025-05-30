#!/usr/bin/env python3
"""
Simple verification script for MOT OCR System setup.
This script checks the project structure without requiring dependencies.
"""
import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and print status."""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False

def check_directory_exists(dir_path, description):
    """Check if a directory exists and print status."""
    if Path(dir_path).is_dir():
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (MISSING)")
        return False

def main():
    """Main verification function."""
    print("🔍 MOT OCR System - Setup Verification")
    print("=" * 50)
    
    # Check core files
    core_files = [
        ("README.md", "Project README"),
        ("requirements.txt", "Dependencies file"),
        ("run.py", "Main startup script"),
        ("test_system.py", "System test script"),
        (".env.example", "Environment template"),
        ("setup.py", "Package setup"),
        ("LICENSE", "License file"),
        ("INSTALLATION.md", "Installation guide"),
        ("CONTRIBUTING.md", "Contributing guide"),
        ("Dockerfile", "Docker configuration"),
        ("docker-compose.yml", "Docker Compose"),
        (".gitignore", "Git ignore file"),
    ]
    
    print("\n📁 Core Files:")
    core_files_ok = all(check_file_exists(file, desc) for file, desc in core_files)
    
    # Check directories
    directories = [
        ("src", "Source code directory"),
        ("src/api", "API module"),
        ("src/vision_models", "Vision models"),
        ("src/pipeline", "Processing pipeline"),
        ("src/validation", "Validation module"),
        ("src/dvla", "DVLA integration"),
        ("src/utils", "Utilities"),
        ("config", "Configuration"),
        ("tests", "Test suite"),
        ("docs", "Documentation"),
        (".github/workflows", "CI/CD workflows"),
    ]
    
    print("\n📂 Directories:")
    dirs_ok = all(check_directory_exists(dir_path, desc) for dir_path, desc in directories)
    
    # Check source files
    source_files = [
        ("src/api/main.py", "FastAPI application"),
        ("src/api/models.py", "API models"),
        ("src/vision_models/base_vision_model.py", "Base vision model"),
        ("src/vision_models/claude_vision.py", "Claude integration"),
        ("src/vision_models/gpt4_vision.py", "GPT-4V integration"),
        ("src/pipeline/ensemble_pipeline.py", "Ensemble pipeline"),
        ("src/validation/uk_registration_validator.py", "UK registration validator"),
        ("src/validation/date_validator.py", "Date validator"),
        ("src/dvla/api_client.py", "DVLA API client"),
        ("src/utils/logger.py", "Logging utilities"),
        ("src/utils/file_handler.py", "File handling"),
        ("config/settings.py", "Configuration settings"),
    ]
    
    print("\n🐍 Source Files:")
    source_files_ok = all(check_file_exists(file, desc) for file, desc in source_files)
    
    # Check Git setup
    print("\n🔧 Git Setup:")
    git_ok = True
    if Path(".git").is_dir():
        print("✅ Git repository initialized")
        
        # Check if we have commits
        try:
            import subprocess
            result = subprocess.run(["git", "log", "--oneline"], 
                                  capture_output=True, text=True, cwd=".")
            if result.returncode == 0 and result.stdout.strip():
                print("✅ Initial commit created")
            else:
                print("❌ No commits found")
                git_ok = False
        except:
            print("⚠️  Could not check Git commits")
    else:
        print("❌ Git repository not initialized")
        git_ok = False
    
    # Check environment template
    print("\n⚙️  Environment Configuration:")
    env_ok = True
    if Path(".env.example").exists():
        print("✅ Environment template exists")
        with open(".env.example", "r") as f:
            content = f.read()
            required_keys = [
                "ANTHROPIC_API_KEY",
                "OPENAI_API_KEY", 
                "GOOGLE_API_KEY",
                "DVLA_API_KEY"
            ]
            for key in required_keys:
                if key in content:
                    print(f"✅ {key} template found")
                else:
                    print(f"❌ {key} template missing")
                    env_ok = False
    else:
        print("❌ Environment template missing")
        env_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY:")
    print("=" * 50)
    
    all_ok = core_files_ok and dirs_ok and source_files_ok and git_ok and env_ok
    
    if all_ok:
        print("🎉 ALL CHECKS PASSED!")
        print("\n✅ Your MOT OCR System is properly set up!")
        print("\n📋 Next Steps:")
        print("1. Create GitHub repository at: https://github.com/new")
        print("2. Set repository name to: MOTCHECK")
        print("3. Push code: git remote add origin <your-repo-url>")
        print("4. Install dependencies: pip install -r requirements.txt")
        print("5. Configure API keys in .env file")
        print("6. Run system test: python test_system.py")
        
    else:
        print("⚠️  SOME ISSUES FOUND!")
        print("\n❌ Please check the missing files/directories above")
        print("💡 Try running the setup script again: ./setup_git.sh")
    
    # File count summary
    total_files = len([f for f in Path(".").rglob("*") if f.is_file() and not f.name.startswith(".")])
    print(f"\n📈 Project Statistics:")
    print(f"   • Total files: {total_files}")
    print(f"   • Python files: {len(list(Path('.').rglob('*.py')))}")
    print(f"   • Documentation files: {len(list(Path('.').rglob('*.md')))}")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
