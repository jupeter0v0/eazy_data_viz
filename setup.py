"""eazy_data_viz 打包配置（pip install . / pip install -e .）。"""
import io
import os

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with io.open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


setup(
    name="eazy_data_viz",
    version="1.0.0",
    description="给 pandas 用的经营驾驶舱图表库（HTML / Streamlit）：45 种图表、Material Design 3、客户端下钻/联动",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(include=["eazy_data_viz", "eazy_data_viz.*"]),
    package_data={
        "eazy_data_viz": ["assets/*.js", "assets/*.json", "gallery/*.html", "gallery/*.py", "fonts/*"],
    },
    include_package_data=True,
    install_requires=["pandas>=1.3"],
    extras_require={
        "streamlit": ["streamlit>=1.10"],
        "notebook": ["ipython>=7"],
    },
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    keywords=["pandas", "chart", "visualization", "echarts", "streamlit", "html"],
)
