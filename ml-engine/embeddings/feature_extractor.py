"""
DupeFinder ML Engine - Feature Extraction Module
Task 2.3: Extract embeddings from images using pre-trained ResNet50

This module handles:
- Loading pre-trained ResNet50 model
- Extracting 2048-dimensional feature embeddings
- Batch processing for multiple images
- Saving/loading embeddings to/from disk
- Device management (CPU/GPU)
"""

import torch
import torch.nn as nn
import torchvision.models as models
from pathlib import Path
import numpy as np
import pickle
from typing import Union, List, Dict, Tuple
import time
from tqdm import tqdm

# Import preprocessing from parent package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from preprocessing.image_preprocessor import ImagePreprocessor


class FeatureExtractor:
    """
    Extracts deep feature embeddings from images using pre-trained ResNet50.
    
    The model's final classification layer is removed to extract 2048-dimensional
    feature vectors that represent the semantic content of images.
    """
    
    def __init__(
        self,
        model_name: str = 'resnet50',
        device: str = 'auto',
        use_pretrained: bool = True
    ):
        """
        Initialize the feature extractor.
        
        Args:
            model_name: Name of the model architecture (default: 'resnet50')
            device: Device to use ('cuda', 'cpu', 'mps', or 'auto' for auto-detection)
            use_pretrained: Whether to use pre-trained weights
        """
        self.model_name = model_name
        self.device = self._setup_device(device)
        self.preprocessor = ImagePreprocessor()
        
        print(f"[INFO] Initializing FeatureExtractor with {model_name} on {self.device}")
        
        # Load model
        self.model = self._load_model(use_pretrained)
        self.embedding_dim = self._get_embedding_dimension()
        
        print(f"[INFO] Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def _setup_device(self, device: str) -> torch.device:
        """
        Setup computing device (CPU, CUDA GPU, or Apple Silicon MPS).
        
        Args:
            device: Device specification or 'auto'
        
        Returns:
            torch.device object
        """
        if device == 'auto':
            if torch.cuda.is_available():
                device = 'cuda'
                print(f"[INFO] CUDA GPU detected: {torch.cuda.get_device_name(0)}")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = 'mps'
                print(f"[INFO] Apple Silicon (MPS) detected")
            else:
                device = 'cpu'
                print(f"[INFO] Using CPU")
        
        return torch.device(device)
    
    def _load_model(self, use_pretrained: bool) -> nn.Module:
        """
        Load pre-trained ResNet50 model and remove classification layer.
        
        Args:
            use_pretrained: Whether to load pre-trained weights
        
        Returns:
            Modified ResNet50 model for feature extraction
        """
        print(f"[INFO] Loading {self.model_name} model...")
        start_time = time.time()
        
        # Load ResNet50
        if use_pretrained:
            model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        else:
            model = models.resnet50(weights=None)
        
        # Remove the final fully connected layer (classification head)
        # ResNet50 structure: ... -> avgpool -> fc (1000 classes)
        # We want features before the fc layer (2048-dim)
        model = nn.Sequential(*list(model.children())[:-1])
        
        # Move model to device
        model = model.to(self.device)
        
        # Set to evaluation mode (disable dropout, batch norm in eval mode)
        model.eval()
        
        load_time = time.time() - start_time
        print(f"[INFO] Model loaded in {load_time:.2f} seconds")
        
        return model
    
    def _get_embedding_dimension(self) -> int:
        """
        Get the embedding dimension by running a test input through the model.
        
        Returns:
            Integer dimension of embedding vector
        """
        # Create dummy input
        dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
        
        with torch.no_grad():
            embedding = self.model(dummy_input)
        
        # Flatten to get dimension
        embedding = embedding.squeeze()
        return embedding.shape[0]
    
    def extract_from_tensor(
        self,
        image_tensor: torch.Tensor
    ) -> np.ndarray:
        """
        Extract embedding from a preprocessed image tensor.
        
        Args:
            image_tensor: Preprocessed image tensor of shape (3, 224, 224)
        
        Returns:
            Numpy array of shape (2048,) containing the embedding
        """
        # Add batch dimension if needed
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)  # (1, 3, 224, 224)
        
        # Move to device
        image_tensor = image_tensor.to(self.device)
        
        # Extract features
        with torch.no_grad():
            embedding = self.model(image_tensor)
        
        # Remove extra dimensions and convert to numpy
        embedding = embedding.squeeze().cpu().numpy()
        
        return embedding
    
    def extract_from_path(
        self,
        image_path: Union[str, Path]
    ) -> np.ndarray:
        """
        Extract embedding from an image file.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Numpy array of shape (2048,) containing the embedding
        """
        # Preprocess image
        image_tensor = self.preprocessor.preprocess_from_path(image_path)
        
        # Extract embedding
        embedding = self.extract_from_tensor(image_tensor)
        
        return embedding
    
    def extract_from_bytes(
        self,
        image_bytes: bytes
    ) -> np.ndarray:
        """
        Extract embedding from image bytes.
        
        Args:
            image_bytes: Raw image bytes
        
        Returns:
            Numpy array of shape (2048,) containing the embedding
        """
        # Preprocess image
        image_tensor = self.preprocessor.preprocess_from_bytes(image_bytes)
        
        # Extract embedding
        embedding = self.extract_from_tensor(image_tensor)
        
        return embedding
    
    def extract_batch(
        self,
        image_paths: List[Union[str, Path]],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Extract embeddings from multiple images in batches.
        
        Args:
            image_paths: List of paths to image files
            batch_size: Number of images to process at once
            show_progress: Whether to show progress bar
        
        Returns:
            Numpy array of shape (N, 2048) where N = len(image_paths)
        """
        embeddings = []
        
        # Create batches
        num_batches = (len(image_paths) + batch_size - 1) // batch_size
        
        iterator = range(0, len(image_paths), batch_size)
        if show_progress:
            iterator = tqdm(iterator, total=num_batches, desc="Extracting embeddings")
        
        for i in iterator:
            batch_paths = image_paths[i:i + batch_size]
            
            # Preprocess batch
            batch_tensors = []
            for path in batch_paths:
                try:
                    tensor = self.preprocessor.preprocess_from_path(path)
                    batch_tensors.append(tensor)
                except Exception as e:
                    print(f"[WARNING] Failed to process {path}: {e}")
                    # Add zero vector for failed images
                    batch_tensors.append(torch.zeros(3, 224, 224))
            
            # Stack into batch
            batch = torch.stack(batch_tensors).to(self.device)
            
            # Extract features
            with torch.no_grad():
                batch_embeddings = self.model(batch)
            
            # Convert to numpy
            batch_embeddings = batch_embeddings.squeeze().cpu().numpy()
            
            # Handle single image case
            if batch_embeddings.ndim == 1:
                batch_embeddings = batch_embeddings.reshape(1, -1)
            
            embeddings.append(batch_embeddings)
        
        # Concatenate all batches
        all_embeddings = np.vstack(embeddings)
        
        return all_embeddings
    
    def extract_and_save(
        self,
        image_paths: List[Union[str, Path]],
        output_path: Union[str, Path],
        batch_size: int = 32,
        save_metadata: bool = True
    ) -> Dict:
        """
        Extract embeddings and save to disk.
        
        Args:
            image_paths: List of paths to image files
            output_path: Path to save embeddings (.npy or .pkl)
            batch_size: Batch size for processing
            save_metadata: Whether to save metadata (paths, timestamps, etc.)
        
        Returns:
            Dictionary with extraction statistics
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"[INFO] Extracting embeddings from {len(image_paths)} images...")
        start_time = time.time()
        
        # Extract embeddings
        embeddings = self.extract_batch(image_paths, batch_size=batch_size)
        
        extraction_time = time.time() - start_time
        
        # Prepare data to save
        if save_metadata:
            data = {
                'embeddings': embeddings,
                'image_paths': [str(p) for p in image_paths],
                'model_name': self.model_name,
                'embedding_dim': self.embedding_dim,
                'num_images': len(image_paths),
                'extraction_time': extraction_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            # Save as pickle
            with open(output_path, 'wb') as f:
                pickle.dump(data, f)
            print(f"[INFO] Saved embeddings with metadata to {output_path}")
        else:
            # Save just embeddings as numpy array
            np.save(output_path, embeddings)
            print(f"[INFO] Saved embeddings to {output_path}")
        
        # Return statistics
        stats = {
            'num_images': len(image_paths),
            'embedding_shape': embeddings.shape,
            'extraction_time': extraction_time,
            'avg_time_per_image': extraction_time / len(image_paths),
            'output_path': str(output_path)
        }
        
        print(f"[INFO] Extraction complete:")
        print(f"       - {stats['num_images']} images processed")
        print(f"       - Total time: {stats['extraction_time']:.2f}s")
        print(f"       - Average per image: {stats['avg_time_per_image']*1000:.2f}ms")
        
        return stats
    
    @staticmethod
    def load_embeddings(file_path: Union[str, Path]) -> Union[np.ndarray, Dict]:
        """
        Load embeddings from disk.
        
        Args:
            file_path: Path to embeddings file (.npy or .pkl)
        
        Returns:
            Numpy array or dictionary with embeddings and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Embeddings file not found: {file_path}")
        
        if file_path.suffix == '.npy':
            # Load numpy array
            embeddings = np.load(file_path)
            return embeddings
        elif file_path.suffix == '.pkl':
            # Load pickle (with metadata)
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            return data
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'device': str(self.device),
            'num_parameters': sum(p.numel() for p in self.model.parameters()),
            'trainable_parameters': sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        }


def create_feature_extractor(
    model_name: str = 'resnet50',
    device: str = 'auto'
) -> FeatureExtractor:
    """
    Factory function to create a FeatureExtractor instance.
    
    Args:
        model_name: Name of the model architecture
        device: Device to use ('cuda', 'cpu', 'mps', or 'auto')
    
    Returns:
        FeatureExtractor instance
    """
    return FeatureExtractor(model_name=model_name, device=device)


# Convenience function for quick embedding extraction
def extract_embedding(image_path: Union[str, Path]) -> np.ndarray:
    """
    Quick function to extract embedding from a single image.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Numpy array of shape (2048,) containing the embedding
    """
    extractor = FeatureExtractor()
    return extractor.extract_from_path(image_path)









