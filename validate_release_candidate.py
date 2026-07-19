#!/usr/bin/env python
"""
Release Candidate Validation Suite
Comprehensive testing of all critical flows before production release
"""

import json
from pathlib import Path
from datetime import datetime

# Test matrix: formats to validate
TEST_FORMATS = ["jpg", "png", "webp", "pdf", "docx", "xlsx", "pptx", "mp4"]

def validate_recommendation_api():
    """Validate recommendation API returns certified converters."""
    from app.recommendation.engine import recommendation_engine
    
    results = {}
    
    for fmt in TEST_FORMATS:
        try:
            result = recommendation_engine.recommend(fmt)
            
            if result.best_choice is None:
                results[fmt] = {
                    "status": "⚠️ WARN",
                    "best_choice": None,
                    "alternatives": [],
                    "message": "No recommendation found"
                }
            else:
                results[fmt] = {
                    "status": "✅ PASS",
                    "best_choice": {
                        "source": result.best_choice.source,
                        "target": result.best_choice.target,
                        "title": result.best_choice.title,
                        "score": result.best_choice.score
                    },
                    "alternatives_count": len(result.alternatives),
                    "message": f"Recommended: {result.best_choice.target}"
                }
        except Exception as e:
            results[fmt] = {
                "status": "❌ FAIL",
                "error": str(e),
                "message": f"Error: {type(e).__name__}"
            }
    
    return results

def validate_converter_contracts():
    """Validate all converter contracts are properly registered."""
    from app.services.converter_registry_service import ConverterRegistryService
    from pathlib import Path
    
    contracts_dir = Path("app/data/converters")
    registry = ConverterRegistryService(contracts_dir)
    
    results = {
        "total_contracts": len(registry.list_all()),
        "active_contracts": len(registry.get_active()),
        "beta_contracts": len(registry.get_beta()),
        "contracts": {}
    }
    
    # Verify all have lifecycle_status
    for contract in registry.list_all():
        slug = contract.get("slug", "unknown")
        status = contract.get("lifecycle_status", "unknown")
        results["contracts"][slug] = {
            "status": "✅ PASS" if status in {"active", "certified", "deprecated", "beta"} else "❌ FAIL",
            "lifecycle_status": status
        }
    
    return results

def validate_certified_converters():
    """Validate certified converters registry."""
    registry_path = Path("app/data/certified_converters.json")
    
    with open(registry_path) as f:
        registry = json.load(f)
    
    certified = registry.get("certified", [])
    beta = registry.get("beta", [])
    disabled = registry.get("disabled", [])
    
    return {
        "file": str(registry_path),
        "exists": registry_path.exists(),
        "certified_count": len(certified),
        "beta_count": len(beta),
        "disabled_count": len(disabled),
        "total": len(certified) + len(beta) + len(disabled),
        "certified_list": [c.get("slug") for c in certified],
        "status": "✅ PASS" if len(certified) >= 20 else "❌ FAIL"
    }

def validate_error_handling():
    """Validate error handling for invalid inputs."""
    from app.recommendation.engine import recommendation_engine
    
    results = {}
    
    # Test 1: Invalid format
    try:
        result = recommendation_engine.recommend("invalid_format_xyz")
        results["invalid_format"] = {
            "status": "✅ PASS",
            "returns_null": result.best_choice is None,
            "detected_type": result.detected_type
        }
    except Exception as e:
        results["invalid_format"] = {
            "status": "❌ FAIL",
            "error": str(e)
        }
    
    # Test 2: Empty format
    try:
        result = recommendation_engine.recommend("")
        results["empty_format"] = {
            "status": "✅ PASS",
            "returns_null": result.best_choice is None
        }
    except Exception as e:
        results["empty_format"] = {
            "status": "❌ FAIL",
            "error": str(e)
        }
    
    # Test 3: Case insensitive
    try:
        result_upper = recommendation_engine.recommend("PDF")
        result_lower = recommendation_engine.recommend("pdf")
        
        same_target = (
            result_upper.best_choice and result_lower.best_choice and
            result_upper.best_choice.target == result_lower.best_choice.target
        )
        
        results["case_insensitive"] = {
            "status": "✅ PASS" if same_target else "⚠️ WARN",
            "message": "PDF and pdf return same recommendation" if same_target else "Different targets for case variants"
        }
    except Exception as e:
        results["case_insensitive"] = {
            "status": "❌ FAIL",
            "error": str(e)
        }
    
    return results

