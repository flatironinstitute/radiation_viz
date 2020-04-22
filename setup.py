from setuptools import setup

url = "https://github.com/flatironinstitute/radiation_viz"
version = "0.1.0"
readme = open('README.md').read()

# Note:  psutil is needed for demo purposes only.

setup(
    name="radiation_viz",
    packages=["radiation_viz"],
    version=version,
    description="Visualizations for astrophysical radiation simulation data",
    long_description=readme,
    include_package_data=True,
    author="Aaron Watters",
    author_email="awatters@flatironinstitute.org",
    url=url,
    install_requires=[
        "numpy", 
        "pillow", 
        "h5py",
        ],
    #package_data={'jp_gene_viz': ['*.js']},
    license="MIT",
    zip_safe = False,
)
