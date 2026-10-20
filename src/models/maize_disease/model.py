"""
src/models/maize_disease/model.py
─────────────────────────────────
MobileNetV2 transfer learning architecture and fine-tuning configurations
for Maize Leaf Disease classification.
"""

from __future__ import annotations

import tensorflow as tf
from tensorflow.keras import layers, Model


def build_mobilenetv2_classifier(
    num_classes: int = 4,
    input_shape: tuple[int, int, int] = (224, 224, 3),
    dropout_rate: float = 0.3,
) -> tuple[Model, Model]:
    """
    Constructs a transfer-learning classifier using MobileNetV2 pretrained on ImageNet
    with custom classification head: GlobalAveragePooling2D -> Dropout -> Dense(num_classes, softmax).

    Returns:
        (model, base_model): Full end-to-end model and the underlying MobileNetV2 backbone.
    """
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )
    # Freeze the backbone initially for stage 1 training
    base_model.trainable = False

    inputs = tf.keras.Input(shape=input_shape, name="leaf_image_input")
    # Base model called with training=False to keep BatchNormalization in inference mode
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = layers.Dropout(dropout_rate, name="head_dropout")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="disease_probabilities")(x)

    model = Model(inputs=inputs, outputs=outputs, name="MaizeLeafDiseaseClassifier")
    return model, base_model


def compile_for_initial_training(model: Model, learning_rate: float = 1e-3) -> None:
    """Compiles the model with frozen backbone for training the classification head."""
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=optimizer,
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )


def unfreeze_for_fine_tuning(
    model: Model,
    base_model: Model,
    unfreeze_from_layer: int = 100,
    learning_rate: float = 1e-4,
) -> None:
    """
    Unfreezes top layers of the backbone for fine-tuning with a low learning rate.
    Maintains earlier generic feature extractor layers frozen.
    """
    base_model.trainable = True
    # Freeze all layers before unfreeze_from_layer
    for layer in base_model.layers[:unfreeze_from_layer]:
        layer.trainable = False

    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=optimizer,
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
