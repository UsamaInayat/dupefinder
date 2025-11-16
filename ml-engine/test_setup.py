"""
DupeFinder ML Engine - Setup Verification Test
Task 2.1: Verify ML environment and dependencies are correctly installed

This script tests:
1. All required libraries can be imported
2. Pre-trained ResNet50 model can be loaded
3. Model can perform inference on a test image
4. Device (GPU/CPU) is properly detected
"""

import sys
import time

def test_imports():
    """Test that all required libraries can be imported"""
    print("=" * 60)
    print("TEST 1: Verifying Library Imports")
    print("=" * 60)
    
    try:
        import torch
        print(f"[OK] PyTorch {torch.__version__} imported successfully")
        
        import torchvision
        print(f"[OK] TorchVision {torchvision.__version__} imported successfully")
        
        from PIL import Image
        print(f"[OK] Pillow (PIL) imported successfully")
        
        import numpy as np
        print(f"[OK] NumPy {np.__version__} imported successfully")
        
        from scipy.spatial.distance import cosine
        print(f"[OK] SciPy (cosine similarity) imported successfully")
        
        import yaml
        print(f"[OK] PyYAML imported successfully")
        
        import cv2
        print(f"[OK] OpenCV {cv2.__version__} imported successfully")
        
        print("\n[SUCCESS] All required libraries imported successfully!\n")
        return True
    except ImportError as e:
        print(f"\n[ERROR] Import Error: {e}")
        print("\nPlease install dependencies using:")
        print("  pip install -r requirements.txt")
        return False


def test_device():
    """Test device availability (CUDA/MPS/CPU)"""
    print("=" * 60)
    print("TEST 2: Detecting Computing Device")
    print("=" * 60)
    
    import torch
    
    if torch.cuda.is_available():
        device = "cuda"
        device_name = torch.cuda.get_device_name(0)
        print(f"[OK] CUDA GPU Available: {device_name}")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"
        print(f"[OK] Apple Metal (MPS) Available")
    else:
        device = "cpu"
        print(f"[OK] Using CPU (GPU not available)")
    
    print(f"  Selected Device: {device}")
    print(f"  PyTorch CUDA Available: {torch.cuda.is_available()}")
    print(f"  Number of CPU Threads: {torch.get_num_threads()}")
    
    print("\n[SUCCESS] Device detection successful!\n")
    return device


def test_model_loading(device):
    """Test loading pre-trained ResNet50 model"""
    print("=" * 60)
    print("TEST 3: Loading Pre-trained ResNet50 Model")
    print("=" * 60)
    
    import torch
    import torchvision.models as models
    
    try:
        print("Loading ResNet50 model (this may take a few moments)...")
        start_time = time.time()
        
        # Load pre-trained ResNet50
        model = models.resnet50(pretrained=True)
        
        # Remove the final classification layer to get embeddings
        model = torch.nn.Sequential(*list(model.children())[:-1])
        
        # Move model to device
        model = model.to(device)
        model.eval()  # Set to evaluation mode
        
        load_time = time.time() - start_time
        
        print(f"[OK] ResNet50 loaded successfully in {load_time:.2f} seconds")
        print(f"  Model moved to device: {device}")
        print(f"  Model in evaluation mode: {not model.training}")
        print(f"  Expected embedding dimension: 2048")
        
        print("\n[SUCCESS] Model loading successful!\n")
        return model
    except Exception as e:
        print(f"\n[ERROR] Error loading model: {e}")
        return None