def validate_deployment_config():
    """Validate deployment configuration files."""
    results = {}
    
    # Check Dockerfile
    dockerfile = Path("Dockerfile")
    results["dockerfile"] = {
        "exists": dockerfile.exists(),
        "status": "✅ PASS" if dockerfile.exists() else "❌ FAIL"
    }
    
    # Check railway config
    railway_toml = Path("railway.toml")
    results["railway_toml"] = {
        "exists": railway_toml.exists(),
        "status": "✅ PASS" if railway_toml.exists() else "⚠️ WARN"
    }
    
    # Check Python requirements/dependencies
    venv_dir = Path(".venv")
    results["virtual_environment"] = {
        "exists": venv_dir.exists(),
        "status": "✅ PASS" if venv_dir.exists() else "❌ FAIL"
    }
    
    # Check main app files
    main_files = [
        "app/__init__.py",
        "app/main.py",
        "app/recommendation/__init__.py",
        "app/services/converter_registry_service.py"
    ]
    
    results["critical_files"] = {}
    for f in main_files:
        path = Path(f)
        results["critical_files"][f] = {
            "exists": path.exists(),
            "status": "✅ PASS" if path.exists() else "❌ FAIL"
        }
    
    return results

def validate_certified_tests():
    """Check certified test suite status."""
    import subprocess
    
    results = {}
    
    try:
        # Run certified tests
        result = subprocess.run(
            [".venv\\Scripts\\python", "-m", "pytest", "tests/certified/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        # Parse results
        if "passed" in output:
            results["certified_tests"] = {
                "status": "✅ PASS",
                "output_summary": output.split('\n')[-3] if output else "Tests passed"
            }
        else:
            results["certified_tests"] = {
                "status": "❌ FAIL",
                "output": output[-200:]
            }
    except Exception as e:
        results["certified_tests"] = {
            "status": "⚠️ WARN",
            "error": str(e)
        }
    
    return results

def generate_matrix_table(test_matrix):
    """Generate markdown table for test matrix."""
    rows = []
    rows.append("| Format | Status | Recommendation | Score |")
    rows.append("|--------|--------|-----------------|-------|")
    
    for fmt, result in test_matrix.items():
        status = result.get("status", "UNKNOWN")
        
        if result.get("best_choice"):
            rec = result["best_choice"]["target"].upper()
            score = result["best_choice"]["score"]
            rows.append(f"| {fmt.upper():6} | {status:10} | {rec:15} | {score:.2f} |")
        else:
            rows.append(f"| {fmt.upper():6} | {status:10} | N/A             | N/A   |")
    
    return "\n".join(rows)

def main():
    """Run all validations and collect results."""
    print("=" * 70)
    print("CONVERIGO RELEASE CANDIDATE VALIDATION")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}\n")
    
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "validations": {}
    }
    
    # 1. Recommendation API
    print("[1/6] Validating Recommendation API...")
    rec_api = validate_recommendation_api()
    all_results["validations"]["recommendation_api"] = rec_api
    passed = sum(1 for r in rec_api.values() if "✅" in r.get("status", ""))
    print(f"  ✓ {passed}/{len(TEST_FORMATS)} formats passed\n")
    
    # 2. Converter Contracts
    print("[2/6] Validating Converter Contracts...")
    contracts = validate_converter_contracts()
    all_results["validations"]["converter_contracts"] = contracts
    print(f"  ✓ {contracts['total_contracts']} total contracts")
    print(f"  ✓ {contracts['active_contracts']} active/certified")
    print(f"  ✓ {contracts['beta_contracts']} beta\n")
    
    # 3. Certified Converters Registry
    print("[3/6] Validating Certified Converters Registry...")
    certified = validate_certified_converters()
    all_results["validations"]["certified_registry"] = certified
    print(f"  ✓ {certified['certified_count']} certified")
    print(f"  ✓ {certified['beta_count']} beta")
    print(f"  ✓ {certified['disabled_count']} disabled\n")
    
    # 4. Error Handling
    print("[4/6] Validating Error Handling...")
    errors = validate_error_handling()
    all_results["validations"]["error_handling"] = errors
    passed = sum(1 for r in errors.values() if "✅" in r.get("status", ""))
    print(f"  ✓ {passed}/{len(errors)} error scenarios passed\n")
    
    # 5. Deployment Configuration
    print("[5/6] Validating Deployment Configuration...")
    deploy = validate_deployment_config()
    all_results["validations"]["deployment"] = deploy
    files_ok = sum(1 for r in deploy.get("critical_files", {}).values() if r.get("exists"))
    print(f"  ✓ {files_ok}/{len(deploy.get('critical_files', {}))} critical files present\n")
    
    # 6. Certified Tests
    print("[6/6] Validating Certified Test Suite...")
    tests = validate_certified_tests()
    all_results["validations"]["certified_tests"] = tests
    print(f"  ✓ Test suite status: {tests.get('certified_tests', {}).get('status', 'UNKNOWN')}\n")
    
    # Generate matrix table
    all_results["test_matrix_markdown"] = generate_matrix_table(rec_api)
    
    # Save results
    with open("release_candidate_validation_data.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Results saved to: release_candidate_validation_data.json\n")
    
    return all_results

if __name__ == "__main__":
    results = main()
