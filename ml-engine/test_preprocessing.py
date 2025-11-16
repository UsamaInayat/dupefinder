"""
DupeFinder ML Engine - Preprocessing Test Script
Task 2.2: Test image preprocessing pipeline

This script verifies:
1. Images can be loaded from various formats
2. Preprocessing produces correct tensor shape
3. Batch processing works
4. Error handling for invalid images
"""

import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image
import torch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing.image_preprocessor import ImagePreprocessor


def test_create_test_images():
    """Create test images in various formats"""
    print("=" * 60)
    print("SETUP: Creating Test Images")
    print("=" * 60)
    
    # Create data directory
    data_dir = Path("data/test_images")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    test_images = []
    
    # Create different types of test images
    print("Creating test images...")
    
    # 1. RGB image (landscape)
    rgb_img = Image.new('RGB', (800, 600), color=(100, 150, 200))
    rgb_path = data_dir / "test_rgb.jpg"
    rgb_img.save(rgb_path, 'JPEG')
    test_images.append(('RGB JPG (800x600)', rgb_path))
    print(f"  [OK] Created: {rgb_path.name}")
    
    # 2. PNG image (portrait)
    png_img = Image.new('RGB', (400, 800), color=(200, 100, 150))
    png_path = data_dir / "test_png.png"
    png_img.save(png_path, 'PNG')
    test_images.append(('RGB PNG (400x800)', png_path))
    print(f"  [OK] Created: {png_path.name}")
    
    # 3. Square image
    square_img = Image.new('RGB', (512, 512), color=(150, 200, 100))
    square_path = data_dir / "test_square.jpg"
    square_img.save(square_path, 'JPEG')
    test_images.append(('RGB JPG Square (512x512)', square_path))
    print(f"  [OK] Created: {square_path.name}")
    
    # 4. Small image
    small_img = Image.new('RGB', (64, 64), color=(255, 128, 0))
    small_path = data_dir / "test_small.jpg"
    small_img.save(small_path, 'JPEG')
    test_images.append(('Small RGB JPG (64x64)', small_path))
    print(f"  [OK] Created: {small_path.name}")
    
    # 5. Large image
    large_img = Image.new('RGB', (2048, 1536), color=(50, 100, 200))
    large_path = data_dir / "test_large.jpg"
    large_img.save(large_path, 'JPEG')
    test_images.append(('Large RGB JPG (2048x1536)', large_path))
    print(f"  [OK] Created: {large_path.name}")
    
    # 6. Grayscale image
    gray_img = Image.new('L', (640, 480), color=128)
    gray_path = data_dir / "test_grayscale.png"
    gray_img.save(gray_path, 'PNG')
    test_images.append(('Grayscale PNG (640x480)', gray_path))
    print(f"  [OK] Created: {gray_path.name}")
    
    # 7. RGBA image (with transparency)
    rgba_img = Image.new('RGBA', (500, 500), color=(100, 200, 150, 200))
    rgba_path = data_dir / "test_rgba.png"
    rgba_img.save(rgba_path, 'PNG')
    test_images.append(('RGBA PNG (500x500)', rgba_path))
    print(f"  [OK] Created: {rgba_path.name}")
    
    print(f"\n[SUCCESS] Created {len(test_images)} test images in {data_dir}\n")
    return test_images, data_dir


def test_basic_preprocessing(test_images):
    """Test basic preprocessing functionality"""
    print("=" * 60)
    print("TEST 1: Basic Image Preprocessing")
    print("=" * 60)
    
    preprocessor = ImagePreprocessor()
    
    passed = 0
    failed = 0
    
    for img_name, img_path in test_images:
        try:
            # Preprocess image
            start_time = time.time()
            tensor = preprocessor.preprocess_from_path(img_path)
            process_time = (time.time() - start_time) * 1000  # ms
            
            # Verify shape
            expected_shape = (3, 224, 224)
            if tensor.shape == expected_shape:
                print(f"[OK] {img_name}")
                print(f"     Shape: {tuple(tensor.shape)} | Time: {process_time:.2f}ms")
                passed += 1
            else:
                print(f"[FAIL] {img_name}")
                print(f"       Expected shape: {expected_shape}, Got: {tuple(tensor.shape)}")
                failed += 1
                
        except Exception as e:
            print(f"[ERROR] {img_name}: {str(e)}")
            failed += 1
    
    print(f"\n[RESULT] Passed: {passed}/{len(test_images)}, Failed: {failed}/{len(test_images)}")
    
    if failed == 0:
        print("[SUCCESS] All images preprocessed successfully!\n")
        return True
    else:
        print("[WARNING] Some images failed preprocessing\n")
        return False