def test_inference(model, device):
    """Test model inference on a dummy image"""
    print("=" * 60)
    print("TEST 4: Testing Model Inference")
    print("=" * 60)
    
    import torch
    import numpy as np
    from PIL import Image
    from torchvision import transforms
    
    try:
        # Create preprocessing pipeline
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Create a dummy RGB image (224x224x3)
        print("Creating dummy test image (224x224 RGB)...")
        dummy_image = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        )
        
        # Preprocess image
        print("Preprocessing image...")
        input_tensor = preprocess(dummy_image)
        input_batch = input_tensor.unsqueeze(0)  # Add batch dimension
        input_batch = input_batch.to(device)
        
        # Perform inference
        print("Running inference...")
        start_time = time.time()
        
        with torch.no_grad():
            embedding = model(input_batch)
        
        inference_time = time.time() - start_time
        
        # Get embedding as numpy array
        embedding = embedding.squeeze().cpu().numpy()
        
        print(f"[OK] Inference completed in {inference_time*1000:.2f} ms")
        print(f"  Input shape: {input_batch.shape}")
        print(f"  Output embedding shape: {embedding.shape}")
        print(f"  Expected shape: (2048,)")
        print(f"  Embedding sample (first 5 values): {embedding[:5]}")
        
        # Verify embedding dimension
        if embedding.shape == (2048,):
            print("\n[SUCCESS] Inference test successful! Model is working correctly!\n")
            return True
        else:
            print(f"\n[WARNING] Warning: Unexpected embedding shape: {embedding.shape}")
            print("   Expected: (2048,)")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Inference Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_calculation():
    """Test cosine similarity calculation"""
    print("=" * 60)
    print("TEST 5: Testing Similarity Calculation")
    print("=" * 60)
    
    import numpy as np
    from scipy.spatial.distance import cosine
    
    try:
        # Create two random embeddings
        embedding1 = np.random.randn(2048)
        embedding2 = np.random.randn(2048)
        
        # Normalize embeddings
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        cosine_distance = cosine(embedding1, embedding2)
        cosine_similarity = 1 - cosine_distance
        
        print(f"[OK] Cosine similarity calculated successfully")
        print(f"  Embedding 1 shape: {embedding1.shape}")
        print(f"  Embedding 2 shape: {embedding2.shape}")
        print(f"  Cosine distance: {cosine_distance:.4f}")
        print(f"  Cosine similarity: {cosine_similarity:.4f}")
        print(f"  Similarity range: [-1, 1] (higher = more similar)")
        
        print("\n[SUCCESS] Similarity calculation test successful!\n")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Similarity calculation error: {e}")
        return False


def main():
    """Run all setup verification tests"""
    print("\n" + "=" * 60)
    print("DupeFinder ML Engine - Setup Verification")
    print("Task 2.1: Testing ML Environment Setup")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Test 1: Imports
    results['imports'] = test_imports()
    if not results['imports']:
        print("\n[FAILED] Setup verification failed at imports!")
        print("Please install dependencies first: pip install -r requirements.txt")
        sys.exit(1)
    
    # Test 2: Device Detection
    try:
        device = test_device()
        results['device'] = True
    except Exception as e:
        print(f"[FAILED] Device detection failed: {e}")
        results['device'] = False
        sys.exit(1)
    
    # Test 3: Model Loading
    model = test_model_loading(device)
    results['model_loading'] = model is not None
    if not results['model_loading']:
        print("\n[FAILED] Setup verification failed at model loading!")
        sys.exit(1)
    
    # Test 4: Inference
    results['inference'] = test_inference(model, device)
    if not results['inference']:
        print("\n[FAILED] Setup verification failed at inference!")
        sys.exit(1)
    
    # Test 5: Similarity Calculation
    results['similarity'] = test_similarity_calculation()
    
    # Final Summary
    print("=" * 60)
    print("FINAL RESULTS - Setup Verification Summary")
    print("=" * 60)
    print(f"[OK] Library Imports:        {'PASS' if results['imports'] else 'FAIL'}")
    print(f"[OK] Device Detection:       {'PASS' if results['device'] else 'FAIL'}")
    print(f"[OK] Model Loading:          {'PASS' if results['model_loading'] else 'FAIL'}")
    print(f"[OK] Model Inference:        {'PASS' if results['inference'] else 'FAIL'}")
    print(f"[OK] Similarity Calculation: {'PASS' if results['similarity'] else 'FAIL'}")
    print("=" * 60)
    
    if all(results.values()):
        print("\n*** SUCCESS! All tests passed! ***")
        print("\n[COMPLETE] Task 2.1 Complete: ML environment is ready!")
        print("   - PyTorch and dependencies installed")
        print("   - Pre-trained ResNet50 model loads successfully")
        print("   - Model can extract embeddings (2048-dim)")
        print("   - Cosine similarity calculation works")
        print("\nYou can now proceed to Task 2.2: Image Preprocessing Pipeline")
        return 0
    else:
        print("\n[FAILED] Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

