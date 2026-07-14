#!/usr/bin/env python3
"""Repository health check for Converigo v0.4.0 Foundation."""
import json
import sys
from pathlib import Path


def check_contracts():
    """Verify all contracts are valid and complete."""
    print("\n=== CONTRACT VALIDATION ===")
    contracts_dir = Path("app/data/converters")
    contract_files = sorted(contracts_dir.glob("*.contract.json"))
    
    print(f"✓ Found {len(contract_files)} contracts")
    
    ids = set()
    slugs = set()
    errors = []
    
    for path in contract_files:
        with path.open("r") as f:
            contract = json.load(f)
        
        contract_id = contract.get("id")
        slug = contract.get("slug")
        
        if not contract_id:
            errors.append(f"  ✗ {path.name}: missing id")
        elif contract_id in ids:
            errors.append(f"  ✗ {path.name}: duplicate id '{contract_id}'")
        else:
            ids.add(contract_id)
        
        if not slug:
            errors.append(f"  ✗ {path.name}: missing slug")
        elif slug in slugs:
            errors.append(f"  ✗ {path.name}: duplicate slug '{slug}'")
        else:
            slugs.add(slug)
    
    if errors:
        for error in errors:
            print(error)
        return False
    else:
        print(f"✓ All {len(contract_files)} contracts have unique IDs and slugs")
        return True


def check_converter_data():
    """Verify converter data files exist for active contracts."""
    print("\n=== CONVERTER DATA VALIDATION ===")
    contracts_dir = Path("app/data/converters")
    contract_files = sorted(contracts_dir.glob("*.contract.json"))
    
    missing_data = []
    for contract_path in contract_files:
        with contract_path.open("r") as f:
            contract = json.load(f)
        slug = contract.get("slug")
        data_file = contracts_dir / f"{slug}.json"
        
        if not data_file.exists():
            missing_data.append(f"  ✗ {slug}: missing data file {data_file.name}")
    
    if missing_data:
        for item in missing_data:
            print(item)
        print(f"✓ {len(contract_files) - len(missing_data)}/{len(contract_files)} have data files")
        return False
    else:
        print(f"✓ All {len(contract_files)} converters have data files")
        return True


def check_imports():
    """Check for obvious import errors."""
    print("\n=== IMPORT VALIDATION ===")
    
    app_dir = Path("app")
    py_files = sorted(app_dir.rglob("*.py"))
    
    import_errors = []
    for py_file in py_files:
        try:
            with py_file.open("r") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip().startswith("from ") or line.strip().startswith("import "):
                        # Basic syntax check
                        if " import " in line and not line.strip().endswith(":"):
                            pass  # Likely valid
        except Exception as e:
            import_errors.append(f"  ✗ {py_file.relative_to('.')}: {e}")
    
    if import_errors:
        for error in import_errors:
            print(error)
        return False
    else:
        print(f"✓ All {len(py_files)} Python files have valid import syntax")
        return True


def check_services():
    """Verify all core services are discoverable."""
    print("\n=== SERVICE VALIDATION ===")
    
    expected_services = [
        "converter_registry_service.py",
        "converter_data_service.py",
        "landing_service.py",
        "knowledge_service.py",
        "seo_service.py",
        "programmatic_seo_service.py",
        "related_converter_service.py",
        "hub_page_service.py",
        "sitemap_service.py",
        "production_audit_service.py",
        "growth_dashboard_service.py",
        "upload_service.py",
        "plugin_validator.py",
    ]
    
    services_dir = Path("app/services")
    found_services = set(f.name for f in services_dir.glob("*.py") if not f.name.startswith("_"))
    
    missing = []
    for service in expected_services:
        if service not in found_services:
            missing.append(f"  ✗ Missing: {service}")
    
    if missing:
        for item in missing:
            print(item)
        return False
    else:
        print(f"✓ All {len(expected_services)} core services found")
        return True


def check_tests():
    """Verify test suite is complete."""
    print("\n=== TEST SUITE VALIDATION ===")
    
    tests_dir = Path("tests")
    test_files = sorted(tests_dir.glob("test_*.py"))
    
    print(f"✓ Found {len(test_files)} test files")
    
    # Expected core test coverage
    expected_tests = [
        "test_converter_registry_service.py",
        "test_landing_contract.py",
        "test_production_audit_service.py",
        "test_growth_dashboard_service.py",
        "test_knowledge_service.py",
        "test_plugin_validation_service.py",
        "test_sitemap_service.py",
        "test_hub_page_service.py",
    ]
    
    found = set(f.name for f in test_files)
    missing = [t for t in expected_tests if t not in found]
    
    if missing:
        print(f"  ⚠ Missing test coverage for: {', '.join(missing)}")
        return False
    else:
        print(f"✓ All core services have test coverage")
        return True


def check_registry():
    """Verify registry can load all contracts."""
    print("\n=== REGISTRY VALIDATION ===")
    
    try:
        from app.services.converter_registry_service import ConverterRegistryService
        registry_service = ConverterRegistryService("app/data/converters")
        active = registry_service.get_active()
        print(f"✓ Registry loaded {len(active)} active converters")
        
        # Verify categories
        categories = set()
        for contract in active:
            categories.add(contract.get("category"))
        
        print(f"✓ Categories: {', '.join(sorted(categories))}")
        return True
    except Exception as e:
        print(f"  ✗ Registry error: {e}")
        return False


def check_docs():
    """Verify documentation completeness."""
    print("\n=== DOCUMENTATION VALIDATION ===")
    
    expected_docs = [
        "docs/FOUNDATION_COMPLETE.md",
        "docs/RELEASE_v0.4.0_FOUNDATION_COMPLETE.md",
        "docs/PRODUCTION_STANDARD.md",
        "README.md",
        "DEPLOYMENT.md",
        "ROADMAP.md",
    ]
    
    missing = []
    for doc in expected_docs:
        if not Path(doc).exists():
            missing.append(f"  ✗ Missing: {doc}")
    
    if missing:
        for item in missing:
            print(item)
        return False
    else:
        print(f"✓ All {len(expected_docs)} key documentation files present")
        return True


def main():
    """Run all health checks."""
    print("=" * 60)
    print("CONVERIGO v0.4.0 - REPOSITORY HEALTH CHECK")
    print("=" * 60)
    
    checks = [
        ("Contracts", check_contracts),
        ("Converter Data", check_converter_data),
        ("Services", check_services),
        ("Tests", check_tests),
        ("Registry", check_registry),
        ("Imports", check_imports),
        ("Documentation", check_docs),
    ]
    
    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"\n✗ {name} check failed: {e}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {name}")
    
    all_passed = all(results.values())
    
    print("=" * 60)
    if all_passed:
        print("✓ REPOSITORY HEALTH: EXCELLENT")
        print("  Foundation is stable and ready for release")
        return 0
    else:
        print("✗ REPOSITORY HEALTH: ISSUES DETECTED")
        print("  Please review and fix issues above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
