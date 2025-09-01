"""
Basic test to verify NHS Paperwork Agent functionality
"""

import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from src.models.schemas import ClinicalNote, ExtractedData, FormTypeEnum
        from src.services.form_templates import FormTemplateService
        from src.services.form_filler import FormFillerService
        from src.core.config import settings, ensure_directories
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_form_templates():
    """Test form template service"""
    try:
        from src.services.form_templates import FormTemplateService
        from src.models.schemas import FormTypeEnum
        
        service = FormTemplateService()
        templates = service.get_all_templates()
        
        expected_forms = [
            FormTypeEnum.DISCHARGE_SUMMARY,
            FormTypeEnum.REFERRAL,
            FormTypeEnum.RISK_ASSESSMENT
        ]
        
        for form_type in expected_forms:
            template = service.get_template(form_type)
            if template is None:
                print(f"❌ Template missing: {form_type}")
                return False
            print(f"✅ Template found: {template.form_name} ({len(template.fields)} fields)")
        
        return True
    except Exception as e:
        print(f"❌ Form template test failed: {e}")
        return False

def test_directories():
    """Test directory creation"""
    try:
        from src.core.config import ensure_directories
        ensure_directories()
        
        required_dirs = ["data", "data/uploads", "data/forms", "templates"]
        for directory in required_dirs:
            if not os.path.exists(directory):
                print(f"❌ Directory not created: {directory}")
                return False
            print(f"✅ Directory exists: {directory}")
        
        return True
    except Exception as e:
        print(f"❌ Directory test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("🧪 Running Basic Tests for NHS Paperwork Agent")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Form Templates", test_form_templates), 
        ("Directory Setup", test_directories),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🏆 Tests Passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Add your OpenAI API key to .env file")
        print("2. Run: python demo.py")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