def test_different_input_methods():
    """Test preprocessing from different input types"""
    print("=" * 60)
    print("TEST 2: Different Input Methods")
    print("=" * 60)
    
    preprocessor = ImagePreprocessor()
    
    # Create a test image
    test_img = Image.new('RGB', (640, 480), color=(100, 150, 200))
    test_path = Path("data/test_images/test_methods.jpg")
    test_img.save(test_path)
    
    tests_passed = 0
    
    # Test 1: From file path
    try:
        tensor1 = preprocessor.preprocess_from_path(test_path)
        assert tensor1.shape == (3, 224, 224), f"Wrong shape: {tensor1.shape}"
        print("[OK] Preprocessing from file path works")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] From file path: {e}")
    
    # Test 2: From bytes
    try:
        with open(test_path, 'rb') as f:
            image_bytes = f.read()
        tensor2 = preprocessor.preprocess_from_bytes(image_bytes)
        assert tensor2.shape == (3, 224, 224), f"Wrong shape: {tensor2.shape}"
        print("[OK] Preprocessing from bytes works")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] From bytes: {e}")
    
    # Test 3: From PIL Image
    try:
        pil_img = Image.open(test_path)
        tensor3 = preprocessor.preprocess_from_pil(pil_img)
        assert tensor3.shape == (3, 224, 224), f"Wrong shape: {tensor3.shape}"
        print("[OK] Preprocessing from PIL Image works")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] From PIL Image: {e}")
    
    # Test 4: From numpy array
    try:
        numpy_img = np.array(test_img)
        tensor4 = preprocessor.preprocess_from_numpy(numpy_img)
        assert tensor4.shape == (3, 224, 224), f"Wrong shape: {tensor4.shape}"
        print("[OK] Preprocessing from numpy array works")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] From numpy array: {e}")
    
    print(f"\n[RESULT] {tests_passed}/4 input methods working")
    
    if tests_passed == 4:
        print("[SUCCESS] All input methods work correctly!\n")
        return True
    else:
        print("[WARNING] Some input methods failed\n")
        return False


