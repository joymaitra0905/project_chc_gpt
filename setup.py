import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="edl",
    # version_format is only used when the repo has moved on from tag.
    version_format="{tag}.dev{commitcount}.{gitsha}",
    setup_requires=["setuptools-git-version"],
    install_requires=["boto3", "pyyaml", "requests"],
    description="Tools for interacting with the sanofi datalake",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SanofiDSE/data-lake-config",
    packages=setuptools.find_packages(include=["edl*"]),
    package_data={
        "edl.cloudformation": ["templates/*.yaml"],
        "edl": ["pipeline_wrapper/*", "core_resources/*", "core_resources/*/*",
                "core_resources/*/*/*"],
        'edl_api': ['api_details.yaml']
    },
    entry_points={
        'console_scripts': [
            'edl=edl.installed_scripts.dl:main',
            'edl-api=edl_api.edl_api:main'
        ],
    },
    classifiers=["Programming Language :: Python :: 2"],
)
