# DupeFinder ML Engine

Machine Learning engine for image similarity and product matching.

**Current Status**: Phase 2 - ML Engine Proof of Concept (40% Milestone)

## Features (40% Milestone)

- ✅ Pre-trained ResNet50 for feature extraction
- ✅ Image preprocessing pipeline
- ✅ 2048-dimensional embedding generation
- ✅ Cosine similarity-based search
- 🔄 Simple numpy/scipy similarity (FAISS deferred to 60%)
- 🔄 Pre-trained models only (fine-tuning deferred to 60%)

## Features (Planned for 60-100%)

- FAISS-based similarity search for scalability
- Model fine-tuning on fashion datasets
- Advanced preprocessing (background removal)
- Batch processing optimization
- Multi-modal search (image + text)

## Project Structure

```
ml-engine/
├── models/                 # Trained model files
├── preprocessing/          # Image preprocessing modules
├── embeddings/            # Embedding generation
├── similarity/            # Similarity search logic
├── data/                  # Training data and indices
├── tests/                 # Test files
├── config.yaml            # Configuration
└── requirements.txt       # Dependencies
```

## Setup Instructions

### Task 2.1: ML Environment Setup

**Prerequisites:**
- Python 3.8+ (3.10+ recommended)
- CUDA-capable GPU (optional, for faster processing)
- 2GB+ free disk space for PyTorch

### Quick Setup (Automated)

Run the automated setup script:

```bash
# Navigate to ml-engine directory
cd ml-engine

# Run automated setup
python setup_ml_env.py
```

This will:
1. Check Python version
2. Install all dependencies from requirements.txt
3. Download pre-trained ResNet50 model automatically
4. Run verification tests
5. Confirm everything works

### Manual Setup

If you prefer manual installation:

**1. Create virtual environment (recommended):**

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

**3. Verify setup:**

```bash
python test_setup.py
```

Expected output:
```
✓ All required libraries imported successfully
✓ Device detection successful (CUDA/MPS/CPU)
✓ ResNet50 loaded successfully
✓ Model inference working (2048-dim embeddings)
✓ Cosine similarity calculation working
🎉 SUCCESS! All tests passed!
```

### GPU Support (Optional but Recommended)

**For NVIDIA GPU (CUDA):**
```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**For Apple Silicon (M1/M2/M3):**
```bash
# MPS (Metal Performance Shaders) is automatically supported
# Just install regular PyTorch, it will detect MPS
pip install torch torchvision
```

**For CPU Only:**
```bash
# Default installation uses CPU
pip install torch torchvision
```

## Components

### 1. Image Preprocessing
- Image resizing and normalization
- Background removal (optional)
- Quality enhancement
- Augmentation for training

### 2. Feature Extraction
- ResNet50/ResNet101 pretrained models
- EfficientNet pretrained models
- Custom fine-tuned models
- Output: 2048-dimensional embeddings

### 3. Similarity Search
- FAISS index creation
- Efficient nearest neighbor search
- Batch query processing
- Filtering by metadata

### 4. Model Training
- Fine-tuning on fashion dataset
- Triplet loss training
- Metric learning
- Model evaluation

## Usage

### Generate Embeddings for Product Catalog

```python
from embeddings.generator import EmbeddingGenerator

generator = EmbeddingGenerator(model_name='resnet50')
embedding = generator.generate(image_path)
```

### Build FAISS Index

```python
from similarity.indexer import FAISSIndexer

indexer = FAISSIndexer(dimension=2048)
indexer.add_embeddings(embeddings, product_ids)
indexer.save('product_index.faiss')
```

### Search Similar Products

```python
from similarity.search import SimilaritySearch

searcher = SimilaritySearch(index_path='product_index.faiss')
results = searcher.search(query_embedding, k=10)
```

## Configuration

Edit `config.yaml` to customize:
- Model architecture
- Image preprocessing parameters
- FAISS index settings
- Batch processing options

## Performance

- Single image embedding: ~50ms (GPU) / ~200ms (CPU)
- FAISS search (1M products): ~10ms
- Batch processing: ~1000 images/minute (GPU)

## Model Accuracy

Target: 80%+ accuracy in top-3 matches

Evaluation metrics:
- Precision@K
- Recall@K
- Mean Average Precision (MAP)

## Testing

```bash
pytest tests/
```

## Future Enhancements

- Multi-modal search (image + text)
- Style transfer for virtual try-on
- Trend prediction
- Personalized recommendations

## License

[To be determined]

