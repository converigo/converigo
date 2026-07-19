#!/usr/bin/env python3
"""
Multi-Upload Validation Test
Verifies that multiple files (3 JPG) are correctly processed
"""

from fastapi.testclient import TestClient
from pathlib import Path
import io
from PIL import Image

from app.main import app

client = TestClient(app)

def create_test_jpg():
    """Create a valid test JPG file"""
    img = Image.new('RGB', (100, 100), color='red')
    jpg_data = io.BytesIO()
    img.save(jpg_data, format='JPEG')
    jpg_data.seek(0)
    return jpg_data.getvalue()

def test_multi_file_conversion():
    """Test uploading and converting 3 JPG files to PNG"""
    print("\n" + "="*60)
    print("MULTI-UPLOAD VALIDATION TEST")
    print("="*60)
    
    # Create 3 valid JPG files
    jpg_content = create_test_jpg()
    
    # Create form data with proper file handling
    from fastapi import File, Form
    
    files = [
        ("file", ("test1.jpg", io.BytesIO(jpg_content), "image/jpeg")),
        ("file", ("test2.jpg", io.BytesIO(jpg_content), "image/jpeg")),
        ("file", ("test3.jpg", io.BytesIO(jpg_content), "image/jpeg")),
    ]
    data = {"target_format": "png"}
    
    print("\nTest: Upload 3 JPG files for conversion to PNG")
    print("-" * 60)
    
    response = client.post(
        "/convert",
        files=files,
        data={"target_format": "png"}
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"\n✓ Conversion request successful")
        print(f"  Total files: {data.get('total')}")
        print(f"  Successful: {data.get('successful')}")
        print(f"  Status: {data.get('status')}")
        
        results = data.get('results', [])
        print(f"\n  Individual file results:")
        for i, result in enumerate(results, 1):
            filename = result.get('filename', 'unknown')
            status = result.get('status', 'unknown')
            error = result.get('error', '')
            print(f"    File {i}: {filename} - {status}")
            if error:
                print(f"            Error: {error}")
        
        # Validate results
        assert data.get('total') == 3, f"Expected 3 files, got {data.get('total')}"
        assert data.get('successful') == 3, f"Expected 3 successful conversions, got {data.get('successful')}"
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # Verify all files have success status
        for i, result in enumerate(results, 1):
            assert result.get('status') == 'success', f"File {i} failed with error: {result.get('error')}"
            assert 'download_path' in result, f"File {i} missing download_path"
            assert result.get('filename').endswith('.png'), f"File {i} should be PNG format"
        
        print("\n✓ All validation checks passed!")
        print(f"  All 3 files successfully converted to PNG")
        return True
    else:
        print(f"\n❌ Conversion failed")
        print(f"Response: {response.json()}")
        return False

if __name__ == "__main__":
    try:
        success = test_multi_file_conversion()
        if success:
            print("\n" + "="*60)
            print("RESULT: ✓ MULTI-UPLOAD VALIDATION PASSED")
            print("="*60)
            exit(0)
        else:
            print("\n" + "="*60)
            print("RESULT: ❌ MULTI-UPLOAD VALIDATION FAILED")
            print("="*60)
            exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
