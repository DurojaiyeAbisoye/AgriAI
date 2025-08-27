from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from PIL import Image
import numpy as np
from src.vision.inference import  DEVICE, load_model, preprocess_image, run_inference

def reshape_transform(tensor, height=7, width=7):
    result = tensor.reshape(tensor.size(0),
                            height, width, tensor.size(2))

    result = result.transpose(2, 3).transpose(1, 2)
    return result

def generate_gradcam(image, input_tensor, model, target_layer = None, reshape_transform= None):
    image_array = np.array(image.resize((224, 224))) / 255.0
    predicted_class = run_inference(model, input_tensor, device=DEVICE)[0]
    if target_layer is None:
        target_layer = [model.model.layers[-1].blocks[-1].norm2]
    targets = [ClassifierOutputTarget(predicted_class)]
    with GradCAM(model=model, target_layers=target_layer, reshape_transform=reshape_transform) as cam:
        grayscale_cam = cam(input_tensor=input_tensor, targets=targets) # type: ignore
        grayscale_cam = grayscale_cam[0, :]
        visualization = show_cam_on_image(image_array, grayscale_cam, use_rgb=True)
    return visualization
