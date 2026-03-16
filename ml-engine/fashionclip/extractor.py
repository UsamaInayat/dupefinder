"""
FashionCLIP Feature Extractor (Isolated)

Model : patrickjohncyh/fashion-clip  (CLIP ViT-B/32 fine-tuned on ~700k
        Farfetch fashion images)
Output: 512-dim L2-normalised embeddings — cosine similarity via IndexFlatIP

Public interface (same as ResNet50 FeatureExtractor):
    extract_from_path(path)   -> np.ndarray (512,)
    extract_from_bytes(bytes) -> np.ndarray (512,)
    extract_batch(paths, ...) -> np.ndarray (N, 512)

Bug note: CLIPModel.get_image_features() for this checkpoint returns a
BaseModelOutputWithPooling object, not a plain tensor. We use
vision_model + visual_projection explicitly to avoid this.
"""

import time
from io import BytesIO
from pathlib import Path
from typing import List, Union

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm
from transformers import CLIPModel, CLIPProcessor

MODEL_ID = "patrickjohncyh/fashion-clip"


class FashionCLIPExtractor:
    """
    Extracts 512-dim fashion embeddings using FashionCLIP (ViT-B/32).
    Vectors are L2-normalised — inner product == cosine similarity,
    compatible with faiss.IndexFlatIP.
    """

    def __init__(self, device: str = "auto"):
        self.device       = self._resolve_device(device)
        self.embedding_dim = 512

        print(f"[INFO] Loading FashionCLIP '{MODEL_ID}' on {self.device} ...")
        t0 = time.time()
        self.processor = CLIPProcessor.from_pretrained(MODEL_ID)
        self.model     = CLIPModel.from_pretrained(MODEL_ID).to(self.device)
        self.model.eval()
        print(f"[OK]  FashionCLIP loaded in {time.time()-t0:.1f}s  "
              f"| embedding_dim={self.embedding_dim}  | device={self.device}")

    # ── Device ────────────────────────────────────────────────────────────────

    def _resolve_device(self, device: str) -> torch.device:
        if device == "auto":
            if torch.cuda.is_available():
                print(f"[INFO] CUDA GPU: {torch.cuda.get_device_name(0)}")
                device = "cuda"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                print("[INFO] Apple Silicon (MPS) detected")
                device = "mps"
            else:
                print("[INFO] Using CPU")
                device = "cpu"
        return torch.device(device)

    # ── Core extraction ───────────────────────────────────────────────────────

    def _extract_pil(self, images: List[Image.Image]) -> np.ndarray:
        """
        Given a list of PIL Images returns L2-normalised (N, 512) float32.
        Uses vision_model + visual_projection explicitly to avoid the
        BaseModelOutputWithPooling bug in get_image_features().
        """
        inputs       = self.processor(images=images, return_tensors="pt", padding=True)
        pixel_values = inputs["pixel_values"].to(self.device)

        with torch.no_grad():
            vision_out = self.model.vision_model(pixel_values=pixel_values)
            pooled     = vision_out.pooler_output            # (N, hidden_dim)
            vecs       = self.model.visual_projection(pooled) # (N, 512)

        vecs = vecs / vecs.norm(dim=-1, keepdim=True)
        return vecs.cpu().float().numpy()

    @staticmethod
    def _load_pil(source: Union[str, Path, bytes]) -> Image.Image:
        if isinstance(source, (str, Path)):
            return Image.open(source).convert("RGB")
        return Image.open(BytesIO(source)).convert("RGB")

    # ── Public interface ──────────────────────────────────────────────────────

    def extract_from_path(self, image_path: Union[str, Path]) -> np.ndarray:
        return self._extract_pil([self._load_pil(image_path)])[0]

    def extract_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        return self._extract_pil([self._load_pil(image_bytes)])[0]

    def extract_batch(
        self,
        image_paths: List[Union[str, Path]],
        batch_size:  int  = 64,
        show_progress: bool = True,
    ) -> np.ndarray:
        """Extract embeddings for a list of image paths (CPU fallback, no DataLoader)."""
        all_vecs: List[np.ndarray] = []
        n_batches = (len(image_paths) + batch_size - 1) // batch_size
        it = range(0, len(image_paths), batch_size)
        if show_progress:
            it = tqdm(it, total=n_batches, desc="FashionCLIP embeddings")

        for i in it:
            batch = image_paths[i : i + batch_size]
            pils  = []
            for p in batch:
                try:
                    pils.append(self._load_pil(p))
                except Exception as exc:
                    print(f"[WARNING] Could not load {p}: {exc} — blank image used")
                    pils.append(Image.new("RGB", (224, 224)))
            all_vecs.append(self._extract_pil(pils))

        return np.vstack(all_vecs)

    def info(self) -> dict:
        return {
            "model":         MODEL_ID,
            "embedding_dim": self.embedding_dim,
            "device":        str(self.device),
        }
