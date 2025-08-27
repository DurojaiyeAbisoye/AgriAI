import torch
import albumentations as A
import numpy as np
from albumentations.pytorch import ToTensorV2
from PIL import Image

from src.vision.lit_model import CropDiseaseModel, LABEL2ID, ID2LABEL

MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

VAL_TRANSFORMS = A.Compose([
    A.Resize(224, 224),
    A.Normalize(mean=MEAN, std=STD), # type: ignore
    ToTensorV2()
])


def load_model(checkpoint_path, device =DEVICE):
    model = CropDiseaseModel.load_from_checkpoint(checkpoint_path)
    model = model.to(device)
    model.eval()
    return model


def preprocess_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = np.array(image)
    image = VAL_TRANSFORMS(image=image)["image"]
    image = image.unsqueeze(0)  # Add batch dimension
    return image


def run_inference(model, image_tensor, device=DEVICE):
    image_tensor = image_tensor.to(device)
    with torch.inference_mode():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted_class = torch.max(probabilities, dim=1)
        label = ID2LABEL[int(predicted_class.item())]
    return predicted_class.item(), confidence.item(), label