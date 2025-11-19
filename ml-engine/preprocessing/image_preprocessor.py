"""
DupeFinder ML Engine - Image Preprocessing Module
Task 2.2: Image preprocessing pipeline for ResNet50

This module handles:
- Loading images from file paths or file objects
- Resizing to standard dimensions (224x224)
- Normalizing pixel values using ImageNet mean/std
- Converting to PyTorch tensors
- Handling various image formats (JPG, PNG, WebP, etc.)
- Error handling for invalid/corrupted images
"""

from PIL import Image
import torch
from torchvision import transforms
import numpy as np
from pathlib import Path
from typing import Union, Tuple
import io


class ImagePreprocessor:
    """
    Preprocesses images for ResNet50 model inference.
    
    Uses standard ImageNet preprocessing:
    - Resize to 224x224
    - Convert to RGB (handle grayscale, RGBA, etc.)
    - Normalize with mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    """
    
    # ImageNet normalization parameters
    IMAGENET_MEAN = [0.485, 0.456, 0.406]
    IMAGENET_STD = [0.229, 0.224, 0.225]
    
    # Target size for ResNet50
    TARGET_SIZE = (224, 224)
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff'}
    
    def __init__(self, target_size: Tuple[int, int] = None):
        """
        Initialize the image preprocessor.
        
        Args:
            target_size: Tuple of (height, width). Defaults to (224, 224)
        """
        self.target_size = target_size or self.TARGET_SIZE
        
        # Create preprocessing pipeline
        self.transform = transforms.Compose([
            transforms.Resize(256),  # Resize shortest side to 256
            transforms.CenterCrop(self.target_size),  # Center crop to 224x224
            transforms.ToTensor(),  # Convert to tensor [0, 1]
            transforms.Normalize(
                mean=self.IMAGENET_MEAN,
                std=self.IMAGENET_STD
            )
        ])
        
        # Alternative: Direct resize (faster, but may distort aspect ratio)
        self.transform_fast = transforms.Compose([
            transforms.Resize(self.target_size),  # Direct resize
            transforms.ToTensor(),
            transforms.Normalize(
                mean=self.IMAGENET_MEAN,
                std=self.IMAGENET_STD
            )
        ])
    
    def preprocess_from_path(
        self, 
        image_path: Union[str, Path],
        use_fast: bool = False
    ) -> torch.Tensor:
        """
        Load and preprocess an image from a file path.
        
        Args:
            image_path: Path to the image file
            use_fast: If True, use faster direct resize (may distort aspect ratio)
        
        Returns:
            Preprocessed image tensor of shape (3, 224, 224)
        
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image format is not supported or image is corrupted
        """
        image_path = Path(image_path)
        
        # Check file exists
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Check file extension
        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported image format: {image_path.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Preprocess
            return self._preprocess_image(image, use_fast)
            
        except Exception as e:
            raise ValueError(f"Failed to load/process image {image_path}: {str(e)}")
    
    def preprocess_from_bytes(
        self,
        image_bytes: bytes,
        use_fast: bool = False
    ) -> torch.Tensor:
        """
        Load and preprocess an image from bytes (e.g., uploaded file).
        
        Args:
            image_bytes: Raw image bytes
            use_fast: If True, use faster direct resize
        
        Returns:
            Preprocessed image tensor of shape (3, 224, 224)
        
        Raises:
            ValueError: If image cannot be decoded or is corrupted
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Preprocess
            return self._preprocess_image(image, use_fast)
            
        except Exception as e:
            raise ValueError(f"Failed to decode/process image from bytes: {str(e)}")
    
    def preprocess_from_pil(
        self,
        image: Image.Image,
        use_fast: bool = False
    ) -> torch.Tensor:
        """
        Preprocess a PIL Image object.
        
        Args:
            image: PIL Image object
            use_fast: If True, use faster direct resize
        
        Returns:
            Preprocessed image tensor of shape (3, 224, 224)
        
        Raises:
            ValueError: If preprocessing fails
        """
        try:
            return self._preprocess_image(image, use_fast)
        except Exception as e:
            raise ValueError(f"Failed to preprocess PIL image: {str(e)}")
    
    def preprocess_from_numpy(
        self,
        image_array: np.ndarray,
        use_fast: bool = False
    ) -> torch.Tensor:
        """
        Preprocess a numpy array image (H, W, C) with values in [0, 255].
        
        Args:
            image_array: Numpy array of shape (H, W, C)
            use_fast: If True, use faster direct resize
        
        Returns:
            Preprocessed image tensor of shape (3, 224, 224)
        
        Raises:
            ValueError: If array format is invalid
        """
        try:
            # Convert numpy array to PIL Image
            if image_array.dtype != np.uint8:
                # Normalize to [0, 255] if needed
                if image_array.max() <= 1.0:
                    image_array = (image_array * 255).astype(np.uint8)
                else:
                    image_array = image_array.astype(np.uint8)
            
            image = Image.fromarray(image_array)
            return self._preprocess_image(image, use_fast)
            
        except Exception as e:
            raise ValueError(f"Failed to preprocess numpy array: {str(e)}")
    
    def _preprocess_image(
        self,
        image: Image.Image,
        use_fast: bool = False
    ) -> torch.Tensor:
        """
        Internal method to preprocess a PIL Image.
        
        Args:
            image: PIL Image object
            use_fast: If True, use faster direct resize
        
        Returns:
            Preprocessed image tensor of shape (3, 224, 224)
        """
        # Convert to RGB (handles grayscale, RGBA, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Apply transformations
        transform = self.transform_fast if use_fast else self.transform
        tensor = transform(image)
        
        return tensor
    
    def preprocess_batch(
        self,
        image_paths: list,
        use_fast: bool = False
    ) -> torch.Tensor:
        """
        Preprocess a batch of images from file paths.
        
        Args:
            image_paths: List of image file paths
            use_fast: If True, use faster direct resize
        
        Returns:
            Batch tensor of shape (N, 3, 224, 224) where N = len(image_paths)
        
        Raises:
            ValueError: If any image fails to load/process
        """
        tensors = []
        
        for path in image_paths:
            tensor = self.preprocess_from_path(path, use_fast)
            tensors.append(tensor)
        
        # Stack into batch
        batch = torch.stack(tensors)
        return batch
    
    def get_image_info(self, image_path: Union[str, Path]) -> dict:
        """
        Get information about an image without preprocessing.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dictionary with image metadata (size, format, mode)
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            with Image.open(image_path) as img:
                return {
                    'path': str(image_path),
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,  # (width, height)
                    'width': img.size[0],
                    'height': img.size[1],
                    'file_size_bytes': image_path.stat().st_size
                }
        except Exception as e:
            raise ValueError(f"Failed to read image info: {str(e)}")
    
    @staticmethod
    def denormalize_tensor(
        tensor: torch.Tensor,
        mean: list = None,
        std: list = None
    ) -> torch.Tensor:
        """
        Denormalize a tensor back to [0, 1] range for visualization.
        
        Args:
            tensor: Normalized tensor of shape (C, H, W)
            mean: Mean values used for normalization
            std: Std values used for normalization
        
        Returns:
            Denormalized tensor in [0, 1] range
        """
        mean = mean or ImagePreprocessor.IMAGENET_MEAN
        std = std or ImagePreprocessor.IMAGENET_STD
        
        # Create tensors for mean and std
        mean_tensor = torch.tensor(mean).view(3, 1, 1)
        std_tensor = torch.tensor(std).view(3, 1, 1)
        
        # Denormalize: x_original = x_normalized * std + mean
        denormalized = tensor * std_tensor + mean_tensor
        
        # Clip to [0, 1]
        denormalized = torch.clamp(denormalized, 0, 1)
        
        return denormalized


def create_preprocessor(target_size: Tuple[int, int] = None) -> ImagePreprocessor:
    """
    Factory function to create an ImagePreprocessor instance.
    
    Args:
        target_size: Target image size (height, width). Defaults to (224, 224)
    
    Returns:
        ImagePreprocessor instance
    """
    return ImagePreprocessor(target_size=target_size)


# Convenience function for quick preprocessing
def preprocess_image(image_path: Union[str, Path]) -> torch.Tensor:
    """
    Quick function to preprocess a single image.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Preprocessed tensor of shape (3, 224, 224)
    """
    preprocessor = ImagePreprocessor()
    return preprocessor.preprocess_from_path(image_path)









