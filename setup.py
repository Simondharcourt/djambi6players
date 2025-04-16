from setuptools import setup, find_packages

setup(
    name="djambi6players",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "gymnasium",
        "torch>=2.0.0",
        "matplotlib>=3.7.0",
        "tqdm>=4.65.0",
    ],
    extras_require={
        "tensorboard": ["tensorboard>=2.13.0"],
    },
    python_requires=">=3.8",
) 