import lightning.pytorch as pl
import timm
from torchmetrics.classification import Accuracy, Precision, Recall
from torchmetrics import MetricCollection
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR


LABEL2ID = {
  'Apple__black_rot': 0, 'Apple__healthy': 1, 'Apple__rust': 2, 'Apple__scab': 3, 'Cassava__bacterial_blight': 4,
  'Cassava__brown_streak_disease': 5, 'Cassava__green_mottle': 6, 'Cassava__healthy': 7, 'Cassava__mosaic_disease': 8, 'Cherry__healthy': 9,
  'Cherry__powdery_mildew': 10, 'Chili__healthy': 11, 'Chili__leaf curl': 12, 'Chili__leaf spot': 13, 'Chili__whitefly': 14,
  'Chili__yellowish': 15, 'Coffee__cercospora_leaf_spot': 16, 'Coffee__healthy': 17, 'Coffee__red_spider_mite': 18, 'Coffee__rust': 19,
  'Corn__common_rust': 20, 'Corn__gray_leaf_spot': 21, 'Corn__healthy': 22, 'Corn__northern_leaf_blight': 23, 'Cucumber__diseased': 24,
  'Cucumber__healthy': 25, 'Gauva__diseased': 26, 'Gauva__healthy': 27, 'Grape__black_measles': 28, 'Grape__black_rot': 29,
  'Grape__healthy': 30, 'Grape__leaf_blight_(isariopsis_leaf_spot)': 31, 'Jamun__diseased': 32, 'Jamun__healthy': 33, 'Lemon__diseased': 34,
  'Lemon__healthy': 35, 'Mango__diseased': 36, 'Mango__healthy': 37, 'Peach__bacterial_spot': 38, 'Peach__healthy': 39,
  'Pepper_bell__bacterial_spot': 40, 'Pepper_bell__healthy': 41, 'Pomegranate__diseased': 42, 'Pomegranate__healthy': 43, 'Potato__early_blight': 44,
  'Potato__healthy': 45, 'Potato__late_blight': 46, 'Rice__brown_spot': 47, 'Rice__healthy': 48, 'Rice__hispa': 49,
  'Rice__leaf_blast': 50, 'Rice__neck_blast': 51, 'Soybean__bacterial_blight': 52, 'Soybean__caterpillar': 53, 'Soybean__diabrotica_speciosa': 54,
  'Soybean__downy_mildew': 55, 'Soybean__healthy': 56, 'Soybean__mosaic_virus': 57, 'Soybean__powdery_mildew': 58, 'Soybean__rust': 59,
  'Soybean__southern_blight': 60, 'Strawberry___leaf_scorch': 61, 'Strawberry__healthy': 62, 'Sugarcane__bacterial_blight': 63, 'Sugarcane__healthy': 64,
  'Sugarcane__red_rot': 65, 'Sugarcane__red_stripe': 66, 'Sugarcane__rust': 67, 'Tea__algal_leaf': 68, 'Tea__anthracnose': 69,
  'Tea__bird_eye_spot': 70, 'Tea__brown_blight': 71, 'Tea__healthy': 72, 'Tea__red_leaf_spot': 73, 'Tomato__bacterial_spot': 74,
  'Tomato__early_blight': 75, 'Tomato__healthy': 76, 'Tomato__late_blight': 77, 'Tomato__leaf_mold': 78, 'Tomato__mosaic_virus': 79,
  'Tomato__septoria_leaf_spot': 80, 'Tomato__spider_mites_(two_spotted_spider_mite)': 81, 'Tomato__target_spot': 82, 'Tomato__yellow_leaf_curl_virus': 83, 'Wheat__brown_rust': 84,
  'Wheat__healthy': 85, 'Wheat__septoria': 86, 'Wheat__yellow_rust': 87
}

ID2LABEL = {v: k for k, v in LABEL2ID.items()}

class CropDiseaseModel(pl.LightningModule):
    def __init__(self, model_name, lr):
        super().__init__()
        self.model_name = model_name
        self.lr = lr


        self.model = timm.create_model(
            model_name=model_name,
            pretrained=True,
            exportable=True,
            num_classes=len(LABEL2ID)
        )

        self.loss_fn = nn.CrossEntropyLoss()

        metrics = MetricCollection({
            "acccuracy": Accuracy(task="multiclass", num_classes=len(LABEL2ID), average="weighted"),
            "precision": Precision(task="multiclass", num_classes=len(LABEL2ID), average="weighted"),
            "recall": Recall(task="multiclass", num_classes=len(LABEL2ID), average="weighted"),
        })

        self.train_metrics = metrics.clone(prefix="train_")
        self.val_metrics = metrics.clone(prefix="val_")
        self.test_metrics = metrics.clone(prefix="test_")

        self.save_hyperparameters()

    def forward(self, x):
        return self.model(x)

    def _shared_step(self, batch, stage):
        x, y = batch["image"], batch["label"]
        logits = self(x)
        loss = self.loss_fn(logits, y)

        if stage == "train":
            metrics = self.train_metrics
        elif stage == "val":
            metrics = self.val_metrics
        else:
            metrics = self.test_metrics

        self.log(f"{stage}_loss", loss, prog_bar=True, on_step = False, on_epoch = True)
        self.log_dict(metrics(logits.softmax(dim=-1), y), prog_bar=True, on_step = False, on_epoch = True)
        return loss

    def training_step(self, batch, batch_idx):
        return self._shared_step(batch, "train")

    def validation_step(self, batch, batch_idx):
        return self._shared_step(batch, "val")

    def test_step(self, batch, batch_idx):
        return self._shared_step(batch, "test")

    def predict_step(self, batch, batch_idx):
        return self(batch['image']).argmax(dim = -1)

    def configure_optimizers(self):
        optimizer = AdamW(self.parameters(), lr=self.lr)

        steps_per_epoch = self.trainer.estimated_stepping_batches
        scheduler = OneCycleLR(
            optimizer,
            max_lr=self.lr,
            total_steps=int(steps_per_epoch),
            pct_start=0.3,
            anneal_strategy='cos',
        )

        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "interval": "step",
                "frequency": 1
            }
        }
