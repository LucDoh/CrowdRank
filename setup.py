import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="crowdrank1-LucDoh", # Replace with your own username
    version="1.0.0",
    author="Luc d'Hauthuille",
    author_email="ex@ample.com",
    description="Ranking using crowd wisdom",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LucDoh/CrowdRank",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
