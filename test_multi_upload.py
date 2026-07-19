#!/usr/bin/env python3
"""
Test multi-file upload flow
Verifies whether multiple files are accepted and processed
"""

from fastapi.testclient import TestClient
from pathlib import Path
import io

from app.main import app

client = TestClient(app)

def test_single_file_upload():
    """Test single file upload baseline"""
    file_data = io.BytesIO(b"fake jpg content")
    files = [("file", ("test1.jpg", file_data, "image/jpeg"))]
    
    response = client.post(
        "/upload",
        files=files,
    )
    print("\n=== Single File Upload ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"


def test_multi_file_upload_sequential():
    """Test uploading multiple files sequentially - mimics frontend loop"""
    print("\n=== Multi File Upload (Sequential) ===")
    
    files_to_upload = [
        ("test1.jpg", b"fake jpg 1"),
        ("test2.jpg", b"fake jpg 2"),
        ("test3.jpg", b"fake jpg 3"),
    ]
    
    results = []
    for filename, content in files_to_upload:
        file_data = io.BytesIO(content)
        files = [("file", (filename, file_data, "image/jpeg"))]
        
        response = client.post("/upload", files=files)
        print(f"  File: {filename} - Status: {response.status_code}")
        if response.status_code == 201:
            results.append(True)
        else:
            results.append(False)
            print(f"    Error: {response.json()}")
    
    print(f"Results: {sum(results)}/{len(results)} files uploaded")
    assert all(results), "Not all files uploaded successfully"


def test_multi_file_convert():
    """Test converting multiple files - this is where the regression likely is"""
    print("\n=== Multi File Convert ===")
    
    # Simulating what the frontend would send
    # The regression is likely here: frontend only sends one file to /convert
    
    file_data1 = io.BytesIO(b"\xff\xd8\xff")  # jpg signature
    file_data2 = io.BytesIO(b"\xff\xd8\xff")
    file_data3 = io.BytesIO(b"\xff\xd8\xff")
    
    # Test 1: Try sending multiple files in one request
    print("  Attempting multi-file convert in single request...")
    files = [
        ("file", ("test1.jpg", file_data1, "image/jpeg")),
        ("file", ("test2.jpg", file_data2, "image/jpeg")),
        ("file", ("test3.jpg", file_data3, "image/jpeg")),
    ]
    
    response = client.post(
        "/convert",
        files=files,
        data={"target_format": "png"}
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    # The backend endpoint currently only accepts single file
    # This will likely fail or only process the first file
    

if __name__ == "__main__":
    print("Testing multi-upload regression...")
    
    try:
        test_single_file_upload()
    except AssertionError as e:
        print(f"FAIL: {e}")
    
    try:
        test_multi_file_upload_sequential()
    except AssertionError as e:
        print(f"FAIL: {e}")
    
    try:
        test_multi_file_convert()
    except Exception as e:
        print(f"FAIL: {e}")
    
    print("\n=== Test Complete ===")
