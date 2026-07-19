#!/usr/bin/env python3
"""
Test conversion fixes
"""
from pathlib import Path
from PIL import Image
import sys

def create_test_jpg(filename):
    """Create test JPEG file"""
    img = Image.new('RGB', (100, 100), color='red')
    img.save(filename, 'JPEG')

def test_conversions():
    """Test all conversion cases"""
    from app.main import app
    from starlette.testclient import TestClient
    
    client = TestClient(app)
    
    # Create test files
    create_test_jpg('test_single.jpg')
    create_test_jpg('test_multi_1.jpg')
    create_test_jpg('test_multi_2.jpg')
    create_test_jpg('test_multi_3.jpg')
    
    try:
        # CASE A: Single JPG -> PNG
        print("\n" + "="*60)
        print("CASE A: Single JPG -> PNG")
        print("="*60)
        with open('test_single.jpg', 'rb') as f:
            response = client.post(
                '/convert',
                data={'target_format': 'png'},
                files={'file': ('test_single.jpg', f, 'image/jpeg')}
            )
            print(f"Status: {response.status_code}")
            result = response.json()
            if response.status_code == 201:
                total = result.get('total', 0)
                success = result.get('successful', 0)
                print(f"SUCCESS: {success}/{total} files converted")
                print(f"Response: {result}")
            else:
                print(f"FAILED: {result}")
        
        # CASE B: Multiple JPG -> PNG (3 files)
        print("\n" + "="*60)
        print("CASE B: Multiple JPG -> PNG (3 files)")
        print("="*60)
        files = [
            ('file', ('test_multi_1.jpg', open('test_multi_1.jpg', 'rb'))),
            ('file', ('test_multi_2.jpg', open('test_multi_2.jpg', 'rb'))),
            ('file', ('test_multi_3.jpg', open('test_multi_3.jpg', 'rb'))),
        ]
        response = client.post(
            '/convert',
            data={'target_format': 'png'},
            files=files
        )
        for f in files:
            f[1][1].close()
        
        print(f"Status: {response.status_code}")
        result = response.json()
        if response.status_code == 201:
            total = result.get('total', 0)
            success = result.get('successful', 0)
            print(f"SUCCESS: {success}/{total} files converted")
            print(f"Response: {result}")
        else:
            print(f"FAILED: {result}")
            
        # CASE C: Single JPG -> PDF
        print("\n" + "="*60)
        print("CASE C: Single JPG -> PDF")
        print("="*60)
        with open('test_single.jpg', 'rb') as f:
            response = client.post(
                '/convert',
                data={'target_format': 'pdf'},
                files={'file': ('test_single.jpg', f, 'image/jpeg')}
            )
            print(f"Status: {response.status_code}")
            result = response.json()
            if response.status_code == 201:
                total = result.get('total', 0)
                success = result.get('successful', 0)
                print(f"SUCCESS: {success}/{total} files converted")
                print(f"Response: {result}")
            else:
                print(f"FAILED: {result}")
                
    finally:
        # Clean up
        for p in Path('.').glob('test_*.jpg'):
            try:
                p.unlink()
            except:
                pass

if __name__ == '__main__':
    test_conversions()
