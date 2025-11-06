# DupeFinder ML Engine

Machine Learning engine for image similarity and product matching.

## Features

- Image preprocessing and augmentation
- Deep learning-based feature extraction (ResNet, EfficientNet)
- Vector embedding generation
- FAISS-based similarity search
- Model training and fine-tuning capabilities
- Batch processing for catalog indexing

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

### Prerequisites
- Python 3.10+
- CUDA-capable GPU (optional, for faster processing)

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt

# For GPU support (optional)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install faiss-gpu
```

3. Download pretrained models:
```bash
# Scripts will be provided for model download
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