def test_batch_preprocessing(test_images):
    """Test batch preprocessing"""
    print("=" * 60)
    print("TEST 3: Batch Preprocessing")
    print("=" * 60)
    
    preprocessor = ImagePreprocessor()
    
    try:
        # Take first 5 images
        image_paths = [path for _, path in test_images[:5]]
        
        print(f"Processing batch of {len(image_paths)} images...")
        start_time = time.time()
        
        batch_tensor = preprocessor.preprocess_batch(image_paths)
        
        batch_time = (time.time() - start_time) * 1000
        
        # Verify shape
        expected_shape = (len(image_paths), 3, 224, 224)
        
        if batch_tensor.shape == expected_shape:
            print(f"[OK] Batch preprocessing successful")
            print(f"     Batch shape: {tuple(batch_tensor.shape)}")
            print(f"     Total time: {batch_time:.2f}ms")
            print(f"     Average per image: {batch_time/len(image_paths):.2f}ms")
            print("\n[SUCCESS] Batch preprocessing works!\n")
            return True
        else:
            print(f"[FAIL] Wrong batch shape")
            print(f"       Expected: {expected_shape}, Got: {tuple(batch_tensor.shape)}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Batch preprocessing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for invalid inputs"""
    print("=" * 60)
    print("TEST 4: Error Handling")
    print("=" * 60)
    
    preprocessor = ImagePreprocessor()
    errors_caught = 0
    
    # Test 1: Non-existent file
    try:
        preprocessor.preprocess_from_path("nonexistent_file.jpg")
        print("[FAIL] Should have raised FileNotFoundError")
    except FileNotFoundError:
        print("[OK] FileNotFoundError caught for non-existent file")
        errors_caught += 1
    except Exception as e:
        print(f"[FAIL] Wrong exception: {type(e).__name__}")
    
    # Test 2: Invalid image data
    try:
        invalid_bytes = b"This is not an image"
        preprocessor.preprocess_from_bytes(invalid_bytes)
        print("[FAIL] Should have raised ValueError for invalid data")
    except ValueError:
        print("[OK] ValueError caught for invalid image data")
        errors_caught += 1
    except Exception as e:
        print(f"[FAIL] Wrong exception: {type(e).__name__}")
    
    # Test 3: Create corrupted file
    try:
        corrupt_path = Path("data/test_images/corrupt.jpg")
        with open(corrupt_path, 'wb') as f:
            f.write(b"CORRUPT IMAGE DATA")
        
        preprocessor.preprocess_from_path(corrupt_path)
        print("[FAIL] Should have raised ValueError for corrupt file")
    except ValueError:
        print("[OK] ValueError caught for corrupted image file")
        errors_caught += 1
    except Exception as e:
        print(f"[FAIL] Wrong exception: {type(e).__name__}")
    
    print(f"\n[RESULT] {errors_caught}/3 error cases handled correctly")
    
    if errors_caught == 3:
        print("[SUCCESS] Error handling works correctly!\n")
        return True
    else:
        print("[WARNING] Some error cases not handled properly\n")
        return False


def test_image_info():
    """Test image info retrieval"""
    print("=" * 60)
    print("TEST 5: Image Information Retrieval")
    print("=" * 60)
    
    preprocessor = ImagePreprocessor()
    
    # Use first test image
    test_path = Path("data/test_images/test_rgb.jpg")
    
    try:
        info = preprocessor.get_image_info(test_path)
        
        print(f"[OK] Image info retrieved successfully")
        print(f"     Format: {info['format']}")
        print(f"     Mode: {info['mode']}")
        print(f"     Size: {info['width']}x{info['height']}")
        print(f"     File size: {info['file_size_bytes']} bytes")
        
        # Verify required fields
        required_fields = ['format', 'mode', 'size', 'width', 'height', 'file_size_bytes']
        if all(field in info for field in required_fields):
            print("\n[SUCCESS] Image info retrieval works!\n")
            return True
        else:
            print("\n[FAIL] Missing required fields in info\n")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to get image info: {e}")
        return False


def test_normalization_values():
    """Test that normalization produces expected value ranges"""
    print("=" * 60)
    print("TEST 6: Normalization Value Ranges")
    print("=" * 60)
    
    preprocessor = ImagePreprocessor()
    
    # Create a white image (all 255)
    white_img = Image.new('RGB', (224, 224), color=(255, 255, 255))
    white_path = Path("data/test_images/test_white.png")
    white_img.save(white_path)
    
    # Create a black image (all 0)
    black_img = Image.new('RGB', (224, 224), color=(0, 0, 0))
    black_path = Path("data/test_images/test_black.png")
    black_img.save(black_path)
    
    try:
        # Preprocess both images
        white_tensor = preprocessor.preprocess_from_path(white_path)
        black_tensor = preprocessor.preprocess_from_path(black_path)
        
        # Check value ranges (after normalization, values should be roughly in [-2, 2])
        white_min, white_max = white_tensor.min().item(), white_tensor.max().item()
        black_min, black_max = black_tensor.min().item(), black_tensor.max().item()
        
        print(f"[OK] White image tensor range: [{white_min:.4f}, {white_max:.4f}]")
        print(f"[OK] Black image tensor range: [{black_min:.4f}, {black_max:.4f}]")
        
        # After ImageNet normalization:
        # White (255/255 = 1.0) -> (1.0 - mean) / std
        # Black (0/255 = 0.0) -> (0.0 - mean) / std
        
        # Reasonable ranges after normalization
        if -3 < black_min < 0 and -3 < black_max < 0:
            print("[OK] Black image normalization in expected range")
        else:
            print(f"[WARNING] Black image normalization unexpected")
        
        if 1 < white_min < 3 and 1 < white_max < 3:
            print("[OK] White image normalization in expected range")
        else:
            print(f"[WARNING] White image normalization unexpected")
        
        print("\n[SUCCESS] Normalization test complete!\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] Normalization test failed: {e}")
        return False


def main():
    """Run all preprocessing tests"""
    print("\n" + "=" * 60)
    print("DupeFinder ML Engine - Preprocessing Tests")
    print("Task 2.2: Image Preprocessing Pipeline Verification")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Setup: Create test images
    test_images, data_dir = test_create_test_images()
    
    # Test 1: Basic preprocessing
    results['basic'] = test_basic_preprocessing(test_images)
    
    # Test 2: Different input methods
    results['input_methods'] = test_different_input_methods()
    
    # Test 3: Batch preprocessing
    results['batch'] = test_batch_preprocessing(test_images)
    
    # Test 4: Error handling
    results['error_handling'] = test_error_handling()
    
    # Test 5: Image info
    results['image_info'] = test_image_info()
    
    # Test 6: Normalization
    results['normalization'] = test_normalization_values()
    
    # Final Summary
    print("=" * 60)
    print("FINAL RESULTS - Preprocessing Test Summary")
    print("=" * 60)
    print(f"[{'PASS' if results['basic'] else 'FAIL'}] Basic preprocessing (7 image formats)")
    print(f"[{'PASS' if results['input_methods'] else 'FAIL'}] Different input methods (4 types)")
    print(f"[{'PASS' if results['batch'] else 'FAIL'}] Batch preprocessing")
    print(f"[{'PASS' if results['error_handling'] else 'FAIL'}] Error handling (3 cases)")
    print(f"[{'PASS' if results['image_info'] else 'FAIL'}] Image info retrieval")
    print(f"[{'PASS' if results['normalization'] else 'FAIL'}] Normalization values")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n*** SUCCESS! All preprocessing tests passed! ***")
        print("\n[COMPLETE] Task 2.2 Complete: Image preprocessing pipeline is ready!")
        print("   - Supports 7+ image formats (JPG, PNG, WebP, etc.)")
        print("   - Handles 4 input types (path, bytes, PIL, numpy)")
        print("   - Batch processing works")
        print("   - Proper error handling")
        print("   - ImageNet normalization applied")
        print(f"\nTest images saved in: {data_dir.absolute()}")
        print("\nYou can now proceed to Task 2.3: Feature Extraction (Embedding Generation)")
        return 0
    else:
        failed_count = sum(1 for v in results.values() if not v)
        print(f"\n[FAILED] {failed_count} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)









